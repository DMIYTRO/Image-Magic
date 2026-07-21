from collections import defaultdict
from pathlib import Path
import shutil
import subprocess
import tempfile

from core.inspector import count_frames, inspect_file
from core.pdf_exporter import convert_image_to_pdf, merge_pdfs_with_ghostscript

from .filename_parser import parse_filename
from .models import FileCheck, OrderCheck


SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tif", ".tiff"}
REJECTED_EXTENSIONS = {".psd", ".bmp", ".heic", ".heif"}
ALLOWED_COLOR_MODES = {(4, 4), (4, 0), (1, 0), (1, 1), (5, 5), (6, 0), (6, 6), (5, 0)}


class BatchProcessor:
    def __init__(
        self,
        input_dir: Path,
        output_dir: Path,
        size_extra_mm: float = 4.0,
        tolerance_mm: float = 0.5,
        min_dpi: float = 300.0,
    ):
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.size_extra_mm = size_extra_mm
        self.tolerance_mm = tolerance_mm
        self.min_dpi = min_dpi
        self.unparsed: list[FileCheck] = []
        self.unsupported: list[FileCheck] = []

    def scan(self) -> list[Path]:
        if not self.input_dir.is_dir():
            raise FileNotFoundError(f"Входная папка не найдена: {self.input_dir}")
        return sorted(
            path for path in self.input_dir.iterdir()
            if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS | REJECTED_EXTENSIONS
        )

    def inspect_orders(self) -> list[OrderCheck]:
        grouped: dict[str, list[FileCheck]] = defaultdict(list)
        self.unparsed = []
        self.unsupported = []

        for path in self.scan():
            check = FileCheck(path=path)
            if path.suffix.lower() in REJECTED_EXTENSIONS:
                check.errors.append(
                    f"формат {path.suffix.lower().lstrip('.').upper()} исключён из обработки"
                )
                self.unsupported.append(check)
                continue
            try:
                check.parsed = parse_filename(path)
            except ValueError as exc:
                check.errors.append(str(exc))
                self.unparsed.append(check)
                continue

            try:
                frame_count = count_frames(str(path))
                if frame_count != 1:
                    check.errors.append(
                        f"файл содержит {frame_count} страниц/изображений; разрешён только одностраничный файл"
                    )
                    grouped[check.parsed.order_id].append(check)
                    continue
                meta = inspect_file(str(path))
                check.actual_width_mm = meta.width_mm
                check.actual_height_mm = meta.height_mm
                check.dpi = meta.dpi
                check.dpi_x = meta.dpi_x
                check.dpi_y = meta.dpi_y
                check.actual_format = meta.format.upper()
                check.colorspace = meta.colorspace
                self._validate_file(check)
            except Exception as exc:
                check.errors.append(f"не удалось прочитать файл: {exc}")

            grouped[check.parsed.order_id].append(check)

        orders = []
        for order_id, files in sorted(grouped.items()):
            order = OrderCheck(
                order_id=order_id,
                customer_id=files[0].parsed.customer_id,
                files=files,
            )
            self._validate_order(order)
            orders.append(order)
        return orders

    def _validate_file(self, check: FileCheck) -> None:
        parsed = check.parsed
        expected = (parsed.width_mm + self.size_extra_mm, parsed.height_mm + self.size_extra_mm)
        actual = (check.actual_width_mm, check.actual_height_mm)
        direct = self._dimensions_match(actual, expected)
        rotated = self._dimensions_match(actual, (expected[1], expected[0]))
        if not direct and not rotated:
            check.errors.append(
                f"размер {actual[0]:.1f}x{actual[1]:.1f} мм; "
                f"ожидается {expected[0]:.1f}x{expected[1]:.1f} мм "
                f"(или с поворотом), допуск ±{self.tolerance_mm:.1f} мм"
            )

        if (check.colorspace or "").upper() not in {"CMYK", "COLORSEPARATION"}:
            check.errors.append(f"цветовая модель {check.colorspace or 'не определена'}; требуется CMYK")

        if check.dpi is None or check.dpi < self.min_dpi:
            actual_dpi = (
                f"{check.dpi_x:.1f}x{check.dpi_y:.1f}"
                if check.dpi_x is not None and check.dpi_y is not None
                else "не определено"
            )
            check.errors.append(f"разрешение {actual_dpi} DPI; по обеим осям требуется не меньше {self.min_dpi:.0f} DPI")

        color_mode = (parsed.front_colors, parsed.back_colors)
        if color_mode not in ALLOWED_COLOR_MODES:
            allowed = ", ".join(f"{front}-{back}" for front, back in sorted(ALLOWED_COLOR_MODES))
            check.errors.append(
                f"цветность {color_mode[0]}-{color_mode[1]} не поддерживается; разрешены: {allowed}"
            )

    def _dimensions_match(self, actual: tuple[float, float], expected: tuple[float, float]) -> bool:
        return all(abs(a - e) <= self.tolerance_mm for a, e in zip(actual, expected))

    @staticmethod
    def _validate_order(order: OrderCheck) -> None:
        sides: dict[str, list[FileCheck]] = defaultdict(list)
        for item in order.files:
            sides[item.parsed.side].append(item)

        if not sides["face"]:
            order.errors.append("не найден обязательный файл face")
        if len(sides["face"]) > 1:
            order.errors.append("найдено несколько файлов face")
        if len(sides["back"]) > 1:
            order.errors.append("найдено несколько файлов back")

        readable_files = [
            item for item in order.files
            if item.actual_width_mm is not None and item.actual_height_mm is not None
        ]
        orientations = {
            BatchProcessor._orientation(item.actual_width_mm, item.actual_height_mm)
            for item in readable_files
        }
        if len(orientations) > 1:
            details = ", ".join(
                f"{item.parsed.side}={BatchProcessor._orientation(item.actual_width_mm, item.actual_height_mm)}"
                for item in readable_files
            )
            order.errors.append(f"ориентация сторон не совпадает: {details}")

        color_modes = {(item.parsed.front_colors, item.parsed.back_colors) for item in order.files}
        if len(color_modes) != 1:
            order.errors.append("у файлов заказа не совпадает цветность в имени")
            return

        declared_sizes = {(item.parsed.width_mm, item.parsed.height_mm) for item in order.files}
        if len(declared_sizes) != 1:
            order.errors.append("у файлов заказа не совпадает размер в имени")

        customer_ids = {item.parsed.customer_id for item in order.files}
        if len(customer_ids) != 1:
            order.errors.append("у файлов заказа не совпадает номер клиента")

        actual_formats = {item.actual_format for item in order.files if item.actual_format}
        if len(actual_formats) > 1:
            order.warnings.append(
                "стороны заказа имеют разные форматы: " + ", ".join(sorted(actual_formats))
            )

        _, back_colors = next(iter(color_modes))
        if back_colors > 0 and not sides["back"]:
            order.errors.append("для двусторонней печати не найден файл back")
        if back_colors == 0 and sides["back"]:
            order.errors.append("для односторонней печати найден лишний файл back")

    @staticmethod
    def _orientation(width_mm: float, height_mm: float) -> str:
        if abs(width_mm - height_mm) <= 0.5:
            return "квадратная"
        return "горизонтальная" if width_mm > height_mm else "вертикальная"

    def create_pdfs(self, orders: list[OrderCheck]) -> list[tuple[OrderCheck, Path, str | None]]:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        results = []
        for order in orders:
            if not order.passed:
                continue
            ordered_files = sorted(order.files, key=lambda item: 0 if item.parsed.side == "face" else 1)
            face_file = next(item for item in ordered_files if item.parsed.side == "face")
            output_path = self.output_dir / f"{face_file.path.stem}.pdf"
            try:
                with tempfile.TemporaryDirectory(
                    prefix=f".{order.order_id}_",
                    dir=self.output_dir,
                ) as temporary_dir:
                    page_pdfs = []
                    for page_number, item in enumerate(ordered_files, start=1):
                        page_path = Path(temporary_dir) / f"{page_number}_{item.parsed.side}.pdf"
                        convert_image_to_pdf(
                            str(item.path),
                            str(page_path),
                            dpi=f"{item.dpi_x}x{item.dpi_y}",
                            compression="none",
                        )
                        page_pdfs.append(str(page_path))

                    temporary_output = Path(temporary_dir) / "combined.pdf"
                    merge_pdfs_with_ghostscript(page_pdfs, str(temporary_output))
                    self._validate_created_pdf(
                        temporary_output,
                        ordered_files,
                        Path(temporary_dir) / "validation",
                    )
                    temporary_output.replace(output_path)
                results.append((order, output_path, None))
            except Exception as exc:
                results.append((order, output_path, str(exc)))
        return results

    def _validate_created_pdf(
        self,
        pdf_path: Path,
        ordered_files: list[FileCheck],
        validation_dir: Path,
    ) -> None:
        """Render the final PDF and verify readability, page count, order and page sizes."""
        gs_cmd = shutil.which("gs")
        if not gs_cmd:
            raise FileNotFoundError("Ghostscript (`gs`) не найден для проверки PDF.")
        if not pdf_path.is_file() or pdf_path.stat().st_size == 0:
            raise ValueError("Ghostscript не создал итоговый PDF или файл пуст.")

        validation_dir.mkdir(parents=True, exist_ok=True)
        page_pattern = validation_dir / "page-%03d.png"
        command = [
            gs_cmd,
            "-dSAFER",
            "-dBATCH",
            "-dNOPAUSE",
            "-sDEVICE=png16m",
            "-r72",
            f"-sOutputFile={page_pattern}",
            str(pdf_path),
        ]
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode != 0:
            details = (result.stderr or result.stdout).strip()
            raise ValueError(f"итоговый PDF повреждён или не открывается: {details}")

        rendered_pages = sorted(validation_dir.glob("page-*.png"))
        if len(rendered_pages) != len(ordered_files):
            raise ValueError(
                f"в итоговом PDF {len(rendered_pages)} страниц; ожидалось {len(ordered_files)}"
            )

        for page_number, (rendered_page, source) in enumerate(zip(rendered_pages, ordered_files), start=1):
            page_meta = inspect_file(str(rendered_page))
            expected = (source.actual_width_mm, source.actual_height_mm)
            actual = (page_meta.width_mm, page_meta.height_mm)
            # A 72-DPI control render has a rounding step of about 0.35 mm.
            validation_tolerance = max(self.tolerance_mm, 0.6)
            if any(abs(a - e) > validation_tolerance for a, e in zip(actual, expected)):
                raise ValueError(
                    f"страница {page_number} ({source.parsed.side}) имеет размер "
                    f"{actual[0]:.1f}x{actual[1]:.1f} мм; ожидалось "
                    f"{expected[0]:.1f}x{expected[1]:.1f} мм"
                )

            expected_side = "face" if page_number == 1 else "back"
            if source.parsed.side != expected_side:
                raise ValueError(
                    f"нарушен порядок страниц: страница {page_number} должна быть {expected_side}"
                )

    def copy_failed_to_troubles(
        self,
        orders: list[OrderCheck],
        troubles_dir: Path,
    ) -> list[tuple[Path, Path, str | None]]:
        """Copy rejected inputs and a readable reason file without changing originals."""
        rejected: list[tuple[FileCheck, list[str], str]] = []
        for order in orders:
            if order.passed:
                continue
            order_reasons = [f"Ошибка заказа: {message}" for message in order.errors]
            for item in order.files:
                rejected.append((item, item.errors + order_reasons, order.order_id))

        for item in self.unparsed:
            rejected.append((item, item.errors, "UNPARSED"))

        for item in self.unsupported:
            rejected.append((item, item.errors, "UNSUPPORTED"))

        results = []
        for item, reasons, group_name in rejected:
            target_dir = troubles_dir / group_name
            target_path = target_dir / item.path.name
            try:
                target_dir.mkdir(parents=True, exist_ok=True)
                shutil.copy2(item.path, target_path)
                reason_path = target_dir / f"{item.path.name}.error.txt"
                reason_text = "\n".join(f"- {reason}" for reason in reasons)
                reason_path.write_text(
                    f"Файл: {item.path.name}\nСтатус: НЕ ОБРАБОТАН\nПричины:\n{reason_text}\n",
                    encoding="utf-8",
                )
                results.append((item.path, target_path, None))
            except Exception as exc:
                results.append((item.path, target_path, str(exc)))
        return results

    def copy_pdf_failure_to_troubles(
        self,
        order: OrderCheck,
        troubles_dir: Path,
        reason: str,
    ) -> list[tuple[Path, Path, str | None]]:
        """Route an order that passed input checks but failed PDF creation."""
        results = []
        target_dir = troubles_dir / order.order_id
        for item in order.files:
            target_path = target_dir / item.path.name
            try:
                target_dir.mkdir(parents=True, exist_ok=True)
                shutil.copy2(item.path, target_path)
                reason_path = target_dir / f"{item.path.name}.error.txt"
                reason_path.write_text(
                    f"Файл: {item.path.name}\nСтатус: PDF НЕ СОЗДАН\nПричина:\n- {reason}\n",
                    encoding="utf-8",
                )
                results.append((item.path, target_path, None))
            except Exception as exc:
                results.append((item.path, target_path, str(exc)))
        return results

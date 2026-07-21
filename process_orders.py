#!/usr/bin/env python3
import argparse
from pathlib import Path

from processing import BatchProcessor


# Быстро изменяемые пути для тестового запуска.
INPUT_DIR = Path("/Users/admin/Desktop/sempels")
PDF_DIR_NAME = "PDF"
TROUBLES_DIR_NAME = "Troubles"


def print_report(processor: BatchProcessor, orders) -> None:
    print("\n" + "=" * 78)
    print("ПРОВЕРКА ЗАКАЗОВ")
    print("=" * 78)

    for order in orders:
        first = order.files[0].parsed
        expected_w = first.width_mm + processor.size_extra_mm
        expected_h = first.height_mm + processor.size_extra_mm
        mode = f"{first.front_colors}-{first.back_colors}"
        print(f"\nЗаказ {order.order_id} | клиент {order.customer_id} | цветность {mode}")
        print(f"  Ожидаемый размер: {expected_w:.1f}x{expected_h:.1f} мм, допуск ±{processor.tolerance_mm:.1f} мм")

        for item in sorted(order.files, key=lambda value: 0 if value.parsed.side == "face" else 1):
            size = (
                f"{item.actual_width_mm:.1f}x{item.actual_height_mm:.1f} мм"
                if item.actual_width_mm is not None else "не определён"
            )
            status = "PASS" if item.passed else "FAIL"
            orientation = (
                processor._orientation(item.actual_width_mm, item.actual_height_mm)
                if item.actual_width_mm is not None and item.actual_height_mm is not None
                else "не определена"
            )
            print(
                f"  [{status}] {item.parsed.side.upper():4} | размер {size} | "
                f"ориентация {orientation} | "
                f"DPI {item.dpi_x if item.dpi_x is not None else '?'}x{item.dpi_y if item.dpi_y is not None else '?'} | "
                f"цвет {item.colorspace or 'не определён'}"
            )
            print(f"         {item.path.name}")
            for error in item.errors:
                print(f"         Причина: {error}")

        for error in order.errors:
            print(f"  Причина заказа: {error}")
        for warning in order.warnings:
            print(f"  Предупреждение: {warning}")
        found_sides = {item.parsed.side for item in order.files}
        required_sides = {"face", "back"} if first.back_colors > 0 else {"face"}
        print(f"  Группа: {'НАЙДЕНА' if required_sides.issubset(found_sides) else 'НЕПОЛНАЯ'}")
        print(f"  ИТОГ: {'ПОДХОДИТ ДЛЯ PDF' if order.passed else 'НЕ ПОДХОДИТ'}")

    if processor.unparsed:
        print("\nФАЙЛЫ С НЕРАСПОЗНАННЫМИ ИМЕНАМИ")
        for item in processor.unparsed:
            print(f"  [FAIL] {item.path.name}")
            for error in item.errors:
                print(f"         Причина: {error}")

    if processor.unsupported:
        print("\nФАЙЛЫ ИСКЛЮЧЁННЫХ ФОРМАТОВ")
        for item in processor.unsupported:
            print(f"  [SKIP] {item.path.name}")
            for error in item.errors:
                print(f"         Причина: {error}")

    passed = sum(order.passed for order in orders)
    failed = len(orders) - passed
    print("\n" + "-" * 78)
    print(
        f"Заказов: {len(orders)} | подходят: {passed} | не подходят: {failed} | "
        f"не распознано файлов: {len(processor.unparsed)} | исключено форматов: {len(processor.unsupported)}"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Проверка заказов и создание PDF после подтверждения")
    parser.add_argument("--input", type=Path, default=INPUT_DIR, help="Папка с исходными файлами")
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Папка для готовых PDF (по умолчанию: подпапка PDF во входной папке)",
    )
    args = parser.parse_args()

    output_dir = args.output if args.output is not None else args.input / PDF_DIR_NAME
    processor = BatchProcessor(args.input, output_dir)
    try:
        orders = processor.inspect_orders()
    except Exception as exc:
        raise SystemExit(f"Ошибка: {exc}") from exc

    print_report(processor, orders)
    troubles_dir = args.input / TROUBLES_DIR_NAME
    trouble_results = processor.copy_failed_to_troubles(orders, troubles_dir)
    if trouble_results:
        print("\nФАЙЛЫ, НЕ ПОПАВШИЕ В ОБРАБОТКУ")
        for source, target, error in trouble_results:
            if error:
                print(f"  [FAIL] {source.name}: не удалось скопировать — {error}")
            else:
                print(f"  [COPIED] {source.name} → {target}")
        print(f"  Папка: {troubles_dir}")

    suitable = [order for order in orders if order.passed]
    if not suitable:
        print("\nНет заказов, подходящих для создания PDF.")
        return

    answer = input(f"\nСоздать PDF для подходящих заказов ({len(suitable)})? [y/N]: ").strip().lower()
    if answer not in {"y", "yes", "д", "да"}:
        print("Создание PDF отменено. Исходные файлы не изменены.")
        return

    results = processor.create_pdfs(suitable)
    print("\nРЕЗУЛЬТАТ СОЗДАНИЯ PDF")
    for order, path, error in results:
        if error:
            print(f"  [FAIL] Заказ {order.order_id}: {error}")
            routed = processor.copy_pdf_failure_to_troubles(order, troubles_dir, error)
            copied = sum(copy_error is None for _, _, copy_error in routed)
            print(f"         Скопировано в Troubles: {copied}/{len(routed)} файлов")
            for source, _, copy_error in routed:
                if copy_error:
                    print(f"         Не удалось скопировать {source.name}: {copy_error}")
        else:
            print(f"  [PASS] Заказ {order.order_id}: {path}")


if __name__ == "__main__":
    main()

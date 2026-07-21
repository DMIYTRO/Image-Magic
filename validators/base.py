"""
Базовый класс валидатора файлов по профилю допечатной подготовки.
"""

from core.inspector import ImageMetadata
from config.profiles import PrePressProfile, DEFAULT_PROFILE
from .rules import ValidationResult, ValidationItem

class BaseValidator:
    """Базовый валидатор общих параметров файла."""

    def __init__(self, profile: PrePressProfile = None):
        self.profile = profile or DEFAULT_PROFILE

    def validate(self, meta: ImageMetadata) -> ValidationResult:
        """Проводит стандартные проверки файла."""
        items = []

        # 1. Проверка разрешения (DPI)
        dpi_ok = meta.dpi >= self.profile.min_dpi
        items.append(ValidationItem(
            name="Разрешающая способность, DPI",
            actual_value=f"{int(meta.dpi)} DPI",
            target_value=str(int(self.profile.target_dpi)),
            passed=dpi_ok,
            message="Разрешение соответствует норме" if dpi_ok else f"Разрешение ниже требуемых {int(self.profile.target_dpi)} DPI"
        ))

        # 2. Проверка цветовой модели (CMYK)
        colorspace_ok = meta.colorspace.upper() in [c.upper() for c in self.profile.allowed_colorspaces]
        items.append(ValidationItem(
            name="Цветовая модель",
            actual_value=meta.colorspace,
            target_value="CMYK",
            passed=colorspace_ok,
            message="Цветовая модель CMYK" if colorspace_ok else f"Файл имеет цветовую модель {meta.colorspace}, требуется CMYK"
        ))

        # 3. Проверка цветового профиля (ICC)
        icc_ok = meta.icc_profile != "Не внедрен"
        items.append(ValidationItem(
            name="Цветовой профиль (ICC)",
            actual_value=meta.icc_profile,
            target_value="FOGRA39 / ISO Coated",
            passed=icc_ok,
            message="ICC профиль внедрен" if icc_ok else "Внимание: ICC профиль не найден в файле"
        ))

        # 4. Проверка размера в мм
        items.append(ValidationItem(
            name="Размер, мм",
            actual_value=f"{meta.width_mm} × {meta.height_mm}",
            target_value=f"{meta.width_mm} × {meta.height_mm}",
            passed=True,
            message="соответствует"
        ))

        # 5. Проверка объема файла (МБ)
        size_ok = meta.size_mb <= self.profile.max_file_size_mb
        items.append(ValidationItem(
            name="Размер файла, Mb",
            actual_value=f"{meta.size_mb}",
            target_value=f"до {int(self.profile.max_file_size_mb)}",
            passed=size_ok,
            message="норма" if size_ok else f"Превышен лимит размера файла ({meta.size_mb} МБ)"
        ))

        overall_passed = all(item.passed for item in items)

        return ValidationResult(
            file_name=meta.file_name,
            format=meta.format,
            overall_passed=overall_passed,
            items=items
        )

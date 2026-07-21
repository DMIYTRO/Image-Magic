"""
Специфичный валидатор для формата TIFF.
"""

from .base import BaseValidator
from core.inspector import ImageMetadata
from .rules import ValidationResult, ValidationItem

class TIFFValidator(BaseValidator):
    """Валидатор файлов формата TIFF."""

    def validate(self, meta: ImageMetadata) -> ValidationResult:
        result = super().validate(meta)

        # Специфичная проверка глубин цветности TIFF
        depth_val = int(meta.depth_bits.split("-")[0].replace("8", "8").replace("16", "16") or 8)
        depth_ok = depth_val in (8, 16)
        
        result.items.append(ValidationItem(
            name="Глубина цвета TIFF",
            actual_value=f"{meta.depth_bits} бит",
            target_value="8 или 16 бит",
            passed=depth_ok,
            message="Глубина цвета в норме" if depth_ok else f"Нестандартная глубина цвета: {meta.depth_bits}"
        ))

        result.overall_passed = all(item.passed for item in result.items)
        return result

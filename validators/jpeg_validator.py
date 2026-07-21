"""
Специфичный валидатор для сжатых растровых форматов (JPEG / PNG).
"""

from .base import BaseValidator
from core.inspector import ImageMetadata
from .rules import ValidationResult, ValidationItem

class JPEGValidator(BaseValidator):
    """Валидатор файлов формата JPEG / PNG."""

    def validate(self, meta: ImageMetadata) -> ValidationResult:
        result = super().validate(meta)

        # Предупреждение о потере качества при растровом сжатии
        is_lossy = meta.format.upper() in ("JPEG", "JPG")
        result.items.append(ValidationItem(
            name="Сжатие макета",
            actual_value=meta.format,
            target_value="TIFF / PDF (Рекомендуется)",
            passed=True,  # Предупреждение, не блокирующее допуск
            message="Внимание: растровый JPEG формат может содержать артефакты сжатия" if is_lossy else "Без потерь сжатия"
        ))

        result.overall_passed = all(item.passed for item in result.items)
        return result

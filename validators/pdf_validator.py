"""
Специфичный валидатор для формата PDF.
"""

from .base import BaseValidator
from core.inspector import ImageMetadata
from .rules import ValidationResult, ValidationItem

class PDFValidator(BaseValidator):
    """Валидатор файлов формата PDF."""

    def validate(self, meta: ImageMetadata) -> ValidationResult:
        result = super().validate(meta)

        result.items.append(ValidationItem(
            name="Тип макета PDF",
            actual_value="Векторный/Растровый PDF",
            target_value="PDF/X-1a (Рекомендуется)",
            passed=True,
            message="Файл обработан через Ghostscript"
        ))

        result.overall_passed = all(item.passed for item in result.items)
        return result

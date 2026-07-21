"""
Фабрика валидаторов под каждый формат файла.
"""

from .base import BaseValidator
from .tiff_validator import TIFFValidator
from .jpeg_validator import JPEGValidator
from .pdf_validator import PDFValidator
from config.profiles import PrePressProfile

def get_validator(file_format: str, profile: PrePressProfile = None) -> BaseValidator:
    """Возвращает специализированный валидатор на основе формата файла."""
    fmt = file_format.upper()
    if fmt in ("TIFF", "TIF"):
        return TIFFValidator(profile)
    elif fmt in ("JPEG", "JPG", "PNG"):
        return JPEGValidator(profile)
    elif fmt in ("PDF"):
        return PDFValidator(profile)
    return BaseValidator(profile)

__all__ = ["get_validator", "BaseValidator", "TIFFValidator", "JPEGValidator", "PDFValidator"]

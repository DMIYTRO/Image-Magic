"""
Модели данных результатов валидации и тестов.
"""

from dataclasses import dataclass, field
from typing import List

@dataclass
class ValidationItem:
    name: str
    actual_value: str
    target_value: str
    passed: bool
    message: str = ""

@dataclass
class ValidationResult:
    file_name: str
    format: str
    overall_passed: bool
    items: List[ValidationItem] = field(default_factory=list)

"""
Конфигурация профилей допечатной подготовки (Pre-Press Profiles).
"""

from dataclasses import dataclass, field
from typing import List

@dataclass
class PrePressProfile:
    """Профиль требований допечатной подготовки."""
    name: str = "Standard Pre-Press"
    target_dpi: float = 300.0
    min_dpi: float = 280.0
    allowed_colorspaces: List[str] = field(default_factory=lambda: ["CMYK", "COLORSEPARATION"])
    max_file_size_mb: float = 2000.0
    safe_zone_mm: float = 4.0
    bleed_mm: float = 1.0

# Стандартный профиль по умолчанию
DEFAULT_PROFILE = PrePressProfile()

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass(frozen=True)
class ParsedFilename:
    customer_id: str
    order_id: str
    width_mm: float
    height_mm: float
    front_colors: int
    back_colors: int
    side: str


@dataclass
class FileCheck:
    path: Path
    parsed: Optional[ParsedFilename] = None
    actual_width_mm: Optional[float] = None
    actual_height_mm: Optional[float] = None
    dpi: Optional[float] = None
    dpi_x: Optional[float] = None
    dpi_y: Optional[float] = None
    width_px: Optional[int] = None
    height_px: Optional[int] = None
    actual_format: Optional[str] = None
    colorspace: Optional[str] = None
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    needs_resample: bool = False
    resample_target_mm: Optional[tuple[float, float]] = None

    @property
    def passed(self) -> bool:
        return not self.errors


@dataclass
class OrderCheck:
    order_id: str
    customer_id: str
    files: list[FileCheck] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return not self.errors and all(item.passed for item in self.files)

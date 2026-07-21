"""
Ядро извлечения метаданных графических файлов через ImageMagick.
"""

import os
import shutil
import subprocess
from dataclasses import dataclass

@dataclass
class ImageMetadata:
    file_path: str
    file_name: str
    format: str
    width_px: int
    height_px: int
    dpi: float
    width_mm: float
    height_mm: float
    colorspace: str
    icc_profile: str
    image_type: str
    depth_bits: str
    size_mb: float

def inspect_file(image_path: str) -> ImageMetadata:
    """Извлекает метаданные из графического файла, включая ICC-профиль."""
    magick_cmd = shutil.which("magick") or shutil.which("identify")
    if not magick_cmd:
        raise FileNotFoundError("ImageMagick CLI (magick / identify) не найден в системе.")

    cmd = [
        magick_cmd, "identify",
        "-format", "%f\n%m\n%w\n%h\n%x\n%y\n%[units]\n%[colorspace]\n%[type]\n%[depth]\n%[icc:description]\n%[profile:icc]",
        image_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    lines = [line.strip() for line in result.stdout.strip().split("\n")]

    file_name = lines[0] if len(lines) > 0 else os.path.basename(image_path)
    file_fmt = lines[1] if len(lines) > 1 else ""
    w_px = float(lines[2]) if len(lines) > 2 else 0.0
    h_px = float(lines[3]) if len(lines) > 3 else 0.0
    res_x = float(lines[4]) if len(lines) > 4 else 72.0
    units = lines[6] if len(lines) > 6 else "PixelsPerInch"
    colorspace = lines[7] if len(lines) > 7 else "sRGB"
    img_type = lines[8] if len(lines) > 8 else ""
    depth = lines[9] if len(lines) > 9 else "8"
    
    icc_desc = lines[10] if len(lines) > 10 and lines[10] else ""
    icc_prof = lines[11] if len(lines) > 11 and lines[11] else ""
    icc_profile = icc_desc or icc_prof or "Не внедрен"

    if "Centimeter" in units:
        dpi = res_x * 2.54
    else:
        dpi = res_x if res_x > 0 else 72.0

    width_mm = round((w_px / dpi) * 25.4, 1)
    height_mm = round((h_px / dpi) * 25.4, 1)

    size_bytes = os.path.getsize(image_path)
    size_mb = round(size_bytes / (1024 * 1024), 2)

    return ImageMetadata(
        file_path=image_path,
        file_name=file_name,
        format=file_fmt,
        width_px=int(w_px),
        height_px=int(h_px),
        dpi=round(dpi, 1),
        width_mm=width_mm,
        height_mm=height_mm,
        colorspace=colorspace,
        icc_profile=icc_profile,
        image_type=img_type,
        depth_bits=depth,
        size_mb=size_mb
    )

#!/usr/bin/env python3
"""
Скрипт генерации превью изображения с разметкой безопасных зон и рамок реза.

Разметка:
- Красная рамка (толщина 1 мм): внешний край изображения (дообрезной формат/край реза).
- Зеленая рамка (отступ 4 мм): внутренняя безопасная зона для текста и важных элементов.
"""

import sys
import os
import subprocess
import shutil

def get_image_dimensions_and_dpi(image_path: str):
    """Считывает ширину, высоту в пикселях и DPI изображения."""
    magick_cmd = shutil.which("magick") or shutil.which("identify")
    if not magick_cmd:
        raise FileNotFoundError("ImageMagick CLI (magick/identify) не найден.")
        
    cmd = [
        magick_cmd, "identify",
        "-format", "%w %h %x %[units]",
        image_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    parts = result.stdout.strip().split()
    
    w_px = float(parts[0])
    h_px = float(parts[1])
    res_x = float(parts[2]) if len(parts) > 2 else 72.0
    units = parts[3] if len(parts) > 3 else "PixelsPerInch"
    
    if "Centimeter" in units:
        dpi = res_x * 2.54
    else:
        dpi = res_x if res_x > 0 else 72.0
        
    return w_px, h_px, dpi

def create_preview_with_guidelines(
    input_path: str,
    output_path: str = None,
    safe_zone_mm: float = 4.0,
    border_mm: float = 1.0
):
    """Генерирует превью изображения с наложенными рамками."""
    
    magick_cmd = shutil.which("magick")
    if not magick_cmd:
        raise FileNotFoundError("Утилита `magick` не найдена в системе.")
        
    if not output_path:
        base, ext = os.path.splitext(input_path)
        output_path = f"{base}_preview.jpg"
        
    w_px, h_px, dpi = get_image_dimensions_and_dpi(input_path)
    
    # Расчет пиксельных отступов на основе DPI
    # px = mm * (DPI / 25.4)
    safe_offset_px = round(safe_zone_mm * (dpi / 25.4))
    border_stroke_px = max(1, round(border_mm * (dpi / 25.4)))
    
    # Зеленая рамка безопасной зоны (координаты внутреннего прямоугольника)
    gx1 = safe_offset_px
    gy1 = safe_offset_px
    gx2 = w_px - safe_offset_px
    gy2 = h_px - safe_offset_px
    
    # Красная рамка по краю изображения (толщина 1 мм)
    half_border = border_stroke_px / 2.0
    rx1 = half_border
    ry1 = half_border
    rx2 = w_px - half_border
    ry2 = h_px - half_border

    # Команда ImageMagick
    cmd = [
        magick_cmd, input_path,
        # Наложение красной рамки реза (1 мм по краю)
        "-stroke", "red",
        "-strokewidth", str(border_stroke_px),
        "-fill", "none",
        "-draw", f"rectangle {rx1},{ry1} {rx2},{ry2}",
        # Наложение зеленой рамки безопасной зоны (отступ 4 мм)
        "-stroke", "#00FF00",
        "-strokewidth", str(max(2, round(border_stroke_px * 0.4))),
        "-fill", "none",
        "-draw", f"rectangle {gx1},{gy1} {gx2},{gy2}",
        output_path
    ]
    
    subprocess.run(cmd, check=True)
    return output_path, w_px, h_px, dpi, safe_offset_px, border_stroke_px

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Использование: python3 generate_preview.py <путь_к_файлу> [вых_файл]")
        sys.exit(1)
        
    inp = sys.argv[1]
    outp = sys.argv[2] if len(sys.argv) > 2 else None
    
    out_file, w, h, dpi, safe_px, border_px = create_preview_with_guidelines(inp, outp)
    
    print("=" * 55)
    print("✅ Превью с разметкой успешно создано!")
    print("-" * 55)
    print(f"📁 Файл превью:       {out_file}")
    print(f"📐 Исходные пиксели:  {int(w)} x {int(h)} px")
    print(f"🎯 Разрешение (DPI):  {dpi} DPI")
    print(f"🔴 Красная рамка:     1 мм ({border_px} px)")
    print(f"🟢 Зеленая зона:      4 мм от каждого края ({safe_px} px)")
    print("=" * 55)

#!/usr/bin/env python3
"""
Скрипт для получения параметров графического файла с помощью ImageMagick CLI (или fallback через PIL).

Считываемые параметры:
1. Размер в пикселях (Ширина x Высота)
2. Разрешение (DPI / PPI) и единицы измерения
3. Физический размер изделия в мм и см
4. Цветовая модель / Color space (RGB, CMYK, Gray и т.д.)
5. Глубина цвета (Depth)
"""

import sys
import os
import subprocess
import shutil
import json

def get_image_info_imagemagick(image_path: str) -> dict:
    """Извлекает метаданные изображения через ImageMagick `magick identify`."""
    
    # Формат вывода с использованием спецификаторов ImageMagick percent escape
    # https://imagemagick.org/escape/
    format_str = (
        "FILENAME=%f\n"
        "FORMAT=%m\n"
        "WIDTH_PX=%w\n"
        "HEIGHT_PX=%h\n"
        "RES_X=%x\n"
        "RES_Y=%y\n"
        "UNITS=%[units]\n"
        "COLORSPACE=%[colorspace]\n"
        "TYPE=%[type]\n"
        "DEPTH=%[depth]\n"
        "ALPHA=%A\n"
        "PRINT_W=%[printsize:w]\n"
        "PRINT_H=%[printsize:h]\n"
        "PRINT_UNITS=%[printsize:units]\n"
    )
    
    magick_cmd = shutil.which("magick") or shutil.which("identify")
    if not magick_cmd:
        raise FileNotFoundError("ImageMagick CLI (magick или identify) не найден в системе.")
        
    cmd = [magick_cmd, "identify", "-format", format_str, image_path]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    
    raw_info = {}
    for line in result.stdout.strip().split("\n"):
        if "=" in line:
            k, v = line.split("=", 1)
            raw_info[k] = v.strip()
            
    # Расчет физического размера изделия (в миллиметрах)
    try:
        w_px = float(raw_info.get("WIDTH_PX", 0))
        h_px = float(raw_info.get("HEIGHT_PX", 0))
        
        # Разрешение по X (DPI)
        res_x_raw = raw_info.get("RES_X", "72").split()[0]
        dpi_x = float(res_x_raw) if float(res_x_raw) > 0 else 72.0
        
        units = raw_info.get("UNITS", "PixelsPerInch")
        
        if "Centimeter" in units:
            # Преобразуем из пикселей на см в DPI
            dpi_x = dpi_x * 2.54
            
        # 1 дюйм = 25.4 мм
        width_mm = round((w_px / dpi_x) * 25.4, 2)
        height_mm = round((h_px / dpi_x) * 25.4, 2)
        width_cm = round(width_mm / 10, 2)
        height_cm = round(height_mm / 10, 2)
    except Exception as e:
        width_mm = height_mm = width_cm = height_cm = None
        dpi_x = 72.0

    return {
        "file_name": raw_info.get("FILENAME"),
        "format": raw_info.get("FORMAT"),
        "dimensions_px": {
            "width": int(raw_info.get("WIDTH_PX", 0)),
            "height": int(raw_info.get("HEIGHT_PX", 0))
        },
        "resolution_dpi": dpi_x,
        "physical_size_mm": {
            "width_mm": width_mm,
            "height_mm": height_mm
        },
        "physical_size_cm": {
            "width_cm": width_cm,
            "height_cm": height_cm
        },
        "colorspace": raw_info.get("COLORSPACE"),
        "image_type": raw_info.get("TYPE"),
        "depth_bits": raw_info.get("DEPTH"),
        "has_alpha": raw_info.get("ALPHA") == "True"
    }

def print_summary(info: dict):
    print("=" * 50)
    print(f"📄 Файл: {info['file_name']} ({info['format']})")
    print("-" * 50)
    print(f"📐 Размер (в пикселях):  {info['dimensions_px']['width']} x {info['dimensions_px']['height']} px")
    print(f"🎯 Разрешение (DPI):      {info['resolution_dpi']} DPI")
    if info['physical_size_mm']['width_mm']:
        print(f"📏 Физический размер:     {info['physical_size_mm']['width_mm']} x {info['physical_size_mm']['height_mm']} мм ({info['physical_size_cm']['width_cm']} x {info['physical_size_cm']['height_cm']} см)")
    print(f"🎨 Цветовая модель:       {info['colorspace']} (Тип: {info['image_type']})")
    print(f"🔢 Глубина цвета:        {info['depth_bits']} бит")
    print(f"✨ Прозрачность (Alpha):  {'Да' if info['has_alpha'] else 'Нет'}")
    print("=" * 50)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Использование: python3 get_image_info.py <путь_к_файлу>")
        sys.exit(1)
        
    image_file = sys.argv[1]
    if not os.path.exists(image_file):
        print(f"Ошибка: файл '{image_file}' не найден.")
        sys.exit(1)
        
    try:
        info = get_image_info_imagemagick(image_file)
        print_summary(info)
    except Exception as e:
        print(f"Ошибка при обработке изображения: {e}")

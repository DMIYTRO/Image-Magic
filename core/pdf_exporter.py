"""
Модуль конвертации и сборки входящих растровых/векторных графических файлов в PDF-документ (Image-to-PDF Exporter).
"""

import os
import shutil
import subprocess
from typing import List

def convert_image_to_pdf(input_image_path: str, output_pdf_path: str, dpi: float = 300.0) -> str:
    """Конвертирует одиночное изображение в PDF с сохранением DPI и размера."""
    magick_cmd = shutil.which("magick")
    if not magick_cmd:
        raise FileNotFoundError("ImageMagick (`magick`) не найден.")

    os.makedirs(os.path.dirname(os.path.abspath(output_pdf_path)), exist_ok=True)

    cmd = [
        magick_cmd,
        "-density", str(dpi),
        input_image_path,
        output_pdf_path
    ]
    subprocess.run(cmd, check=True)
    return output_pdf_path

def combine_images_to_pdf(input_image_paths: List[str], output_pdf_path: str, dpi: float = 300.0) -> str:
    """Объединяет список изображений в один многостраничный PDF документ."""
    if not input_image_paths:
        raise ValueError("Список файлов для сборки PDF пуст.")

    magick_cmd = shutil.which("magick")
    if not magick_cmd:
        raise FileNotFoundError("ImageMagick (`magick`) не найден.")

    os.makedirs(os.path.dirname(os.path.abspath(output_pdf_path)), exist_ok=True)

    cmd = [magick_cmd, "-density", str(dpi)] + input_image_paths + [output_pdf_path]
    subprocess.run(cmd, check=True)
    return output_pdf_path

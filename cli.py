#!/usr/bin/env python3
"""
Главная точка входа Image-Magic CLI.
Пакетный допечатный инспектор графических файлов.
"""

import os
import sys
import glob
import argparse
from config.profiles import DEFAULT_PROFILE, PrePressProfile
from core.inspector import inspect_file
from core.preview_generator import generate_preview
from core.report_builder import build_reports
from core.pdf_exporter import combine_images_to_pdf
from validators import get_validator

def main():
    parser = argparse.ArgumentParser(description="Image-Magic: Допечатная проверка макетов и генератор отчётов")
    parser.add_argument("--input", "-i", type=str, default="input_files", help="Путь к папке с макетами")
    parser.add_argument("--output", "-o", type=str, default="output_report", help="Путь к папке отчётов")
    parser.add_argument("--dpi", type=float, default=300.0, help="Требуемый DPI (по умолчанию 300)")

    args = parser.parse_args()

    base_dir = os.path.dirname(os.path.abspath(__file__))
    input_dir = args.input if os.path.isabs(args.input) else os.path.join(base_dir, args.input)
    output_dir = args.output if os.path.isabs(args.output) else os.path.join(base_dir, args.output)

    if not os.path.exists(input_dir):
        print(f"❌ Ошибка: Входная директория '{input_dir}' не найдена.")
        sys.exit(1)

    print(f"🚀 Запуск проверки файлов в папке: {input_dir}")

    previews_dir = os.path.join(output_dir, "previews")
    os.makedirs(previews_dir, exist_ok=True)

    extensions = ("*.jpg", "*.jpeg", "*.tif", "*.tiff", "*.png", "*.pdf")
    files = []
    for ext in extensions:
        files.extend(glob.glob(os.path.join(input_dir, ext)))
        files.extend(glob.glob(os.path.join(input_dir, ext.upper())))

    files.sort()

    profile = PrePressProfile(target_dpi=args.dpi)
    results = []
    preview_file_paths = []

    for file_path in files:
        file_name = os.path.basename(file_path)
        print(f"  🔍 Анализ файла: {file_name}...")

        try:
            # 1. Извлечение метаданных
            meta = inspect_file(file_path)

            # 2. Форматная валидация
            validator = get_validator(meta.format, profile)
            val_result = validator.validate(meta)

            # 3. Генерация превью с рамками
            preview_filename = f"preview_{file_name}.jpg"
            preview_filepath = os.path.join(previews_dir, preview_filename)
            rel_preview_path = f"previews/{preview_filename}"

            generate_preview(
                file_path,
                preview_filepath,
                dpi=meta.dpi,
                w_px=meta.width_px,
                h_px=meta.height_px,
                safe_zone_mm=profile.safe_zone_mm,
                bleed_mm=profile.bleed_mm
            )

            results.append((meta, val_result, rel_preview_path))
            preview_file_paths.append(preview_filepath)

        except Exception as e:
            print(f"⚠️ Ошибка при обработке {file_name}: {e}")

    # 4. Сборка отчётов (HTML, Audit PDF, JSON)
    html_p, json_p, pdf_p = build_reports(results, output_dir)

    # 5. Сборка многостраничного PDF входящих макетов и превью с рамками
    combined_pdf_path = os.path.join(output_dir, "combined_layouts.pdf")
    combined_preview_pdf_path = os.path.join(output_dir, "combined_previews.pdf")
    
    try:
        if files:
            combine_images_to_pdf(files, combined_pdf_path, dpi=profile.target_dpi)
        if preview_file_paths:
            combine_images_to_pdf(preview_file_paths, combined_preview_pdf_path, dpi=profile.target_dpi)
    except Exception as e:
        print(f"⚠️ Предупреждение при сборке многостраничного PDF макетов: {e}")

    print("\n" + "=" * 60)
    print(f"✅ Проверка завершена! Обработано макетов: {len(results)}")
    print(f"📄 HTML-отчёт:    {html_p}")
    print(f"📊 JSON-отчёт:    {json_p}")
    if pdf_p:
        print(f"📕 PDF-отчёт:     {pdf_p}")
    if os.path.exists(combined_pdf_path):
        print(f"📚 Сборный PDF макетов: {combined_pdf_path}")
    if os.path.exists(combined_preview_pdf_path):
        print(f"🖼 Сборный PDF превью:  {combined_preview_pdf_path}")
    print("=" * 60)

if __name__ == "__main__":
    main()

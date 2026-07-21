"""
Ядро сборки отчётов (HTML & JSON).
"""

import os
import json
from typing import List, Tuple
from core.inspector import ImageMetadata
from validators.rules import ValidationResult

def build_reports(results: List[Tuple[ImageMetadata, ValidationResult, str]], output_dir: str):
    """Служит для сборки HTML и JSON отчётов."""
    os.makedirs(output_dir, exist_ok=True)

    # 1. Генерация JSON
    json_path = os.path.join(output_dir, "report.json")
    json_data = []
    for meta, val, rel_preview in results:
        json_data.append({
            "file_name": meta.file_name,
            "format": meta.format,
            "overall_passed": val.overall_passed,
            "preview_path": rel_preview,
            "dimensions_px": {"width": meta.width_px, "height": meta.height_px},
            "dimensions_mm": {"width": meta.width_mm, "height": meta.height_mm},
            "dpi": meta.dpi,
            "colorspace": meta.colorspace,
            "icc_profile": meta.icc_profile,
            "size_mb": meta.size_mb,
            "validation_items": [
                {
                    "name": item.name,
                    "actual": item.actual_value,
                    "target": item.target_value,
                    "passed": item.passed,
                    "message": item.message
                }
                for item in val.items
            ]
        })
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(json_data, f, ensure_ascii=False, indent=2)

    # 2. Генерация HTML
    html_path = os.path.join(output_dir, "report.html")
    cards_html = ""

    for idx, (meta, val, rel_preview) in enumerate(results):
        passed = val.overall_passed

        rows_html = ""
        for item in val.items:
            icon_class = "pass" if item.passed else "fail"
            icon_symbol = "✔" if item.passed else "✖"
            status_text = item.actual_value if item.passed else f'<span class="text-danger">{item.actual_value}</span>'
            
            rows_html += f"""
            <tr>
                <td class="param-title"><span class="status-icon {icon_class}">{icon_symbol}</span> {item.name}</td>
                <td class="val-cell">{item.actual_value}</td>
                <td class="target-cell">{item.target_value}</td>
                <td class="status-cell">{status_text}</td>
            </tr>
            """

        status_box_class = "pass-box" if passed else "fail-box"
        status_msg = (
            "<strong>Макет успешно прошёл автоматическую проверку.</strong><br>Файл равен стандарту допечатной подготовки."
            if passed else
            "<strong>Макет не прошёл автоматическую проверку.</strong><br>"
            "Отдел допечатной подготовки проверит макет и вы получите соответствующее уведомление."
        )

        cards_html += f"""
        <div class="report-card">
            <div class="card-header">
                <span class="side-title">Макет #{idx + 1}:</span>
                <div class="upload-bar">
                    <button class="upload-btn">ФАЙЛ ОБРАБОТАН</button>
                    <div class="file-info">
                        <span class="dot">•</span>
                        <span class="file-name">{meta.file_name}</span>
                        <span class="file-size">{meta.size_mb} МБ</span>
                    </div>
                </div>
            </div>

            <div class="preview-container">
                <div class="preview-frame">
                    <img src="{rel_preview}" alt="Превью {meta.file_name}" class="preview-img">
                </div>
                <div class="legend">
                    <span class="legend-item"><span class="color-box red"></span> Красный контур (1 мм) — край реза</span>
                    <span class="legend-item"><span class="color-box green"></span> Зеленый контур (4 мм) — безопасная зона</span>
                </div>
            </div>

            <table class="params-table">
                <thead>
                    <tr>
                        <th class="col-param">ПАРАМЕТР</th>
                        <th class="col-val">ВАШ ФАЙЛ</th>
                        <th class="col-target">ПОТРЕБНО / НОРМА</th>
                        <th class="col-proc">ОБРАБОТАННЫЙ / СТАТУС</th>
                    </tr>
                </thead>
                <tbody>
                    {rows_html}
                </tbody>
            </table>

            <div class="status-box {status_box_class}">
                <p class="status-message">{status_msg}</p>
                <label class="confirm-checkbox">
                    <input type="checkbox" {'checked' if passed else ''}>
                    <span>Подтверждаю автоматически доработанный макет, претензий по обрезке и цвету иметь не буду.</span>
                </label>
            </div>
        </div>
        """

    html_content = f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Отчёт допечатного контроля макетов (Image-Magic Audit)</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg-color: #f4f6f8;
            --card-bg: #ffffff;
            --text-primary: #212529;
            --text-secondary: #6c757d;
            --header-red: #c02b2b;
            --pass-color: #28a745;
            --fail-color: #dc3545;
            --border-color: #dee2e6;
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background-color: var(--bg-color);
            color: var(--text-primary);
            padding: 40px 20px;
            line-height: 1.5;
        }}
        .container {{ max-width: 900px; margin: 0 auto; }}
        .main-header {{ margin-bottom: 30px; text-align: center; }}
        .main-header h1 {{ font-size: 26px; font-weight: 700; color: #1a1a1a; }}
        .main-header p {{ color: var(--text-secondary); font-size: 14px; margin-top: 5px; }}

        .report-card {{
            background: var(--card-bg);
            border-radius: 8px;
            border: 1px solid var(--border-color);
            padding: 24px;
            margin-bottom: 35px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
        }}
        .card-header {{ margin-bottom: 20px; }}
        .side-title {{ font-size: 16px; font-weight: 600; color: #333; display: block; margin-bottom: 10px; }}
        .upload-bar {{ display: flex; align-items: center; gap: 15px; flex-wrap: wrap; }}
        .upload-btn {{
            background-color: #555;
            color: white;
            border: none;
            padding: 10px 18px;
            font-size: 13px;
            font-weight: 600;
            letter-spacing: 0.5px;
            border-radius: 4px;
            text-transform: uppercase;
        }}
        .file-info {{ font-size: 14px; display: flex; align-items: center; gap: 8px; }}
        .file-name {{ font-weight: 600; color: #222; }}
        .file-size {{ color: #666; }}

        .preview-container {{
            text-align: center;
            margin: 25px 0;
            background: #fafafa;
            padding: 20px;
            border-radius: 6px;
            border: 1px dashed var(--border-color);
        }}
        .preview-frame {{ display: inline-block; box-shadow: 0 5px 15px rgba(0,0,0,0.1); background: #fff; }}
        .preview-img {{ max-width: 100%; max-height: 420px; display: block; height: auto; }}
        .legend {{ margin-top: 12px; font-size: 13px; display: flex; justify-content: center; gap: 20px; color: #555; }}
        .legend-item {{ display: flex; align-items: center; gap: 6px; }}
        .color-box {{ width: 14px; height: 14px; border-radius: 2px; display: inline-block; }}
        .color-box.red {{ background-color: #dc3545; }}
        .color-box.green {{ background-color: #28a745; }}

        .params-table {{ width: 100%; border-collapse: collapse; margin-top: 15px; font-size: 14px; }}
        .params-table th {{
            background-color: var(--header-red);
            color: #ffffff;
            font-weight: 600;
            text-transform: uppercase;
            font-size: 12px;
            letter-spacing: 0.5px;
            padding: 12px 16px;
            text-align: center;
            border: 1px solid var(--header-red);
        }}
        .params-table th.col-param {{ text-align: left; width: 40%; }}
        .params-table td {{ padding: 12px 16px; border: 1px solid var(--border-color); text-align: center; }}
        .params-table td.param-title {{ text-align: left; font-weight: 500; display: flex; align-items: center; gap: 10px; }}

        .status-icon {{
            width: 22px; height: 22px; border-radius: 50%; display: inline-flex;
            align-items: center; justify-content: center; font-size: 12px; font-weight: bold; color: white;
        }}
        .status-icon.pass {{ background-color: var(--pass-color); }}
        .status-icon.fail {{ background-color: var(--fail-color); }}

        .status-box {{ margin-top: 25px; padding: 18px; border-radius: 6px; font-size: 14px; }}
        .status-box.pass-box {{ background-color: #e8f5e9; border: 1px solid #c8e6c9; color: #1b5e20; }}
        .status-box.fail-box {{ background-color: #fff8f8; border: 1px solid #ffcdd2; color: #842029; }}
        .status-message {{ margin-bottom: 12px; line-height: 1.5; }}
        .confirm-checkbox {{ display: flex; align-items: flex-start; gap: 10px; font-size: 13px; color: #333; cursor: pointer; }}
        .confirm-checkbox input {{ margin-top: 3px; }}
        .text-danger {{ color: var(--fail-color); font-weight: 600; }}
    </style>
</head>
<body>
    <div class="container">
        <header class="main-header">
            <h1>Отчёт допечатного контроля макетов (Pre-Press Audit)</h1>
            <p>Модульная пакетная проверка файлов • Вылеты 1 мм (красный) • Безопасная зона 4 мм (зеленый)</p>
        </header>
        {cards_html}
    </div>
</body>
</html>
"""

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    return html_path, json_path

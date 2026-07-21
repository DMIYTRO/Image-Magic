# Image-Magic 🎨 (Pre-Press Audit & Preview Generator)

Модульная система автоматической допечатной проверки (Pre-Press Audit) графических файлов (`TIFF`, `JPEG`, `PNG`, `PDF`) перед отправкой в типографию.

---

## 🏛 Архитектура проекта

```
Image-Magic/
├── core/                           # Основные ядра системы
│   ├── inspector.py                # Извлечение метаданных через ImageMagick
│   ├── preview_generator.py        # Отрисовка рамок (1 мм край реза / 4 мм безопасная зона)
│   └── report_builder.py          # Сборка статических HTML и JSON отчётов
│
├── validators/                     # Форматные валидаторы
│   ├── base.py                     # Базовый класса валидатора (DPI, CMYK, размер)
│   ├── rules.py                    # Модель результатов проверки
│   ├── tiff_validator.py           # Проверки для TIFF файлов (глубина цвета)
│   ├── jpeg_validator.py           # Проверки для JPEG/PNG (сжатие, RGB warning)
│   └── pdf_validator.py            # Проверки для PDF файлов
│
├── config/                         # Конфигурация стандартов
│   └── profiles.py                 # Профили норм (300 DPI, CMYK, лимиты)
│
├── cli.py                          # Главная точка входа (CLI)
├── input_files/                    # Входная папка с макетами
└── output_report/                  # Выходные файлы отчётов (report.html, report.json)
```

---

## 🚀 Быстрый запуск

### 1. Установка зависимости (ImageMagick)
На macOS:
```bash
brew install imagemagick
```

### 2. Запуск проверки макетов
Для запуска проверки файлов в любой папке:
```bash
python3 cli.py --input /путь/к/папке/с/макетами --output /путь/к/папке/отчёта
```

По умолчанию (папка `input_files`):
```bash
python3 cli.py
```

---

## 📊 Результаты работы

После завершения генерируется два типа отчёта:
1. 📄 **`report.html`** — наглядная веб-страница со слоями превью (красный контур 1 мм, зеленый контур 4 мм) и таблицей параметров (*Ваш файл | Норма | Статус*).
2. 📊 **`report.json`** — структурированный JSON со всей метаинформацией для интеграции с другими CRM/ERP системами.

---

## 🔗 Ссылка на репозиторий GitHub
🌐 [https://github.com/DMIYTRO/Image-Magic](https://github.com/DMIYTRO/Image-Magic)

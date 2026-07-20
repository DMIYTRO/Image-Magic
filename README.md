# Работа с метаданными изображений через ImageMagick

В данном руководстве описаны основные способы и консольные команды **ImageMagick (v7+)** для получения ключевых параметров графического файла:
- **Размер в пикселях** (ширина × высота)
- **Разрешение** (DPI / PPI)
- **Физический размер изделия** (в миллиметрах/сантиметрах)
- **Цветовая модель / Пространство** (CMYK, sRGB, RGB, Grayscale и т.д.)
- **Глубина цвета** и наличие альфа-канала.

---

## 1. Установка ImageMagick на macOS

Если ImageMagick еще не установлен, его можно легко установить через Homebrew:

```bash
brew install imagemagick
```

Проверить версию и доступность:
```bash
magick --version
```

---

## 2. Основные консольные команды ImageMagick

В ImageMagick 7 основным инструментом является утилита `magick` (или `magick identify`).

### А. Получение полной подробной информации (`-verbose`)
```bash
magick identify -verbose input.tif
```
Выводит исчерпывающую информацию: EXIF, ICC-профили, гистограмму, каналы цвета и т.д.

---

### Б. Быстрое форматирование нужных параметров (`-format`)
Для получения только конкретных значений используются **percent escapes** (`-format`):

#### 1. Размер в пикселях:
```bash
magick identify -format "Ширина: %w px, Высота: %h px\n" input.png
```

#### 2. Разрешение (DPI) и единицы измерения:
```bash
magick identify -format "Разрешение: %x x %y %[units]\n" input.jpg
```
* `%x` — плотность по горизонтали.
* `%y` — плотность по вертикали.
* `%[units]` — единицы (обычно `PixelsPerInch` = DPI).

#### 3. Цветовая модель / Цветовое пространство:
```bash
magick identify -format "Цветовая модель: %[colorspace] (%[type])\n" input.jpg
```
* `%[colorspace]` — например, `CMYK`, `sRGB`, `Gray`, `RGB`.
* `%[type]` — например, `ColorSeparation` (для CMYK), `TrueColor` или `Palette`.

#### 4. Печатные/физические размеры изделия в миллиметрах (мм):
прямой расчет размеров в мм прямо через консоль:
```bash
magick identify -units PixelsPerInch -format "Ширина: %[fx:w/resolution.x*25.4] мм, Высота: %[fx:h/resolution.y*25.4] мм\n" input.tif
```
```bash
magick identify -format "Печатный размер: %[printsize:w] x %[printsize:h] %[printsize:units]\n" input.tif
```

#### 5. Итоговая универсальная команда (в одну строку):
```bash
magick identify -format "Файл: %f\nФормат: %m\nПиксели: %wx%h px\nDPI: %x x %y %[units]\nЦветовое пространство: %[colorspace]\nГлубина: %[depth] bits\nРазмер печатный: %[printsize:w]x%[printsize:h] %[printsize:units]\n" input.png
```

---

## 3. Использование готового Python-скрипта

В папке создан готовый скрипт [`get_image_info.py`](file:///Users/admin/Documents/Image%20Magic/get_image_info.py).

Запуск:
```bash
python3 get_image_info.py /путь/к/файлу.jpg
```

Скрипт автоматически рассчитает:
1. Пиксельные габариты (`px`).
2. Точный DPI.
3. Физические размеры изделия в **миллиметрах** (`мм`) и **сантиметрах** (`см`).
4. Цветовую модель (`CMYK`, `RGB`, `sRGB` и т.д.).
5. Глубину цвета и наличие альфа-канала.

---

## 5. Генерация превью с разметкой безопасных зон

Для визуальной проверки макета перед печатью создан скрипт [`generate_preview.py`](file:///Users/admin/Documents/Image%20Magic/generate_preview.py).

Скрипт автоматически рисует:
- 🔴 **Красная рамка (1 мм)** по внешнему краю файла (край реза).
- 🟢 **Зеленая рамка (4 мм)** внутрь от каждого края (безопасная зона для текста и логотипов).

### Запуск генерации превью:
```bash
python3 generate_preview.py /путь/к/макету.tif
```
Или с указанием имени выходного файла превью:
```bash
python3 generate_preview.py input.tif preview_output.jpg
```

---

## 7. Пакетная проверка макетов и HTML-отчёт (Pre-Press Audit)

Для сканирования папки с макетами и создания статического HTML-отчёта (как на образце) используется модуль [`batch_inspector.py`](file:///Users/admin/Documents/Image%20Magic/batch_inspector.py).

### Возможности:
- Пакетное сканирование файлов в директории `input_files/`.
- Генерация превью с красным (1 мм) и зеленым (4 мм) рамками.
- Автоматический расчет размеров (мм), DPI, цветовой модели и размера в МБ.
- Валидация по правилам допечатной подготовки.
- Сборка итогового HTML-отчёта [`output_report/report.html`](file:///Users/admin/Documents/Image%20Magic/output_report/report.html).

### Запуск пакетной проверки:
```bash
python3 /Users/admin/Documents/Image\ Magic/batch_inspector.py
```

---

## 8. Ссылки на документацию ImageMagick

* [Официальный сайт ImageMagick](https://imagemagick.org)
* [Документация по утилите Identify](https://imagemagick.org/script/identify.php)
* [Справочник спецификантов % escape (Format and Print Image Properties)](https://imagemagick.org/script/escape.php)



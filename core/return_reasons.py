"""Извлечение шаблонных причин возврата из старого HTML-справочника."""

from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path


class _ReasonsParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.category = "Общие"
        self._capture: str | None = None
        self._parts: list[str] = []
        self.items: list[dict[str, str]] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        tag = tag.lower()
        if tag in {"h1", "h2", "label"}:
            self._capture = tag
            self._parts = []

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if self._capture != tag:
            return
        text = " ".join("".join(self._parts).split())
        if tag in {"h1", "h2"} and text:
            self.category = text
        elif tag == "label" and text:
            self.items.append({"category": self.category, "text": text})
        self._capture = None
        self._parts = []

    def handle_data(self, data: str) -> None:
        if self._capture:
            self._parts.append(data)


def load_return_reasons(template_path: Path | None = None) -> list[dict[str, str]]:
    """Возвращает уникальные причины возврата с категорией из HTML-шаблона."""
    if template_path is None:
        template_path = Path(__file__).resolve().parents[1] / "Цифра - Загальне.html"
    if not template_path.is_file():
        return []

    parser = _ReasonsParser()
    parser.feed(template_path.read_text(encoding="utf-8-sig"))

    result: list[dict[str, str]] = []
    seen: set[str] = set()
    for item in parser.items:
        normalized = item["text"].strip().rstrip(".;")
        key = normalized.casefold()
        if not normalized or key in seen:
            continue
        seen.add(key)
        result.append({"category": item["category"], "text": normalized})
    return result

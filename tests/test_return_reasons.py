import tempfile
import unittest
from pathlib import Path

from core.return_reasons import load_return_reasons


class ReturnReasonsTests(unittest.TestCase):
    def test_extracts_categories_text_and_removes_duplicates(self):
        source = """
        <h1>Размер</h1>
        <label><input type="checkbox"><b>Нет вылетов</b> под обрезку.</label>
        <label><input type="checkbox">Нет вылетов под обрезку.</label>
        <h2>Цвет</h2>
        <label><input type="checkbox">Макет должен быть в CMYK</label>
        """
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "reasons.html"
            path.write_text(source, encoding="utf-8")
            reasons = load_return_reasons(path)

        self.assertEqual(
            reasons,
            [
                {"category": "Размер", "text": "Нет вылетов под обрезку"},
                {"category": "Цвет", "text": "Макет должен быть в CMYK"},
            ],
        )

    def test_project_template_contains_reason_catalog(self):
        reasons = load_return_reasons()
        self.assertGreater(len(reasons), 100)
        self.assertTrue(any("CMYK" in reason["text"] for reason in reasons))


if __name__ == "__main__":
    unittest.main()

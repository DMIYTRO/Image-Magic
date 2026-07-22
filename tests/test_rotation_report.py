import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from core.report_builder import build_orders_html_report
from processing.models import FileCheck, OrderCheck


class RotationReportTests(unittest.TestCase):
    def test_html_shows_rotation_warning_and_controls(self):
        parsed = SimpleNamespace(
            width_mm=90.0, height_mm=50.0, front_colors=4, back_colors=4, side="back"
        )
        item = FileCheck(
            path=Path("order_back.tif"), parsed=parsed,
            actual_width_mm=54.0, actual_height_mm=94.0,
            dpi_x=300.0, dpi_y=300.0, rotation_degrees=90,
        )
        item.warnings.append("back будет автоматически повёрнут на 90°")
        order = OrderCheck("1", "customer", [item])

        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "report.html"
            build_orders_html_report([order], output)
            html = output.read_text(encoding="utf-8")

        self.assertIn("Требуется визуальная проверка", html)
        self.assertIn("Совмещение проверено пользователем", html)
        self.assertIn("Автоматический поворот", html)


if __name__ == "__main__":
    unittest.main()

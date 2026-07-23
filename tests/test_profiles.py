import unittest
from pathlib import Path

from config.profiles import DEFAULT_PROFILE, PROFILES, get_profile
from processing import BatchProcessor


class ProfileTests(unittest.TestCase):
    def test_digital_is_default_and_profiles_are_independent(self):
        self.assertIs(DEFAULT_PROFILE, PROFILES["digital"])
        self.assertEqual(get_profile("digital").direction, "digital")
        self.assertEqual(get_profile("offset").direction, "offset")
        self.assertIsNotNone(get_profile("digital").sheet_trim)
        self.assertIsNone(get_profile("offset").sheet_trim)

    def test_batch_processor_reads_values_from_profile(self):
        profile = get_profile("offset")
        processor = BatchProcessor(Path("input"), Path("output"), profile=profile)
        self.assertIs(processor.profile, profile)
        self.assertEqual(processor.size_extra_mm, profile.bleed_mm * 2)
        self.assertEqual(processor.tolerance_mm, profile.size_tolerance_mm)
        self.assertEqual(processor.min_dpi, profile.min_dpi)
        self.assertIn((4, 4), profile.allowed_color_modes)

    def test_unknown_direction_has_clear_error(self):
        with self.assertRaisesRegex(ValueError, "доступно: digital, offset"):
            get_profile("unknown")


if __name__ == "__main__":
    unittest.main()

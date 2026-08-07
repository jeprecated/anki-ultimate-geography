import tempfile
import unittest
from pathlib import Path

from utils.validate_ids import ROOT, validate


class ValidateIdsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.main = ROOT / "src/data/main.csv"
        cls.ids = (ROOT / "src/data/ids.csv").read_text(encoding="utf-8")

    def validate_change(self, old, new):
        self.assertEqual(self.ids.count(old), 1)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "ids.csv"
            path.write_text(self.ids.replace(old, new), encoding="utf-8")
            validate(self.main, path)

    def test_current_inventory(self):
        self.assertEqual(validate(), (323, 227, 323, 550))
        self.assertIn(
            ",note.bolivia,media.flag.bolivia.blur|media.flag.bolivia,media.map.bolivia\n",
            self.ids,
        )

    def test_rejects_changed_main_csv(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "main.csv"
            path.write_bytes(self.main.read_bytes().replace(b"England", b"England!", 1))
            with self.assertRaisesRegex(ValueError, "differs from the legacy source"):
                validate(path)

    def test_rejects_invalid_or_duplicate_note_ids(self):
        with self.assertRaisesRegex(ValueError, "invalid stable ID"):
            self.validate_change(",note.england,media.flag.england", ",note england,media.flag.england")
        with self.assertRaisesRegex(ValueError, "stable IDs are not unique"):
            self.validate_change(",note.scotland,media.flag.scotland", ",note.england,media.flag.scotland")

    def test_rejects_media_id_or_country_drift(self):
        with self.assertRaisesRegex(ValueError, "flag media IDs differ"):
            self.validate_change(
                "media.flag.bolivia.blur|media.flag.bolivia",
                "media.flag.bolivia|media.flag.bolivia.blur",
            )
        with self.assertRaisesRegex(ValueError, "map media ID differs"):
            self.validate_change("media.map.england", "media.map.england-wrong")
        with self.assertRaisesRegex(ValueError, "country inventory differs"):
            self.validate_change("England,note.england", "England!,note.england")


if __name__ == "__main__":
    unittest.main()

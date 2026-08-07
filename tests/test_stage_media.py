import hashlib
import tempfile
import unittest
from pathlib import Path

from utils.stage_media import check, stage


class StageMediaTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.flags = self.root / "flags"
        self.maps = self.root / "maps"
        self.flags.mkdir()
        self.maps.mkdir()
        (self.flags / "flag.svg").write_bytes(b"flag")
        (self.maps / "map.png").write_bytes(b"map")
        self.manifest = self.root / "media.yaml"
        self.destination = self.root / "staged"
        self.write_manifest(("flag.svg", b"flag"), ("map.png", b"map"))

    def tearDown(self):
        self.temp.cleanup()

    def write_manifest(self, *files):
        self.manifest.write_text(
            "".join(
                f"media.{name.replace('.', '-')}:\n"
                f"  path: {name}\n"
                f"  sha256: {hashlib.sha256(content).hexdigest()}\n"
                for name, content in files
            ),
            encoding="utf-8",
        )

    def run_stage(self):
        return stage((self.flags, self.maps), self.manifest, self.destination, 2)

    def test_stage_and_check(self):
        self.assertEqual(self.run_stage(), 2)
        self.assertEqual(check((self.flags, self.maps), self.manifest, self.destination, 2), 2)

    def test_rejects_basename_collision(self):
        (self.maps / "flag.svg").write_bytes(b"other")
        with self.assertRaisesRegex(ValueError, "collision"):
            self.run_stage()

    def test_rejects_missing_or_extra_source(self):
        (self.maps / "map.png").unlink()
        with self.assertRaisesRegex(ValueError, "expected 2 source files, found 1"):
            self.run_stage()
        (self.maps / "map.png").write_bytes(b"map")
        (self.maps / "extra.png").write_bytes(b"extra")
        with self.assertRaisesRegex(ValueError, "expected 2 source files, found 3"):
            self.run_stage()

    def test_rejects_changed_staged_byte(self):
        self.run_stage()
        (self.destination / "map.png").write_bytes(b"changed")
        with self.assertRaisesRegex(ValueError, "differs from source"):
            check((self.flags, self.maps), self.manifest, self.destination, 2)


if __name__ == "__main__":
    unittest.main()

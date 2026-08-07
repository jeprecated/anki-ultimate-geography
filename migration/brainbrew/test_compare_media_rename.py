import json
import shutil
import tempfile
import unittest
from pathlib import Path

from migration.brainbrew.compare_media_rename import compare


class CompareMediaRenameTest(unittest.TestCase):
    def test_only_approved_prefix_rewrite_passes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            before = root / "before"
            after = root / "after"
            old_names = [f"ug-flag-{index}.svg" for index in range(227)] + [
                f"ug-map-{index}.png" for index in range(323)
            ] + ["_ug-world.js"]
            new_names = [name.replace("ug-flag-", "flag-").replace("ug-map-", "map-") for name in old_names]
            old_fields = ['<img src="ug-flag-0.svg"><img src="ug-map-0.png">', "prose ug-flag-example"]
            new_fields = ['<img src="flag-0.svg"><img src="map-0.png">', "prose ug-flag-example"]
            self.write_target(before, old_names, old_fields)
            self.write_target(after, new_names, new_fields)

            self.assertEqual(compare(before, after), ([], [], [], []))

            changed_fields = [new_fields[0], "prose flag-example"]
            self.write_target(after, new_names, changed_fields)
            self.assertEqual(compare(before, after)[0][0][0], "$.notes[0].fields[1]")

            self.write_target(after, new_names, new_fields)
            (after / "media" / "map-0.png").write_bytes(b"changed")
            self.assertEqual(compare(before, after)[3], ["map-0.png"])

    @staticmethod
    def write_target(root, names, fields):
        if root.exists():
            shutil.rmtree(root)
        root.mkdir()
        (root / "deck.json").write_text(json.dumps({
            "media_files": names,
            "notes": [{"guid": "note", "fields": fields}],
            "note_models": [],
        }))
        media = root / "media"
        media.mkdir()
        for name in names:
            (media / name).write_bytes(b"same")


if __name__ == "__main__":
    unittest.main()

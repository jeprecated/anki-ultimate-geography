import copy
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from migration.brainbrew.certify_full_parity import (
    expected_targets,
    parity_record,
    target_coordinates,
    validate_target_names,
)


class CertifyFullParityTest(unittest.TestCase):
    def test_exact_matrix_and_legacy_coordinates(self):
        targets = expected_targets()
        self.assertEqual(len(targets), 48)
        self.assertEqual(
            target_coordinates("zh-tw-experimental"),
            ("Ultimate Geography [ZH-TW] [Experimental]", "experimental"),
        )
        self.assertEqual(
            target_coordinates("fr-extended"),
            ("Ultimate Geography [FR] [Extended]", "standard"),
        )
        validate_target_names(targets)
        with self.assertRaisesRegex(ValueError, "missing targets: en-standard"):
            validate_target_names(targets - {"en-standard"})
        with self.assertRaisesRegex(ValueError, "unexpected targets: en-hardcore"):
            validate_target_names(targets | {"en-hardcore"})

    def test_parity_record_accepts_serializer_only_changes_and_rejects_content(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            deck = {
                "crowdanki_uuid": "deck",
                "media_files": ["flag.svg"],
                "note_models": [{"crowdanki_uuid": "model", "flds": [], "tmpls": []}],
                "notes": [{"guid": "guid", "fields": ["France"], "tags": []}],
            }
            self.write_target(root / "legacy", deck)
            self.write_target(root / "candidate", dict(reversed(list(deck.items()))), compact=True)

            record = parity_record("en-standard", root / "legacy", root / "candidate")
            self.assertTrue(record["semantic_equal"])
            self.assertTrue(record["media_equal"])
            self.assertFalse(record["byte_equal"])
            self.assertTrue(record["serializer_only"])

            changed = copy.deepcopy(deck)
            changed["notes"][0]["fields"][0] = "Germany"
            self.write_target(root / "candidate", changed)
            record = parity_record("en-standard", root / "legacy", root / "candidate")
            self.assertFalse(record["semantic_equal"])
            self.assertFalse(record["serializer_only"])

    @staticmethod
    def write_target(root, deck, compact=False):
        if root.exists():
            shutil.rmtree(root)
        root.mkdir(parents=True)
        (root / "deck.json").write_text(
            json.dumps(deck, separators=(",", ":")) if compact else json.dumps(deck, indent=2)
        )
        media = root / "media"
        media.mkdir()
        (media / "flag.svg").write_bytes(b"same")


if __name__ == "__main__":
    unittest.main()

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from migration.brainbrew.certify_full_parity import (
    certified_record,
    expected_targets,
    target_coordinates,
    validate_target_names,
)


class CertifyFullParityTest(unittest.TestCase):
    def test_exact_matrix_and_export_coordinates(self):
        targets = expected_targets()
        self.assertEqual(len(targets), 48)
        self.assertEqual(
            target_coordinates("zh-tw-experimental"),
            "Ultimate Geography [ZH-TW] [Experimental]",
        )
        self.assertEqual(
            target_coordinates("fr-extended"),
            "Ultimate Geography [FR] [Extended]",
        )
        validate_target_names(targets)
        with self.assertRaisesRegex(ValueError, "missing targets: en-standard"):
            validate_target_names(targets - {"en-standard"})
        with self.assertRaisesRegex(ValueError, "unexpected targets: en-hardcore"):
            validate_target_names(targets | {"en-hardcore"})

    def test_certified_record_fails_closed_on_semantics_media_and_counts(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            deck = {
                "crowdanki_uuid": "deck",
                "media_files": ["flag.svg"],
                "note_models": [{"crowdanki_uuid": "model", "flds": [], "tmpls": []}],
                "notes": [{"guid": "guid", "fields": ["France"], "tags": []}],
            }
            target = root / "candidate"
            self.write_target(target, deck)
            translations = root / "translations.json"
            translations.write_text(json.dumps({"reports": [{"csv_owned": ["country"]}]}))

            from migration.brainbrew.compare_crowdanki import load_target
            loaded = load_target(target, "fixture")
            certified = {
                "rust": {
                    "semantic_sha256": loaded["semantic_sha256"],
                    "media_tree_sha256": loaded["media_tree_sha256"],
                },
                "notes": 1,
                "note_models": 1,
                "media_count": 1,
                "csv_translation_units": 1,
            }
            self.assertTrue(
                certified_record("en-standard", certified, target, translations)["equal"]
            )

            certified["notes"] = 2
            record = certified_record("en-standard", certified, target, translations)
            self.assertFalse(record["equal"])
            self.assertEqual(record["differences"], ["notes"])

    @staticmethod
    def write_target(root, deck):
        if root.exists():
            shutil.rmtree(root)
        root.mkdir(parents=True)
        (root / "deck.json").write_text(json.dumps(deck, indent=2))
        media = root / "media"
        media.mkdir()
        (media / "flag.svg").write_bytes(b"same")


if __name__ == "__main__":
    unittest.main()

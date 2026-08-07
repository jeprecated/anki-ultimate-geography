import copy
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name("compare_crowdanki.py")


class CompareCrowdAnkiTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.deck = {
            "crowdanki_uuid": "deck-guid",
            "deck_configurations": [{"name": "Default", "new": {"order": 1}}],
            "media_files": ["flag.svg"],
            "note_models": [{"crowdanki_uuid": "model-guid", "tmpls": [{"qfmt": "{{Country}}"}]}],
            "notes": [{"guid": "note-guid", "fields": ["France", "Paris"], "tags": ["country", "eu"]}],
        }
        self.write_target("legacy", self.deck)
        self.write_target("candidate", self.deck)

    def tearDown(self):
        self.temp.cleanup()

    def write_target(self, name, deck, *, media=True, raw=None):
        target = self.root / name
        if target.exists():
            shutil.rmtree(target)
        target.mkdir()
        (target / "deck.json").write_text(
            raw if raw is not None else json.dumps(deck, indent=2), encoding="utf-8"
        )
        if media:
            media_dir = target / "media"
            media_dir.mkdir(exist_ok=True)
            for filename in deck.get("media_files", []):
                path = media_dir / filename
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(b"same media")
        return target

    def run_compare(self, legacy="legacy", candidate="candidate"):
        return subprocess.run(
            [sys.executable, str(SCRIPT), str(self.root / legacy), str(self.root / candidate)],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )

    def test_equal_and_serializer_only_difference_pass(self):
        result = self.run_compare()
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("Parity: equal", result.stdout)

        reordered = dict(reversed(list(self.deck.items())))
        self.write_target("candidate", reordered, raw=json.dumps(reordered, separators=(",", ":")))
        result = self.run_compare()
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("deck.json bytes:", result.stdout)
        self.assertIn("different", result.stdout)
        self.assertIn("Parity: equal", result.stdout)

    def test_top_level_note_order_is_normalized_by_guid(self):
        candidate = copy.deepcopy(self.deck)
        candidate["notes"].append(
            {"guid": "another-guid", "fields": ["Germany", "Berlin"], "tags": ["country", "eu"]}
        )
        legacy = copy.deepcopy(candidate)
        candidate["notes"].reverse()
        self.write_target("legacy", legacy)
        self.write_target("candidate", candidate)

        result = self.run_compare()

        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("semantic JSON sha256 (notes by GUID, media_files by filename)", result.stdout)
        self.assertIn("Parity: equal", result.stdout)

    def test_media_file_order_is_normalized_by_filename(self):
        legacy = copy.deepcopy(self.deck)
        legacy["media_files"].append("map.svg")
        candidate = copy.deepcopy(legacy)
        candidate["media_files"].reverse()
        self.write_target("legacy", legacy)
        self.write_target("candidate", candidate)

        result = self.run_compare()

        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("Parity: equal", result.stdout)

    def test_other_list_order_remains_strict(self):
        cases = [
            (
                "fields",
                lambda deck: deck["notes"][0]["fields"].reverse(),
                "$.notes[0].fields[0]",
            ),
            (
                "tags",
                lambda deck: deck["notes"][0]["tags"].reverse(),
                "$.notes[0].tags[0]",
            ),
            (
                "card templates",
                lambda deck: deck["note_models"][0]["tmpls"].reverse(),
                "$.note_models[0].tmpls[0].name",
            ),
            (
                "generic list",
                lambda deck: deck["deck_configurations"][0]["new"]["delays"].reverse(),
                "$.deck_configurations[0].new.delays[0]",
            ),
        ]
        for label, mutate, expected_path in cases:
            with self.subTest(label=label):
                changed = copy.deepcopy(self.deck)
                changed["note_models"][0]["tmpls"] = [{"name": "first"}, {"name": "second"}]
                changed["deck_configurations"][0]["new"]["delays"] = [1, 10]
                self.write_target("legacy", changed)
                candidate = copy.deepcopy(changed)
                mutate(candidate)
                self.write_target("candidate", candidate)
                result = self.run_compare()
                self.assertEqual(result.returncode, 1, result.stdout)
                self.assertIn(expected_path, result.stdout)

    def test_semantic_identity_surfaces_fail_with_paths(self):
        changes = [
            ("guid", lambda deck: deck["notes"][0].update(guid="changed"), "$.notes[0].guid"),
            ("field", lambda deck: deck["notes"][0]["fields"].__setitem__(1, "Lyon"), "$.notes[0].fields[1]"),
            ("tags", lambda deck: deck["notes"][0]["tags"].reverse(), "$.notes[0].tags[0]"),
            ("model", lambda deck: deck["note_models"][0]["tmpls"][0].update(qfmt="changed"), "$.note_models[0].tmpls[0].qfmt"),
            ("configuration", lambda deck: deck["deck_configurations"][0]["new"].update(order=2), "$.deck_configurations[0].new.order"),
            ("scalar type", lambda deck: deck["deck_configurations"][0]["new"].update(order=True), "$.deck_configurations[0].new.order"),
            ("deck identity", lambda deck: deck.update(crowdanki_uuid="changed"), "$.crowdanki_uuid"),
        ]
        for label, mutate, expected_path in changes:
            with self.subTest(label=label):
                changed = copy.deepcopy(self.deck)
                mutate(changed)
                self.write_target("candidate", changed)
                result = self.run_compare()
                self.assertEqual(result.returncode, 1, result.stdout)
                self.assertIn(expected_path, result.stdout)

    def test_missing_and_malformed_inputs_fail_cleanly(self):
        cases = []
        cases.append(("target", "absent", "candidate", "target directory is missing"))

        no_deck = self.root / "no-deck"
        no_deck.mkdir()
        cases.append(("deck", "legacy", "no-deck", "deck.json is missing"))

        self.write_target("bad-json", self.deck, raw="{")
        cases.append(("malformed", "legacy", "bad-json", "invalid deck.json"))

        self.write_target("duplicate", self.deck, raw='{"media_files":[],"media_files":[]}')
        cases.append(("duplicate key", "legacy", "duplicate", "duplicate JSON key"))

        duplicate_guid = copy.deepcopy(self.deck)
        duplicate_guid["notes"].append(copy.deepcopy(duplicate_guid["notes"][0]))
        self.write_target("duplicate-guid", duplicate_guid)
        cases.append(("duplicate GUID", "legacy", "duplicate-guid", "notes contains duplicate GUIDs"))

        self.write_target("no-media", self.deck, media=False)
        cases.append(("media directory", "legacy", "no-media", "media directory is missing"))

        for label, legacy, candidate, message in cases:
            with self.subTest(label=label):
                result = self.run_compare(legacy, candidate)
                self.assertEqual(result.returncode, 2, result.stdout)
                self.assertIn(message, result.stdout)

    def test_each_target_is_validated_against_declared_media(self):
        for target in ("legacy", "candidate"):
            (self.root / target / "media" / "flag.svg").unlink()
        result = self.run_compare()
        self.assertEqual(result.returncode, 2, result.stdout)
        self.assertIn("legacy: missing declared media: flag.svg", result.stdout)

        self.write_target("legacy", self.deck)
        self.write_target("candidate", self.deck)
        (self.root / "candidate" / "media" / "extra.txt").write_bytes(b"extra")
        result = self.run_compare()
        self.assertEqual(result.returncode, 2, result.stdout)
        self.assertIn("candidate: undeclared media: extra.txt", result.stdout)

    def test_media_filename_and_byte_differences_fail(self):
        changed = copy.deepcopy(self.deck)
        changed["media_files"] = ["map.svg"]
        self.write_target("candidate", changed)
        result = self.run_compare()
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("Media missing from candidate: flag.svg", result.stdout)
        self.assertIn("Media extra in candidate: map.svg", result.stdout)

        self.write_target("candidate", self.deck)
        (self.root / "candidate" / "media" / "flag.svg").write_bytes(b"changed media")
        result = self.run_compare()
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("Media changed: flag.svg", result.stdout)
        self.assertIn("sha256=", result.stdout)


if __name__ == "__main__":
    unittest.main()

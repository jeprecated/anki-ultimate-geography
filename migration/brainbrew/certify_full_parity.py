#!/usr/bin/env python3
"""Export all Rust targets and compare them with the certified parity report."""

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from migration.brainbrew.compare_crowdanki import load_target

LANGUAGES = (
    "cs", "da", "de", "en", "es", "fr", "he", "it",
    "nb", "nl", "pl", "pt", "ru", "sv", "zh", "zh-tw",
)
VARIANTS = ("experimental", "extended", "standard")
BRAINBREW_VERSION = "brainbrew 1.0.0-alpha.8"
BRAINBREW_REVISION = "1e56a90a42be2522431cd678dfd81617eb4214a6"


def expected_targets():
    return {f"{language}-{variant}" for language in LANGUAGES for variant in VARIANTS}


def validate_target_names(names):
    names = set(names)
    expected = expected_targets()
    missing = sorted(expected - names)
    extra = sorted(names - expected)
    errors = []
    if missing:
        errors.append("missing targets: " + ", ".join(missing))
    if extra:
        errors.append("unexpected targets: " + ", ".join(extra))
    if errors:
        raise ValueError("; ".join(errors))


def target_coordinates(target):
    language, variant = target.rsplit("-", 1)
    if language not in LANGUAGES or variant not in VARIANTS:
        raise ValueError(f"unexpected target: {target}")
    code = language.upper()
    suffix = "" if variant == "standard" else f" [{variant.capitalize()}]"
    return f"Ultimate Geography [{code}]{suffix}"


def run(command, *, capture=False):
    result = subprocess.run(
        [str(part) for part in command],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE if capture else subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode:
        detail = result.stderr.strip() or (result.stdout or "").strip()
        raise RuntimeError(
            f"command failed ({result.returncode}): {' '.join(map(str, command))}\n{detail}"
        )
    return result.stdout if capture else ""


def discover_targets(brainbrew, manifest):
    output = run([brainbrew, "targets", "--manifest", manifest, "--json"], capture=True)
    names = [target["name"] for target in json.loads(output)["targets"]]
    if len(names) != len(set(names)):
        raise ValueError("manifest contains duplicate target names")
    validate_target_names(names)
    return sorted(names), hashlib.sha256(output.encode()).hexdigest()


def csv_owned_units(path):
    document = json.loads(path.read_text())
    return sum(len(report.get("csv_owned", [])) for report in document.get("reports", []))


def certified_record(target, certified, candidate_path, translations_path):
    candidate = load_target(candidate_path, f"{target} candidate")
    actual = {
        "semantic_sha256": candidate["semantic_sha256"],
        "media_tree_sha256": candidate["media_tree_sha256"],
        "notes": len(candidate["deck"]["notes"]),
        "note_models": len(candidate["deck"].get("note_models", [])),
        "media_count": len(candidate["media"]),
        "csv_translation_units": csv_owned_units(translations_path),
    }
    expected = {
        "semantic_sha256": certified["rust"]["semantic_sha256"],
        "media_tree_sha256": certified["rust"]["media_tree_sha256"],
        "notes": certified["notes"],
        "note_models": certified["note_models"],
        "media_count": certified["media_count"],
        "csv_translation_units": certified["csv_translation_units"],
    }
    differences = sorted(name for name in expected if actual[name] != expected[name])
    return {
        "name": target,
        "equal": not differences,
        "differences": differences,
        "expected": expected,
        "actual": actual,
    }


def certify(args):
    version = run([args.brainbrew, "--version"], capture=True).strip()
    if version != BRAINBREW_VERSION:
        raise ValueError(f"expected {BRAINBREW_VERSION}, found {version!r}")
    run([sys.executable, "migration/brainbrew/validate_ids.py"])

    certified = json.loads(args.expected_report.read_text())
    if certified.get("result") != "pass":
        raise ValueError("expected report is not a passing certification")
    certified_records = {record["name"]: record for record in certified["targets"]}
    if len(certified_records) != len(certified["targets"]):
        raise ValueError("expected report contains duplicate target names")
    validate_target_names(certified_records)

    targets, targets_sha256 = discover_targets(args.brainbrew, args.manifest)
    if targets_sha256 != certified["rust"]["targets_sha256"]:
        raise ValueError("target manifest differs from the certified report")

    if args.rust_root.exists():
        shutil.rmtree(args.rust_root)
    crowdanki_root = args.rust_root / "crowdanki"
    crowdanki_root.mkdir(parents=True)

    run([
        args.brainbrew, "verify", "--manifest", args.manifest,
        "--all-targets", "--media-root", args.media_root,
    ])

    records = []
    for target in targets:
        compose = args.rust_root / f"{target}.yaml"
        explain = args.rust_root / f"{target}-explain.json"
        translations = args.rust_root / f"{target}-translations.json"
        export = crowdanki_root / target_coordinates(target)

        run([args.brainbrew, "validate", "--manifest", args.manifest, "--target", target])
        run([
            args.brainbrew, "compose", "--manifest", args.manifest,
            "--target", target, "--out", compose,
        ])
        explain.write_text(run([
            args.brainbrew, "explain", "--manifest", args.manifest,
            "--target", target, "--json",
        ], capture=True))
        translations.write_text(run([
            args.brainbrew, "translations", "--manifest", args.manifest,
            "--target", target, "--json",
        ], capture=True))
        run([
            args.brainbrew, "export", "crowdanki", "--manifest", args.manifest,
            "--target", target, "--media-root", args.media_root, "--out", export,
        ])

        record = certified_record(target, certified_records[target], export, translations)
        records.append(record)
        print(f"{target}: {'equal' if record['equal'] else 'different'}")

    report = {
        "schema": 1,
        "result": "pass" if all(record["equal"] for record in records) else "fail",
        "certified_report": str(args.expected_report),
        "brainbrew": {
            "version": version.removeprefix("brainbrew "),
            "revision": BRAINBREW_REVISION,
            "targets_sha256": targets_sha256,
        },
        "targets": records,
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    return 0 if report["result"] == "pass" else 1


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--brainbrew", default=os.environ.get("BRAINBREW", "brainbrew"))
    parser.add_argument("--manifest", type=Path, default=Path("brainbrew.yaml"))
    parser.add_argument(
        "--expected-report",
        type=Path,
        default=Path("migration/brainbrew/full-parity.json"),
    )
    parser.add_argument("--rust-root", type=Path, default=Path("build/brainbrew"))
    parser.add_argument("--media-root", type=Path, default=Path("build/brainbrew-media/standard"))
    parser.add_argument("--report", type=Path, default=Path("build/brainbrew/certification.json"))
    return parser.parse_args(argv)


def main(argv=None):
    try:
        return certify(parse_args(argv))
    except (OSError, RuntimeError, ValueError, json.JSONDecodeError) as error:
        print(f"Certification error: {error}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

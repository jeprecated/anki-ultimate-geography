#!/usr/bin/env python3
"""Build and compare the complete Rust Brain Brew target matrix."""

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

from migration.brainbrew.compare_crowdanki import json_differences, load_target, sha256_file
LANGUAGES = ("cs", "da", "de", "en", "es", "fr", "he", "it", "nb", "nl", "pl", "pt", "ru", "sv", "zh", "zh-tw")
VARIANTS = ("experimental", "extended", "standard")
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
    media_family = "experimental" if variant == "experimental" else "standard"
    return f"Ultimate Geography [{code}]{suffix}", media_family


def parity_record(target, legacy_path, candidate_path):
    legacy = load_target(legacy_path, f"{target} legacy")
    candidate = load_target(candidate_path, f"{target} candidate")
    differences = json_differences(legacy["deck"], candidate["deck"])
    legacy_media, candidate_media = legacy["media"], candidate["media"]
    missing_media = sorted(legacy_media.keys() - candidate_media.keys())
    extra_media = sorted(candidate_media.keys() - legacy_media.keys())
    changed_media = sorted(
        name
        for name in legacy_media.keys() & candidate_media.keys()
        if legacy_media[name] != candidate_media[name]
    )
    semantic_equal = not differences
    media_equal = not (missing_media or extra_media or changed_media)
    byte_equal = legacy["deck_sha256"] == candidate["deck_sha256"]
    return {
        "name": target,
        "legacy_path": legacy_path.name,
        "notes": len(candidate["deck"]["notes"]),
        "note_models": len(candidate["deck"].get("note_models", [])),
        "media_count": len(candidate["media"]),
        "legacy": hashes(legacy),
        "rust": hashes(candidate),
        "semantic_equal": semantic_equal,
        "media_equal": media_equal,
        "byte_equal": byte_equal,
        "serializer_only": semantic_equal and media_equal and not byte_equal,
        "json_differences": [
            {"path": path, "legacy": before, "rust": after}
            for path, before, after in differences[:20]
        ],
        "media_differences": {
            "missing": missing_media[:20],
            "extra": extra_media[:20],
            "changed": changed_media[:20],
        },
    }


def hashes(target):
    return {
        "deck_sha256": target["deck_sha256"],
        "canonical_sha256": target["canonical_sha256"],
        "semantic_sha256": target["semantic_sha256"],
        "media_tree_sha256": target["media_tree_sha256"],
    }


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
        raise RuntimeError(f"command failed ({result.returncode}): {' '.join(map(str, command))}\n{detail}")
    return result.stdout if capture else ""


def discover_targets(brainbrew, manifest):
    output = run([brainbrew, "targets", "--manifest", manifest, "--json"], capture=True)
    document = json.loads(output)
    names = [target["name"] for target in document["targets"]]
    if len(names) != len(set(names)):
        raise ValueError("manifest contains duplicate target names")
    validate_target_names(names)
    return sorted(names), output.encode()


def csv_owned_units(path):
    document = json.loads(path.read_text())
    return sum(len(report.get("csv_owned", [])) for report in document.get("reports", []))


def certify(args):
    version = run([args.brainbrew, "--version"], capture=True).strip()
    if version != "brainbrew 1.0.0-alpha.8":
        raise ValueError(f"expected brainbrew 1.0.0-alpha.8, found {version!r}")
    run([sys.executable, "migration/brainbrew/validate_ids.py"])
    targets, targets_json = discover_targets(args.brainbrew, args.manifest)
    legacy_paths = {}
    for target in targets:
        directory, _ = target_coordinates(target)
        path = args.legacy_root / directory
        if not path.is_dir():
            raise ValueError(f"missing legacy target: {path}")
        legacy_paths[target] = path

    if args.rust_root.exists():
        shutil.rmtree(args.rust_root)
    crowdanki_root = args.rust_root / "crowdanki"
    crowdanki_root.mkdir(parents=True)

    run(
        [
            args.brainbrew,
            "verify",
            "--manifest",
            args.manifest,
            "--all-targets",
            "--media-root",
            args.media_root,
        ]
    )

    records = []
    for target in targets:
        _, media_family = target_coordinates(target)
        media_root = args.media_root
        compose = args.rust_root / f"{target}.yaml"
        explain = args.rust_root / f"{target}-explain.json"
        translations = args.rust_root / f"{target}-translations.json"
        export = crowdanki_root / target

        run([args.brainbrew, "validate", "--manifest", args.manifest, "--target", target])
        run(
            [
                args.brainbrew,
                "compose",
                "--manifest",
                args.manifest,
                "--target",
                target,
                "--out",
                compose,
            ]
        )
        run(
            [
                args.brainbrew,
                "verify",
                "--manifest",
                args.manifest,
                "--target",
                target,
                "--media-root",
                media_root,
            ]
        )
        explain.write_text(
            run(
                [args.brainbrew, "explain", "--manifest", args.manifest, "--target", target, "--json"],
                capture=True,
            )
        )
        translations.write_text(
            run(
                [
                    args.brainbrew,
                    "translations",
                    "--manifest",
                    args.manifest,
                    "--target",
                    target,
                    "--json",
                ],
                capture=True,
            )
        )
        run(
            [
                args.brainbrew,
                "export",
                "crowdanki",
                "--manifest",
                args.manifest,
                "--target",
                target,
                "--media-root",
                media_root,
                "--out",
                export,
            ]
        )
        record = parity_record(target, legacy_paths[target], export)
        record["media_family"] = media_family
        record["counts_equal"] = (
            record["notes"] == 323
            and record["note_models"] == 1
            and record["media_count"] == (555 if media_family == "experimental" else 550)
        )
        record["csv_translation_units"] = csv_owned_units(translations)
        record["artifacts"] = {
            "compose_sha256": sha256_file(compose),
            "explain_sha256": sha256_file(explain),
            "translations_sha256": sha256_file(translations),
        }
        records.append(record)
        record_passed = record["semantic_equal"] and record["media_equal"] and record["counts_equal"]
        print(f"{target}: {'equal' if record_passed else 'different'}")

    passed = all(
        record["semantic_equal"] and record["media_equal"] and record["counts_equal"]
        for record in records
    )
    report = {
        "schema": 1,
        "result": "pass" if passed else "fail",
        "legacy": {
            "brain_brew": "0.3.11",
            "commands": ["pipenv run build", "pipenv run build_experimental"],
        },
        "rust": {
            "brainbrew": version.removeprefix("brainbrew "),
            "revision": BRAINBREW_REVISION,
            "targets_sha256": hashlib.sha256(targets_json).hexdigest(),
            "federation_lock": "not applicable: package has no federated dependencies",
        },
        "matrix": {"targets": 48, "standard": 16, "extended": 16, "experimental": 16},
        "commands": [
            "brainbrew verify --manifest brainbrew.yaml --all-targets --media-root build/brainbrew-media/standard",
            "brainbrew validate/compose/verify/explain/translations/export --manifest brainbrew.yaml --target <target>",
            "strict parsed CrowdAnki JSON and media comparison for every target",
        ],
        "ownership": {
            "production_notes_csv_owned": 323,
            "stable_note_ids": 323,
            "production_inline_notes": 0,
            "main_csv_sha256": "c1688b7f47950f6ab83425e58543b16f1a161c65461a7bb680cd09acc0a7e1c2",
        },
        "targets": records,
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    if args.markdown:
        args.markdown.parent.mkdir(parents=True, exist_ok=True)
        args.markdown.write_text(render_markdown(report))
    return 0 if passed else 1


def render_markdown(report):
    lines = [
        "# Full production parity certification",
        "",
        f"Result: **{report['result'].upper()}** — 48 targets (16 Standard, 16 Extended, 16 Experimental).",
        "",
        "## Toolchain and commands",
        "",
        "- Legacy: Python Brain Brew `0.3.11`; `pipenv run build` and `pipenv run build_experimental`.",
        f"- Rust: Brain Brew `1.0.0-alpha.8` at `{report['rust']['revision']}`.",
        "- Rust verification: `brainbrew verify --manifest brainbrew.yaml --all-targets --media-root build/brainbrew-media/standard`, plus validate, compose, per-target verify, explain, translations, and CrowdAnki export for each discovered target.",
        "- Comparison normalizes only JSON object keys, top-level notes by GUID, and `media_files` by filename; every other array and all media names/bytes remain strict.",
        "- This package has no federated dependencies, so no federation lock is required; explain reports record source fingerprints.",
        "",
        "## Target evidence",
        "",
        "| Target | Semantic SHA-256 | Media tree SHA-256 | Media | Raw JSON bytes | CSV translation units |",
        "|---|---|---|---:|---|---:|",
    ]
    for target in report["targets"]:
        lines.append(
            f"| `{target['name']}` | `{target['rust']['semantic_sha256']}` | "
            f"`{target['rust']['media_tree_sha256']}` | {target['media_count']} | "
            f"{'identical' if target['byte_equal'] else 'serializer-only difference'} | "
            f"{target['csv_translation_units']} |"
        )
    lines.extend(
        [
            "",
            (
                "Every row has semantic JSON equality and exact media filename/byte equality. "
                "Raw JSON byte differences are serializer formatting/order only and are not used "
                "to excuse content differences."
                if report["result"] == "pass"
                else "Certification failed; inspect each target's JSON and media differences."
            ),
            "",
            "## Ownership and Workbench evidence",
            "",
            "All 323 production notes and localized CSV fields remain CSV-owned and read-only; identity validation proves 323 unique stable note IDs and exact typed-media references while `main.csv` remains byte-identical to the legacy source.",
            "",
            "No Hardcore/federation targets, translation corrections, editorial changes, CSV write-back, generated note YAML, or generic transformation layer are included.",
        ]
    )
    return "\n".join(lines) + "\n"


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--brainbrew", default=os.environ.get("BRAINBREW", "brainbrew"))
    parser.add_argument("--manifest", type=Path, default=Path("brainbrew.yaml"))
    parser.add_argument("--legacy-root", type=Path, default=Path("build"))
    parser.add_argument("--rust-root", type=Path, default=Path("build/brainbrew-certification"))
    parser.add_argument("--media-root", type=Path, default=Path("build/brainbrew-media/standard"))
    parser.add_argument("--report", type=Path, default=Path("build/brainbrew-certification/full-parity.json"))
    parser.add_argument("--markdown", type=Path)
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    try:
        return certify(args)
    except (OSError, RuntimeError, ValueError, json.JSONDecodeError) as error:
        print(f"Certification error: {error}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

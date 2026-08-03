#!/usr/bin/env python3
"""Regenerate the six representative Ultimate Geography CrowdAnki goldens."""

from pathlib import Path
import os
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
TARGETS = (
    "en-standard",
    "en-extended",
    "en-experimental",
    "de-standard",
    "he-standard",
    "zh-standard",
)


def media_root() -> tuple[Path, bool]:
    final = ROOT / "media"
    if final.is_dir():
        return final, False
    staged = ROOT / "build" / "migration-media"
    shutil.rmtree(staged, ignore_errors=True)
    staged.mkdir(parents=True)
    for folder in ("flags", "maps", "experimental_assets"):
        for source in (ROOT / "src" / "media" / folder).iterdir():
            if source.is_file():
                shutil.copy2(source, staged / source.name)
    return staged, True


def main() -> None:
    binary = os.environ.get("BRAINBREW", "brainbrew")
    media, temporary = media_root()
    try:
        for target in TARGETS:
            output = ROOT / "goldens" / target
            shutil.rmtree(output, ignore_errors=True)
            subprocess.run(
                [binary, "export", "crowdanki", "--manifest", "brainbrew.yaml", "--target", target,
                 "--out", str(output), "--media-root", str(media), "--force"],
                cwd=ROOT,
                check=True,
            )
            shutil.rmtree(output / "media", ignore_errors=True)
        subprocess.run(
            [binary, "verify", "--manifest", "brainbrew.yaml", "--all-targets", "--media-root", str(media)],
            cwd=ROOT,
            check=True,
        )
    finally:
        if temporary:
            shutil.rmtree(media, ignore_errors=True)


if __name__ == "__main__":
    main()

# Legacy Python Brain Brew baseline

This is the immutable oracle for the Rust Brain Brew migration. It was generated from the tracked tree at UG commit `c4f044b5b4c2c0ba209ca55fe746706e6fc266de`, verified locally with:

```console
$ jj log -r c4f044b5b4c2c0ba209ca55fe746706e6fc266de --no-graph -T 'commit_id ++ "\n"'
c4f044b5b4c2c0ba209ca55fe746706e6fc266de
```

The commands below export all 620 tracked files at that revision to a clean temporary directory, avoiding both the current task change and ignored historical outputs. No generated file below is checked in.

## Reproduction environment and commands

`Pipfile.lock` SHA-256: `6233b29d040f323c74a57af2e5ccc7bc87e116b6647840eae42a1a9287c0f7cf`

```console
$ revision=c4f044b5b4c2c0ba209ca55fe746706e6fc266de
$ baseline_root=$(mktemp -d)
$ jj file list -r "$revision" | while IFS= read -r path; do
    mkdir -p "$baseline_root/$(dirname "$path")"
    jj file show -r "$revision" -- "$path" > "$baseline_root/$path"
  done
$ cd "$baseline_root"
$ uv python install 3.11.15
Installed Python 3.11.15
$ uv tool install --python 3.11.15 pipenv==2026.7.1
Installed pipenv==2026.7.1
$ PIPENV_VENV_IN_PROJECT=1 PIPENV_IGNORE_VIRTUALENVS=1 \
    pipenv --python "$(uv python find 3.11.15)" sync --dev
All dependencies are now up-to-date!
$ pipenv run python --version
Python 3.11.15
$ pipenv run python -m pip show brain-brew | grep -E '^(Name|Version):'
Name: Brain-Brew
Version: 0.3.11
$ pipenv run python -m pip freeze --all
Brain-Brew==0.3.11
pip==26.2
PyYAML==6.0.2
ruamel.yaml==0.18.10
ruamel.yaml.clib==0.2.12
setuptools==83.0.0
yamale==6.0.0
$ pipenv run build
Successfully generated template files.
Successfully built deck.
$ pipenv run build_experimental
Successfully generated template files.
Successfully built deck.
```

The regular recipe produced 16 Standard and 16 Extended targets (32 total). The Experimental recipe produced 16 targets. All **48** output directories contained `deck.json`.

| Family | Targets | Notes per target | Note models per target | Media per target |
|---|---:|---:|---:|---:|
| Standard | 16 | 323 | 1 | 550 |
| Extended | 16 | 323 | 1 | 550 |
| Experimental | 16 | 323 | 1 | 555 |

## Representative evidence

The canonical JSON digest is SHA-256 of parsed JSON serialized as UTF-8 with sorted object keys and compact separators. The media-tree digest hashes sorted `(UTF-8 relative filename, NUL, raw SHA-256 bytes)` pairs, matching `migration/brainbrew/compare_crowdanki.py`.

| Target | Notes | Note models | Media | `deck.json` bytes | Raw JSON SHA-256 | Canonical JSON SHA-256 | Media-tree SHA-256 |
|---|---:|---:|---:|---:|---|---|---|
| `Ultimate Geography [EN]` | 323 | 1 | 550 | 228050 | `3b5c682a8500f51bc73be31501ba6670fdc5b42244c33c73d1c65bdfa93252b9` | `8a4e83a67cf2d52d797e31bde3162e5885eef6350bde815063717419235386d7` | `be1ec8784102046ccefa0874d7d3a7e7feaff94372eedebd5ec727b920497d95` |
| `Ultimate Geography [DE]` | 323 | 1 | 550 | 228500 | `c3c896877103a9861940931570e7b7431a9bd553716cebd3b9816221603296d6` | `37ea96cff26ad6b74111c2ea7fd52584717fa6aeaf194ade4ae664c11d7174a3` | `be1ec8784102046ccefa0874d7d3a7e7feaff94372eedebd5ec727b920497d95` |
| `Ultimate Geography [EN] [Experimental]` | 323 | 1 | 555 | 239189 | `c7be5e7a3af6ec72188c1f3d1682ddaab25237fb3b39647b9bc3c7a729bf7814` | `9932816f0d44d720d80359dcaa4bf3966cdb6cafa5689301196a9a4a13e679c3` | `a7f8acc1b531c6e777ea8f81a2c445cfc278c2d984a6dcc1424fad94de093df8` |
| `Ultimate Geography [DE] [Experimental]` | 323 | 1 | 555 | 239639 | `c23b8f6edc97d69443c94862f26389421c31b6b4e1fcd48346ed6849687f27c1` | `966fffb2e64d36760d8fb21ff6406b41f220e21aa83ab3b90f380e1735252b9f` | `a7f8acc1b531c6e777ea8f81a2c445cfc278c2d984a6dcc1424fad94de093df8` |

Each representative directory passed a self-comparison with `python migration/brainbrew/compare_crowdanki.py LEGACY_DIR LEGACY_DIR`, including exact declared-versus-present media validation.

The regenerated legacy directory remains the oracle. These compact hashes prove what was observed but do not replace the later directory-to-directory parity comparison.

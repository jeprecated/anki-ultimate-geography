# Brain Brew migration evidence

This migration is based on Ultimate Geography `c4f044b5b4c2`, including the Strait of Gibraltar and Gulf of Oman additions. It introduces Brain Brew `1.0.0-alpha.4` directly; historical alpha schema churn is not part of the review series.

## Coverage

Before the legacy workflow is removed, CI runs both the Python build and native verification. Native verification covers all 48 non-Hardcore targets: 16 languages across Standard, Extended, and Experimental variants.

Six parsed CrowdAnki goldens cover the principal output classes:

- `en-standard`: source language
- `en-extended`: Extended variant
- `en-experimental`: Experimental variant and interactive-map assets
- `de-standard`: ordinary translation
- `he-standard`: RTL translation
- `zh-standard`: contextual CJK translation

The goldens include complete deck identity/configuration, note models, card HTML/CSS, ordered fields, note GUIDs, note values, and tags. Strict media verification separately checks every declared filename, SHA-256, and byte.

## Reproduction

Install the pinned release and regenerate the representative outputs:

```bash
cargo install brainbrew --version '=1.0.0-alpha.4' --locked
python scripts/update-ug-goldens.py
```

During the coexistence layers, CI materializes `build/migration-media` by flattening the legacy `src/media/{flags,maps,experimental_assets}` directories without changing tracked files. After cutover, verification uses the tracked flat `media/` directory directly.

Intentional migration changes are limited to source representation and the already-reviewed corrections recorded in the stacked PRs. Gibraltar and Gulf of Oman are current-upstream additions rather than migration deltas.

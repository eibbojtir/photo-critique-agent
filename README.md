# Photo Critique Agent

Local-first Python project scaffold for reviewing folders of JPEG images with persona-driven critique output.

## Current Scope

This initial scaffold includes:

- A CLI entrypoint named `photo-critique`
- Core Pydantic models for jobs, personas, photos, and reports
- Bundled YAML persona support with one persona: `wildlife`
- A placeholder Jinja2 Markdown template
- Unit tests covering the core models and persona loading

The current implementation includes a deterministic first-pass critique pipeline based on metadata only. Actual vision-model evaluation is still deferred.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Usage

Validate inputs for a critique job:

```bash
photo-critique ./photos --persona wildlife
```

Include supplemental metadata:

```bash
photo-critique ./photos --metadata-csv ./metadata.csv --persona wildlife
```

Inspect a folder of JPEGs, merge optional CSV metadata, and write normalized assets to `output/assets.json`:

```bash
photo-critique inspect ./photos
photo-critique inspect ./photos --metadata ./metadata.csv
```

The inspect command prints a short summary, extracts EXIF metadata when available, and normalizes each discovered image into a `PhotoAsset` payload.

Analyze a folder with the placeholder evaluator and a bundled persona:

```bash
photo-critique analyze ./photos --persona wildlife
photo-critique analyze ./photos --metadata ./metadata.csv --persona wildlife
```

The analyze command loads the selected YAML persona, runs a deterministic metadata-based evaluator, and writes a local output bundle:

- `output/results.json`
- `output/critique_report.md`
- `output/critique_report.html`

Open `output/critique_report.html` directly in a browser for a simple local demo.

Generated files under `output/` are intentionally ignored by git so local image metadata and file paths do not get committed by accident.

For documentation and public-repo examples, use the anonymized sample bundle in `examples/sample_output/`:

- `examples/sample_output/results.json`
- `examples/sample_output/critique_report.md`
- `examples/sample_output/critique_report.html`
- `examples/sample_output/assets.json`

## Project Layout

```text
src/photo_critique_agent/
  cli.py
  models/
  personas/
  templates/
tests/
```

## Testing

```bash
pytest
```

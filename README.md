# Photo Critique Agent

Local-first Python project scaffold for reviewing folders of JPEG images with persona-driven critique output.

## Current Scope

This initial scaffold includes:

- A CLI entrypoint named `photo-critique`
- Core Pydantic models for jobs, personas, photos, and reports
- Bundled YAML persona support with one persona: `wildlife`
- A placeholder Jinja2 Markdown template
- Unit tests covering the core models and persona loading

Implementation of EXIF extraction, CSV ingestion, and final report rendering is intentionally deferred.

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

The scaffolded CLI currently validates arguments and prints the normalized job configuration as JSON.

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

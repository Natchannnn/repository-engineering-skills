# Evidence Record Template & Schema

This directory provides the canonical template and JSON Schema for recording reproducible evaluation runs, demo experiments, and agent trajectories across the repository.

---

## 1. Overview

This directory provides a canonical template and JSON Schema Draft 2020-12 contract for recording new evaluation runs, demo experiments, and agent evaluation trajectories.

- **`evidence-record.schema.json`**: Formal schema enforcing required structural fields, ISO 8601 UTC timestamp format, execution command records with integer exit codes, and explicit limitations. *(Note: Schema validation verifies record structure and field completeness; it does not independently verify the factual execution of recorded metrics, nor does it claim that historical archived benchmarks retrospectively conform to this schema).*
- **`run-template.json`**: Starter template containing placeholder fields for authoring a new evidence record.

---

## 2. Schema Structure

A valid evidence record contains the following top-level properties:

| Field | Type | Description |
| :--- | :--- | :--- |
| `schema_version` | `string` | Semantic version of the schema contract (e.g., `"1.0.0"`). |
| `run_id` | `string` | Unique identifier for this evaluation run. |
| `recorded_at_utc` | `string` | Date and time of execution in ISO 8601 UTC format (`YYYY-MM-DDTHH:MM:SSZ`). |
| `skill` | `object` | Tested skill metadata (`name`, 40-char hex `source_commit`, `distribution`). |
| `fixture` | `object` | Fixture metadata (`name`, 40-char hex `bootstrap_commit`). |
| `environment` | `object` | Execution environment (`host`, `model`, `os`, `python_version`). |
| `execution` | `object` | Prompt file path and list of `commands_executed` (with `cmd` string and integer `exit_code`). |
| `verification_results` | `object` | Tri-state verification results (`"pass"`, `"fail"`, or `"not_run"`) and detailed check outputs. |
| `limitations` | `array` | Non-empty array (`minItems: 1`) of explicit scientific limitations and bounds. |

---

## 3. How to Record a Run

1. Copy `run-template.json` into your experiment directory:
   ```bash
   cp examples/template/run-template.json path/to/my-experiment/evidence.json
   ```
2. Populate the environment, skill commit SHA, fixture commit SHA, executed commands, and actual exit codes.
3. Record the exact verification output produced by the fixture's `verify.py` script.
4. List genuine limitations (models tested, task domain, edge cases not evaluated).

---

## 4. Validating an Evidence Record

### Using Python (`jsonschema`)
```bash
python -c "
import json, jsonschema, pathlib
schema = json.loads(pathlib.Path('examples/template/evidence-record.schema.json').read_text())
instance = json.loads(pathlib.Path('path/to/evidence.json').read_text())
jsonschema.validate(instance=instance, schema=schema)
print('Evidence record schema validation passed.')
"
```

### Using PowerShell 7 (`Test-Json`)
```powershell
$schema = "examples\template\evidence-record.schema.json"
$valid = Test-Json -Path "path\to\evidence.json" -SchemaFile $schema
if ($valid) {
    Write-Host "Evidence record schema validation passed." -ForegroundColor Green
} else {
    Write-Error "Schema validation failed!"
}
```

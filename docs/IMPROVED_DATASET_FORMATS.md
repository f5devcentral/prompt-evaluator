# Dataset formats

JSONL is the recommended starting point for prompts with quotes, separators, newlines, or nested metadata. CSV and TSV work well with spreadsheet tools when fields are properly quoted. Parquet is available when its optional engine is installed. Legacy pipe format remains supported with an explicit hint when needed.

These are input-dataset choices, not a promise that every legacy conversion tool supports every direction or preserves every field. Evaluation result exports have their own [format guide](results-format-changes.md).

## JSONL

Store one JSON object per line:

```jsonl
{"prompt":"A harmless example","expected":false,"id":"example-1"}
{"prompt":"A reviewed detection example","expected":true,"metadata":{"source":"example"}}
```

JSON encoding safely represents tabs, newlines, and quotes inside a prompt. The current reader still collects records into memory; the format's ability to support streaming doesn't mean this application performs bounded-memory streaming.

## CSV and TSV

Include named `prompt` and `expected` columns. Quote values containing separators or newlines using a standard CSV writer.

```csv
prompt,expected
"A harmless example",false
"A prompt with a comma, and ""quotes""",true
```

A simple TSV file uses actual tab characters between fields:

```tsv
prompt	expected
A harmless example	false
A reviewed detection example	true
```

Don't insert an unquoted tab inside a TSV field; it creates another column. JSONL is simpler for complex prompts or metadata. Evaluators recognize common text/label aliases, but canonical column names avoid ambiguity.

## Parquet and legacy files

Install `requirements-parquet.txt` inside the project Conda environment for Parquet. Evaluation readers support Parquet input and result writers support Parquet output. Large files can still consume substantial memory.

For an old pipe-delimited file named `.csv`, tell the evaluator which format to read:

```bash
python prompt_evaluator.py --input legacy.csv --format-hint pipe --lines 10
```

This is a live scan after loading input. Confirm the configured environment before running it. Pipe parsing has limitations when prompt text itself contains pipes; prefer a reviewed conversion to JSONL for new work.

## Inspect locally

```bash
python validate_setup.py --dataset datasets/sample-datasets/pii_dataset.jsonl
python -m tools.enhanced_dataset_reader datasets/sample-datasets/pii_dataset.jsonl --max-lines 2
```

The standalone reader prints prompt samples; don't share its output without reviewing it. Its format option is `--format`, while evaluator input hints use `--format-hint`.

For Python callers, the reader returns `PromptRecord` objects, not dictionaries:

```python
from tools.enhanced_dataset_reader import EnhancedDatasetReader

records = EnhancedDatasetReader().read_dataset("dataset.jsonl", max_lines=20)
for record in records:
    print(record.id, record.expected)
```

`load_dataset_enhanced()` is the compatibility wrapper used by evaluators when dictionary records are needed.

## Conversion and migration

Use the working root-level converter for straightforward CSV/JSONL normalization:

```bash
python convert_dataset.py --input source.csv --output datasets/source_converted.jsonl
```

For other formats, use the Python examples in [dataset tools](../tools/README.md). The advanced converter's CLI currently passes its format arguments in the wrong order, so its normal conversion examples are not recommended. Its `--validate` option isn't a standalone one-file validation command. Use `validate_setup.py --dataset` for local evaluator-input checks.

The legacy migrator is a package module:

```bash
python -m tools.migrate_datasets --list
```

Listing only inspects direct `datasets/*.csv` files. It doesn't inventory nested JSONL samples. Migration assumes legacy pipe input, and `--all` only processes detected pipe files from that limited inventory. Backups are enabled by default, but existing backup files aren't refreshed automatically, and there is no rollback command. Read [migration precautions](../tools/README.md#legacy-migration) before making copies or conversions.

Always choose a different output path, keep source data, and inspect record counts, labels, and metadata afterward. Legacy CSV/TSV dataset conversion doesn't preserve nested metadata, even though current evaluation result exports serialize nested fields as JSON.

# Dataset tools

Run these examples from the repository root with the project Conda environment active. These tools prepare local input data; they don't call the guardrails API. Some warnings and demos print prompt content, so protect logs and use synthetic files when trying examples.

## Simple conversion

```bash
python convert_dataset.py --input source.csv --output datasets/source_converted.jsonl
python validate_setup.py --dataset datasets/source_converted.jsonl
```

The root converter accepts CSV/JSONL and writes JSONL by default. It can map malicious/benign `original_label` values when `expected` is missing. It isn't an interactive converter and doesn't preserve every arbitrary source column. Choose a distinct output path and keep originals.

## Advanced conversion in Python

The advanced converter CLI currently has a format-argument ordering bug. Use keyword arguments through its Python API instead of the old positional CLI examples:

```python
from tools.improved_dataset_converter import DatasetConverter

converter = DatasetConverter()
output = converter.convert_dataset(
    "source.tsv",
    "converted.jsonl",
    input_format="tsv",
    output_format="jsonl",
)
stats = converter.validate_dataset(output, format_hint="jsonl")
if not isinstance(stats, dict) or stats.get("error"):
    raise ValueError("Converted dataset needs review")
print(stats["total_records"])
```

Input support here is JSONL, CSV, TSV, and legacy pipe. Parquet is an export option for this converter, not an input branch. The separate enhanced reader and evaluators do read Parquet. Install the optional engine from `requirements-parquet.txt` when needed.

JSONL conversion can retain structured metadata. This older converter's CSV/TSV output projects a fixed set of columns and drops nested metadata; don't assume lossless conversion. It doesn't create backups, prevent same-path overwrites, or make validation errors impossible. These limitations are separate from the newer evaluation result writers.

## Read datasets

```python
from tools.enhanced_dataset_reader import EnhancedDatasetReader

records = EnhancedDatasetReader().read_dataset(
    "dataset.jsonl", max_lines=20
)
for record in records:
    print(record.id, record.expected)
```

The reader returns a list of `PromptRecord` objects; access attributes such as `.prompt`, `.expected`, and `.metadata`. Use `load_dataset_enhanced()` for dictionary records. CSV/TSV require headers. Use `format_hint="pipe"` for legacy pipe-delimited `.csv` input. JSONL supports complex text, but these readers aren't bounded-memory streaming iterators.

For local CLI inspection:

```bash
python -m tools.enhanced_dataset_reader dataset.jsonl --max-lines 2
```

It prints prompt samples. Evaluators use `--format-hint` to choose input format; this standalone reader uses `--format`.

## Legacy migration

```bash
python -m tools.migrate_datasets --list
python -m tools.migrate_datasets --help
```

Use module invocation because the migrator imports other tools relatively. Its inventory is limited to direct `datasets/*.csv` files. Batch migration skips those it doesn't detect as pipe-delimited; it doesn't recursively migrate every supported format.

If you choose to migrate a confirmed legacy pipe file, work on a copy, check its target filename, and retain a backup:

```bash
python -m tools.migrate_datasets --input legacy_copy.csv --output-format jsonl
```

Migration assumes pipe input and derives output by replacing the extension. Selecting the same extension can overwrite the source. Backups are enabled by default, but an existing backup isn't refreshed automatically. Validation returns statistics or errors and isn't a guarantee of a valid migration. There is no automatic rollback command; restore a verified backup manually when needed. Avoid `--no-backup` for data you need to retain.

## Demonstrations

The legacy demonstration programs write example files, and one offers interactive cleanup. Use a disposable copy of the project and synthetic data if exploring them:

```bash
python -m tools.demo_improved_formats
python -m tools.example_improved_formats
```

They're demonstrations, not a substitute for the curated tests or a guarantee that every legacy migration path works. For current application behavior, use [dataset guidance](../docs/datasets.md), [format guidance](../docs/IMPROVED_DATASET_FORMATS.md), and [offline tests](../docs/TESTING_GUIDE_SIMPLE.md).

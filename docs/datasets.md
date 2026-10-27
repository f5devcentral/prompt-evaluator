# Working with datasets

Use labeled examples that match the guardrails you want to evaluate. A dataset with a different labeling task can produce numbers that look valid but don't measure the detection you care about. Review licensing, label meaning, and sensitive content before sending any dataset to the API.

## Included examples

Examples are under `datasets/sample-datasets/`, not the top-level dataset CSV paths shown in older release notes:

- `pii_dataset.jsonl`: personal-information examples.
- `codesagar_malicious_llm_prompts_v4_test.jsonl`: prompt-injection examples.
- `fin_advice_dataset.jsonl`: financial-advice examples.
- `eu-ai-act-prompts.jsonl`: compliance-related examples.

Confirm your target environment and project, then start with a small sample:

```bash
python prompt_evaluator.py --input datasets/sample-datasets/pii_dataset.jsonl --lines 10
```

Add `--project your-project` to use a named project. This command sends prompts to the configured scan API; inspecting or converting a dataset locally does not.

## Create your own data

Use `prompt` for the text and `expected` for whether it should trigger a relevant guardrail. JSONL is recommended:

```jsonl
{"prompt":"A harmless example","expected":false,"id":"example-1"}
{"prompt":"A labeled detection example","expected":true,"id":"example-2","metadata":{"source":"example"}}
```

Replace illustrative text and labels with properly reviewed examples. Boolean true/false and established malicious/safe aliases are recognized by evaluators. Other labels are reported as invalid rather than silently treated as safe. CSV and TSV need header columns. Parquet needs the optional dependencies in [installation](installation.md).

For legacy pipe-delimited files with a `.csv` extension, specify `--format-hint pipe`. A `.csv` extension otherwise selects standard CSV. Readers load records into memory; JSONL doesn't make these evaluators stream indefinitely. Use `--lines` for scan tools or `--max-lines` for the LLM-response tool to limit a run.

## Download from Hugging Face

The downloader can inspect and download datasets from Hugging Face. These commands contact Hugging Face, not your configured guardrails tenant:

```bash
python download_hf_datasets.py --search "prompt injection" --limit 5
python download_hf_datasets.py --info "codesagar/malicious-llm-prompts-v4"
python download_hf_datasets.py --list-splits "codesagar/malicious-llm-prompts-v4"
```

Check the current dataset's split, configuration, and column names before downloading. For a dataset with the shown split and label column:

```bash
python download_hf_datasets.py --dataset "codesagar/malicious-llm-prompts-v4" --split test --label-column malicious --max-samples 20 --format json --output injection_examples.jsonl
```

The output directory defaults to `datasets/`. The format defaults to `json`, which writes JSONL. Choosing a filename does not choose the format: use `--format csv` when naming a CSV file.

Relevant options are `--dataset/-d`, `--config/-c`, `--split/-s`, `--max-samples/-m`, `--output/-o`, `--output-dir`, and `--format/-f`. Use `--text-column/-t` and `--label-column` to avoid relying on automatic column detection. `--label-columns` creates separate label-specific files and, for multiple valid columns, a combined file using OR logic. Review whether that combined meaning matches your guardrails.

`--no-label` marks every example true; it doesn't discover ground truth. Numeric-label conversion also doesn't establish whether a dataset's labels mean harmful/safe. Inspect the source labeling before interpreting accuracy. `--max-samples` limits the saved sample, but the downloader can load the full source dataset first.

## Convert CSV or JSONL

From the repository root, with the Conda environment active:

```bash
python convert_dataset.py --input source.csv --output datasets/source_converted.jsonl
python validate_setup.py --dataset datasets/source_converted.jsonl
```

Choose a separate output path and keep the original. The converter accepts CSV or JSONL and defaults to JSONL output. It reads an existing `expected` value or maps `original_label` values malicious/benign to true/false. CSV recognizes common text and label column names; it isn't an interactive positional-column converter.

This simple converter writes prompts, expected labels, and available JSONL metadata. It isn't a full-fidelity archive of every input column. Check skipped records and label meaning. Some legacy conversion tools can print prompt snippets in warnings, so keep conversion logs private when handling sensitive data.

For TSV, legacy migration, or advanced Python conversion, see [formats](IMPROVED_DATASET_FORMATS.md) and [tools](../tools/README.md). Those pages describe the existing converter CLI limitation and backup behavior. No migration is required for the API compatibility update.

## Save evaluation results

Evaluation output is different from dataset conversion output. To create a CSV result file, select its format explicitly:

```bash
python prompt_evaluator.py --input datasets/sample-datasets/pii_dataset.jsonl --lines 10 --results-format csv --output baseline.csv
```

The main file is `results/baseline.csv`; false-positive and false-negative filenames remain dataset-based. Results stay ignored by Git except for the empty directory placeholder. See [usage](usage.md) and [result formats](results-format-changes.md).

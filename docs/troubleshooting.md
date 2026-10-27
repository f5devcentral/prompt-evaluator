# Troubleshooting

Start with offline validation in the project Conda environment:

```bash
conda activate prompt-evaluator
python validate_setup.py
python validate_setup.py --dataset datasets/sample-datasets/pii_dataset.jsonl
```

## Configuration and authentication

Set `CALYPSOAI_URL` to the confirmed US1, EU1, or custom tenant origin and supply `CALYPSOAI_TOKEN` without embedding it in a URL. Explicit environment values override `.env`. Imports and `--help` don't need credentials.

`authentication_error` means HTTP 401; `permission_error` means 403. Don't log tokens or raw server bodies. After confirming the target tenant, `python validate_setup.py --check-api` reads the documented scanner-list operation. A permission-denied scanner listing isn't proof that the service or scan operation is unavailable. The validator no longer assumes an undocumented `/health` route.

## Input and output failures

Missing, unreadable, or wholly empty/malformed inputs fail before requests or output writes. Supported formats are JSONL, CSV, TSV, optional Parquet, and legacy pipe. Use `--format-hint pipe` for old pipe-delimited `.csv` files. Reader warnings identify skipped malformed source rows without printing prompt text; inspect the original locally.

Explicit output names must stay within `results/` and match the selected main format. Source/export collisions are rejected. Prompts main results still default to CSV; choose `--results-format json` for JSONL. Parquet needs an engine: install `requirements-parquet.txt` inside the activated Conda environment. It no longer silently falls back to a differently named JSONL file.

## Unexpected counts

Inspect attempted, evaluated, error, incomplete, and invalid counts together. `blocked` and `redacted` now count as detections under the documented binary policy. HTTP failures, typed scanner execution errors, and unknown outcomes aren't safe results.

A run with only exclusions can't estimate accuracy. Its output is retained and the CLI exits 2. Provider failures are tracked separately from detection metrics. Old results may lack enough scanner/provider evidence to establish execution completeness.

Recompute results without spending more API requests:

```bash
python evaluate_existing_results.py -i results/pii_dataset_results.jsonl
python report_generator.py --input results/pii_dataset_results.jsonl
```

Reports now recompute FP/FN examples from main results instead of trusting possibly stale export files. A standalone PDF and online evaluation should agree on evaluated counts and denominators for the same evidence.

## Timeouts, rate limits, and concurrency

`timeout`, `connection_error`, `rate_limit` (429), and `server_error` are recorded as safe categories. Use finite positive `--timeout` or `CALYPSOAI_TIMEOUT`. Requests are not automatically replayed because scans/provider calls can have side effects.

Get infrastructure approval before adjusting concurrency. Start with a small synthetic dataset, low concurrency, and an appropriate `--rate-limit`. A high attempt-throughput number isn't evidence of successful evaluation if exclusions also rise. Queue wait is separate from API latency.

## Report failures

Sequential and prompts flows warn if PDF generation fails; main results remain available. Concurrent flows require manual generation. Use `--dataset` with the dataset name, not a path, or use `--input` for custom filenames. PDFs and raw result files can contain PII; review them before sharing.

## Development tests

`make test-core` runs the curated offline suites including contracts. `make test-contract` runs contract/workflow checks with scoped coverage. Don't substitute `make test-concurrent`: it invokes the live evaluator. The broader legacy reader/migration suite has separately reproducible baseline failures; see [testing](TESTING_GUIDE_SIMPLE.md).

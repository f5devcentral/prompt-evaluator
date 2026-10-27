# Usage

## Choose the operation

`prompt_evaluator.py` sends sequential `/scans` requests. `prompt_evaluator_concurrent.py` sends the same operation through a thread pool. Both explicitly use `flagOnly=true`, preserving the API's detection-oriented default.

`prompt_evaluator_prompts.py` sends `/prompts` requests through the selected provider. Its aggregate outcome may include request and response guardrails. Don't treat it as isolated input-scanner accuracy.

Both workflows support the latest CalypsoAI API. Your existing tenant credentials still apply; responses are returned directly rather than requiring you to poll a background job.

## Common controls

All three tools accept `--input/-i`, `--project`, `--timeout`, `--verbose`, `--diagnostics`, `--format-hint`, `--output/-o`, `--results-format/-r`, and `--format/-f`.

`--project` accepts a project name or ID. Omission uses global configuration. `--timeout` overrides `CALYPSOAI_TIMEOUT` and the 30-second default. `--verbose` requests per-guardrail details and is already enabled in prompts mode. `--diagnostics` additionally retains content-rich scanner/configuration details and redacted input when returned; don't enable it without an artifact-handling policy.

`--format-hint` accepts `jsonl`, `csv`, `tsv`, `pipe`, or `parquet`. Use `pipe` explicitly for old pipe-delimited files with a `.csv` extension. Inputs should have a string `prompt` and binary `expected` value. JSON booleans and existing true/false or malicious/safe aliases are normalized consistently. Unknown labels are explicit invalid exclusions. Reader warnings about skipped malformed source lines are separate from API attempt counts.

Sequential and concurrent scans limit rows with `--lines/-l`. Prompts uses `--max-lines/-m`. Limits, concurrency, rates, and timeouts must be positive. Missing, unreadable, or wholly empty/malformed input fails before requests or result writes.

## Sequential scan examples

Confirm the tenant and project before running these live examples:

```bash
python prompt_evaluator.py -i datasets/sample-datasets/pii_dataset.jsonl -l 10 --project evaluation-project
python prompt_evaluator.py -i datasets/sample-datasets/pii_dataset.jsonl -l 10 --project evaluation-project --verbose --timeout 45
python prompt_evaluator.py -i datasets/sample-datasets/pii_dataset.jsonl -l 10 --results-format csv --output baseline.csv
```

## Prompt pipeline examples

Only prompts mode accepts `--provider`, as a configured provider name or ID. Omission uses the project's default provider.

```bash
python prompt_evaluator_prompts.py -i datasets/sample-datasets/pii_dataset.jsonl -m 10 --project evaluation-project --provider evaluation-provider
python prompt_evaluator_prompts.py -i datasets/sample-datasets/pii_dataset.jsonl -m 10 --results-format json --output pipeline.jsonl
```

The historical prompts main-output default remains CSV; `--results-format json` requests JSONL. LLM responses remain part of prompts output, including nullable responses when the contract permits them.

## Concurrent scans

```bash
python prompt_evaluator_concurrent.py -i datasets/sample-datasets/pii_dataset.jsonl -l 10 -c 2 --rate-limit 2 --project evaluation-project --timeout 30
```

The tool still asks for interactive confirmation. Get infrastructure approval before shared-environment load tests. Each thread has its own session, every request has a timeout, and POSTs aren't automatically replayed. See [concurrency](CONCURRENT_EVALUATION.md).

## Output controls

Main formats are `json` (writes JSONL), `csv`, `tsv`, and `parquet`. `--format` independently selects FP/FN export format and defaults to JSONL. Parquet needs `requirements-parquet.txt`.

Default main filenames are `results/{dataset}_results.jsonl` for sequential scans, `results/{dataset}_results.csv` for prompts, and `results/{dataset}_concurrent_results.jsonl` for concurrent scans. FP/FN exports use `{dataset}_false_positives` / `{dataset}_false_negatives`; concurrent names include `_concurrent` before that suffix.

An explicit `--output custom.csv` is honored within `results/`, including subdirectories, and must match `--results-format`. Paths outside `results/` and names colliding with source inputs or FP/FN exports are rejected before requests. FP/FN names remain dataset-derived even when the main output is custom. Archive existing runs before intentionally reusing their names.

Successful complete evaluation exits 0. Configuration/input/output failures during execution exit 1. A completed run with excluded request-error, incomplete, or invalid rows exits 2 after retaining results. Invalid CLI syntax also uses argparse's standard exit status 2. Provider failures are reported separately and don't, by themselves, change a usable detection into an exclusion.

## Reanalysis and PDFs

```bash
python evaluate_existing_results.py -i results/pii_dataset_results.jsonl
python report_generator.py --dataset pii_dataset
python report_generator.py --dataset pii_dataset_concurrent
python report_generator.py --input results/pipeline.jsonl --output results/pipeline_report.pdf
```

Reanalysis and reporting are offline. Use `--dataset` for default names or `--input` for an explicit/custom main result file. Reports recompute metrics and examples from that file rather than trusting stale export sidecars.

Sequential scan and prompt flows automatically generate PDFs when report dependencies are available. Concurrent evaluation doesn't; generate it manually. See [scoring policy](evaluation-metrics.md), [result compatibility](results-format-changes.md), and [report details](pdf-reports.md).

## Protect artifacts

Inputs, original-line provenance, metadata, LLM responses, and PDF examples can contain PII. Defaults aren't PII-free. Error categories omit arbitrary server bodies and exception messages, but `--diagnostics` expands retained content. Limit access and retention, and review artifacts before sharing. Dataset metadata isn't automatically uploaded to the API.

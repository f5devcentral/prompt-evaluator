# prompt-evaluator

Test how well your configured CalypsoAI guardrails detect content in labeled datasets. Review accuracy, false positives, false negatives, and response times, then save the results or generate a PDF report.

The latest update aligns the scan and prompt evaluation workflows with the current CalypsoAI API, adds project/provider selection, and makes scoring and reporting more consistent. See [what's changed](CHANGES_SUMMARY.md).

## Get started

Use Python 3.11 or newer. If you already have a project Conda environment, activate it and skip the creation command.

```bash
conda create -n prompt-evaluator python=3.11
conda activate prompt-evaluator
python -m pip install -r requirements.txt
python validate_setup.py
```

The setup check is offline and doesn't need API credentials. Optional Parquet support and development dependencies are covered in the [installation guide](docs/installation.md).

Create a `.env` file in the project root:

```dotenv
CALYPSOAI_URL=https://us1.calypsoai.app
CALYPSOAI_TOKEN=your_api_token_here
```

Use `https://eu1.calypsoai.app` for EU1 or your organization's tenant address. Existing environment variables take precedence over `.env`. Don't commit your token.

Confirm the target environment and relevant guardrails before sending data. Run a small sample with the scan-only evaluator:

```bash
python prompt_evaluator.py \
  --input datasets/sample-datasets/pii_dataset.jsonl \
  --lines 10
```

This sends up to ten prompts to the scan API using the global project configuration. Add `--project your-project` to select a project by name or ID. Use guardrails that match the dataset's labels; unrelated guardrails can change the overall decision.

Results and an automatically generated PDF go into `results/`. The [quick reference](docs/CHEAT_SHEET.md) covers the most common commands.

## Choose how to evaluate

Use `prompt_evaluator.py` for sequential scan-only evaluation. It's the simplest starting point for checking detection results.

Use `prompt_evaluator_prompts.py` when you also need an LLM response. Select a configured provider with `--provider`, or use the selected project's default:

```bash
python prompt_evaluator_prompts.py \
  --input datasets/sample-datasets/pii_dataset.jsonl \
  --max-lines 10 \
  --project your-project \
  --provider your-provider \
  --results-format json \
  --output provider_results.jsonl
```

Replace the example project/provider names with your configuration. These results can include guardrails on both the input and the LLM response, so they aren't a measure of one isolated input scanner's accuracy.

Use `prompt_evaluator_concurrent.py` for parallel scan requests after confirming approval for the additional load. Start conservatively:

```bash
python prompt_evaluator_concurrent.py \
  --input datasets/sample-datasets/pii_dataset.jsonl \
  --lines 10 \
  --concurrency 2 \
  --rate-limit 2
```

Concurrent mode asks for confirmation before proceeding. It doesn't guarantee a particular speedup. See [concurrent evaluation](docs/CONCURRENT_EVALUATION.md) and [comparing execution modes](docs/SEQUENTIAL_VS_CONCURRENT.md).

## Read the results

A `flagged`, `blocked`, or `redacted` outcome counts as a detection when compared with the dataset label. A `cleared` outcome counts as no detection. Raw outcomes are preserved in saved results.

Accuracy is calculated only from records that could be evaluated. Request errors, incomplete guardrail results, and invalid rows are counted separately. Always check attempted and evaluated totals alongside accuracy; a run with no evaluated rows can't estimate detection accuracy. Provider failures are reported separately.

The decisions reflect all relevant guardrails in the selected configuration. Use an isolated project if you want to measure a specific guardrail. See the [metrics guide](docs/evaluation-metrics.md).

## Save and revisit your work

All three evaluators can save main results and misclassification exports as JSONL, CSV, TSV, or optional Parquet. Use `json` as the CLI format value for JSONL files.

Scan tools default to `{dataset}_results.jsonl`, with `_concurrent` added for concurrent runs. The LLM-response evaluator defaults to `{dataset}_results.csv`. False-positive and false-negative exports default to JSONL in every mode.

`--results-format` controls the main file; `--format` controls the misclassification exports. `--output` chooses a main filename inside `results/`. For example:

```bash
python prompt_evaluator.py \
  --input datasets/sample-datasets/pii_dataset.jsonl \
  --lines 10 \
  --results-format csv \
  --output baseline.csv
```

Custom main filenames don't rename the dataset-based false-positive/false-negative exports. Input/output conflicts are rejected, but reusing an ordinary output name replaces that file. Archive runs you need to retain.

Reanalyze or report on a saved file without another API call:

```bash
python evaluate_existing_results.py --input results/baseline.csv
python report_generator.py --input results/baseline.csv
```

Sequential scans and LLM-response evaluations generate PDFs automatically. Concurrent results need manual reporting. Historical supported result files remain readable, although missing old scanner details can't be recovered. See [result formats](docs/results-format-changes.md) and [PDF reports](docs/pdf-reports.md).

## Protect sensitive data

Input prompts, metadata, LLM responses, and PDF examples can contain personal or confidential information. Results aren't automatically safe to share. Restrict access, set appropriate retention, and review content before sharing it.

`--verbose` requests scanner details and is already enabled in LLM-response mode. `--diagnostics` additionally saves content-rich troubleshooting information. Enable it only when needed. Tokens and arbitrary server error bodies aren't logged.

Generated content under `results/` is ignored by Git, except for an empty `.gitkeep` placeholder. Keep `.env` excluded too. Ignoring files isn't a substitute for securing them locally.

## More documentation

Start with the [documentation index](docs/README.md) for installation, usage, datasets, reporting, and troubleshooting. [What's changed](CHANGES_SUMMARY.md) explains this update in user terms; the [changelog](CHANGELOG.md) tracks development changes.

For development, install `requirements-test.txt` inside the project environment and run the offline checks:

```bash
python -m pip install -r requirements-test.txt
make test-core
python test_ci_features.py
python test_concurrent_basic.py
```

Optional Parquet tests need `requirements-parquet.txt`. See the [testing guide](docs/TESTING_GUIDE_SIMPLE.md) and [contributing guide](docs/contributing.md) for CI details and known limitations. `make test-concurrent` is a live evaluation, not an offline unit test.

## License

Licensed under [Apache License 2.0](LICENSE).

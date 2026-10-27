# Result formats and compatibility

The API compatibility update preserves raw overall outcomes and existing scalar result fields while using shared readers/writers and scoring across all entry points. Historical files remain readable without rescanning or a required migration.

## Defaults and names

Sequential scans default to `results/{dataset}_results.jsonl`; prompts retain the historical `{dataset}_results.csv` default. Concurrent scans default to `{dataset}_concurrent_results.jsonl`. All FP/FN exports default to JSONL; concurrent export names include `_concurrent`.

`--results-format` selects the main format; `--format` selects FP/FN format. Choices are `json` (JSONL), `csv`, `tsv`, and optional `parquet`. `--output` is honored within `results/` and must match the selected format. It doesn't rename dataset-derived FP/FN exports. Preflight rejects source/export collisions, invalid paths, failed input loads, and wholly empty/malformed input before requests or writes. Reusing ordinary existing output names still intentionally replaces that run, so archive data you need to retain.

## Retained fields

Existing `prompt`, `expected`, `outcome`, `response_time`, `prompt_size`, and `original_line` remain available. Dataset `id`, `metadata`, and `timestamp` are retained. When returned, new rows also retain request IDs, safe scanner identities/outcomes/directions/version metadata, status/error category, selected project/provider, evaluation mode, and provider status/timestamps.

Nullable or absent recording IDs, scanner names/IDs, and LLM responses are valid. Prompts mode continues to include LLM response text. Additional scanner message/data detail, redacted input, and scanner configuration detail require `--diagnostics`. Dataset metadata is not automatically uploaded as `externalMetadata`.

Concurrent rows add `queue_time_ms`, `request_time_ms`, `total_time_ms`, actual `worker_id`, and `request_timestamp`. Request timestamp records start time; the dataset's original timestamp is preserved separately.

## Encoding and legacy files

JSONL stores nested structures directly. CSV/TSV quote separators, quotes, Unicode, and newlines using the standard CSV writer. Nested fields use JSON strings rather than Python repr. Tabular scalar values may be strings and optional scalars may be blank. Parquet stores labels as strings so mixed boolean/invalid labels remain available for explicit exclusion counts. A Parquet engine is an explicit optional dependency; no silent JSONL fallback occurs.

Historical Python-repr `scanner_results` cells remain opaque. They are never passed to `eval` or a Python-expression parser. Aggregate outcomes can still be scored, but embedded historical scanner errors can't be reliably reconstructed. `scanner_evidence_unavailable_count` discloses opaque cells. Missing old scanner/provider evidence doesn't establish successful execution.

Malformed JSONL result lines are counted as invalid rather than silently discarded. Four-outcome scoring and explicit exclusions can change historical metric totals compared with older tools; no raw outcome is rewritten. Old FP/FN files may therefore be stale. Reports derive examples from main results and don't trust those sidecars.

## Recompute offline

```bash
python evaluate_existing_results.py -i results/pii_dataset_results.jsonl
python report_generator.py --input results/pii_dataset_results.jsonl
```

These don't consume API credentials or rescan inputs. All formats share the same evaluated denominator and FP/FN membership when equivalent structured evidence is present. Opaque legacy representations are the documented exception for reconstructing scanner completeness.

## Protect output

Prompts, original-line provenance, metadata, provider responses, and PDF examples may contain PII even without diagnostics. Error records store safe categories rather than arbitrary exception or server bodies, but default artifacts are not PII-free. Restrict access and retention, and review/redact content before sharing.

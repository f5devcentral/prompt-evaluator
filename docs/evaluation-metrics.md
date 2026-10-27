# Evaluation metrics

## Detection policy

Keep raw API outcomes unchanged for auditability. For binary scoring, `flagged`, `blocked`, and `redacted` are positive detections; `cleared` is a negative detection. This is the evaluator's policy for comparing against a binary dataset label, not an assertion about provider delivery or whether enforcement was correct.

The API supports all four overall outcomes. Scan-only evaluations keep their detection-oriented behavior: a triggered guardrail is counted as a detection regardless of whether its configured action would block, flag, or redact the content.

A malicious/true label with a positive detection is TP; a safe/false label with `cleared` is TN. A safe label with a positive detection is FP; a malicious label with `cleared` is FN. JSON booleans and established true/false, malicious/safe aliases are normalized consistently across evaluators, exports, reanalysis, and reports.

## Denominators and exclusions

`total` and `evaluated_count` are TP + TN + FP + FN, never all attempted rows. `attempted_count` is the number of result rows. Every row is either evaluated or belongs to one mutually exclusive exclusion category:

* `error_count`: failed request/processing rows, including historical `error: ...` outcomes.
* `incomplete_count`: guardrail execution errors indicated by typed `data.type=error`, or an explicit incomplete status.
* `invalid_count`: unrecognized outcomes, labels, or malformed saved records.

`excluded_count` is their sum, and attempted = evaluated + excluded. Always compare coverage with accuracy. An all-error run isn't a successful zero-accuracy evaluation; displayed zero rates with no evaluated samples are placeholders.

A single scanner's `passed`/`failed` value isn't an overall detection outcome. In particular, a failed guardrail execution must not be counted as a successful detection. `provider_error_count` separately reports non-success provider statuses inside successful API envelopes. It doesn't erase otherwise usable guardrail evidence or imply a detection. For old rows without provider metadata, that count is unavailable rather than evidence of provider success.

Malformed source lines skipped by the dataset reader produce warnings before evaluation; they're not API attempts. Malformed JSONL result lines, by contrast, are counted as invalid result rows during reanalysis.

## Formulas

Accuracy = (TP + TN) / evaluated.

Precision = TP / (TP + FP). Recall = TP / (TP + FN).

F1 = 2 * precision * recall / (precision + recall).

FPR = FP / (FP + TN). FNR = FN / (FN + TP).

The main tools display zero for undefined rates; comparative charts retain their existing N/A convention for undefined precision/FPR. Don't interpret an undefined rate as measured performance. Class balance and dataset relevance matter more than arbitrary universal accuracy thresholds.

## Evaluation scope

Top-level outcomes summarize configured guardrails, not an isolated named scanner. `/prompts` also runs a provider and can include response-direction guardrails; the input label alone doesn't establish which guardrail caused its aggregate outcome. Use an isolated project and appropriate datasets before attributing results to a scanner. Per-scanner accuracy and attribution are not added by this compatibility update.

Scanner IDs, names, version metadata, recording IDs, and LLM responses may be absent or null. An empty scanner list doesn't establish which guardrails ran. Historical Python-repr scanner cells aren't evaluated as code. `scanner_evidence_unavailable_count` identifies opaque cells; scoring can use their aggregate outcome, but historical scanner-error completeness can't be recovered from them. Missing legacy evidence isn't a clean bill of health.

## Timing

Saved `response_time` is in seconds. CLI summaries show milliseconds and percentiles p50/p95/p99. Sequential, concurrent, and report summaries use evaluable rows for latency so failures don't appear as zero-latency successes. Provider failures can still have usable guardrail request timings and are separately reported.

Attempt throughput is all completed attempts divided by measured wall time, not successful detections per second. Standalone reports can't reconstruct sequential wall time from isolated request durations and therefore omit throughput when it isn't available.

Concurrent `queue_time_ms` starts before executor submission; `request_time_ms` measures the API call, and `total_time_ms` includes waiting and local processing. `worker_id` identifies the actual worker-local session. `request_timestamp` records request start; an input `timestamp` retains its original provenance. Small samples produce unstable percentile estimates, and concurrency doesn't guarantee any particular speedup.

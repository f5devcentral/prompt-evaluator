# Concurrent evaluation

Concurrent evaluation sends multiple scan requests at once. It uses the same detection scoring and error handling as sequential evaluation; parallel execution changes scheduling, not what counts as a detection.

## Confirm the target first

Coordinate with the infrastructure owner before running against shared services. Confirm the tenant, isolated project, synthetic dataset, concurrency, rate, and test window. The CLI retains its interactive confirmation. No advertised worker count is universally safe.

```bash
conda activate prompt-evaluator
python prompt_evaluator_concurrent.py -i datasets/sample-datasets/pii_dataset.jsonl -l 10 -c 2 --rate-limit 2 --project evaluation-project --timeout 30
```

`--concurrency/-c` defaults to 10 and must be a positive integer. Optional `--rate-limit` spaces submissions and must be finite and positive. `--timeout` or `CALYPSOAI_TIMEOUT` bounds request operations; queueing can make end-to-end time longer. No automatic POST retries are configured.

Common project, format, output, verbose, and diagnostics controls are documented in [usage](usage.md). Provider selection belongs only to `/prompts`, not this scan-only tool.

## Timing and sessions

`queue_time_ms` measures the actual wait for a worker. `request_time_ms` measures the API call when it completes successfully. `total_time_ms` includes queue wait and local processing. `request_timestamp` records request start. Dataset `id`, `metadata`, and original `timestamp` are preserved.

`worker_id` identifies the actual worker-local session. Sessions are closed when the executor completes. Results may be saved in completion order, so use the preserved dataset ID rather than line order to match inputs.

Latency and queue/total summaries use the same evaluable population as sequential/PDF summaries. Attempt throughput includes all completed attempts divided by wall time. Always inspect error, incomplete, invalid, and provider-failure counts; throughput alone isn't successful work per second.

## Outputs

Defaults are `results/{dataset}_concurrent_results.jsonl`, `{dataset}_concurrent_false_positives.jsonl`, and `{dataset}_concurrent_false_negatives.jsonl`. `--results-format` controls main results; `--format` controls FP/FN exports. `--output` changes only the main filename and must stay within `results/`; source/export collisions are rejected before requests.

Concurrent evaluation doesn't generate a PDF automatically:

```bash
python report_generator.py --dataset pii_dataset_concurrent
python report_generator.py --input results/custom.jsonl
```

Archive outputs before intentionally reusing names. Result content, metadata, and PDF examples may contain PII; detailed scanner messages/configuration require explicit `--diagnostics`.

## Offline tests versus load tests

```bash
make test-contract
python test_concurrent_basic.py
```

The contract suite covers timeouts, out-of-order completion, queue wait, worker identity, shared metric membership, and result formats using synthetic transport. It doesn't contact a tenant.

`make test-concurrent` and `make run-concurrent` invoke live evaluation and aren't offline checks. Compare sequential and concurrent results using the same dataset, project configuration, and verbosity; don't expect a fixed speedup or attribute a single latency increase to a particular server cause without evidence.

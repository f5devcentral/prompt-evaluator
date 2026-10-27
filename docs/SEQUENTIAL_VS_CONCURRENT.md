# Sequential and concurrent evaluation

Use sequential scans to establish a low-load baseline. Use concurrent scans only after infrastructure approval when you need to measure scheduling and load effects. Both call `/scans` with `flagOnly=true` and share outcome normalization, explicit exclusions, and result serialization.

Keep the tenant, dataset, project, guardrail configuration, verbosity, and diagnostic settings the same. These are live examples:

```bash
python prompt_evaluator.py -i datasets/sample-datasets/pii_dataset.jsonl -l 10 --project evaluation-project
python prompt_evaluator_concurrent.py -i datasets/sample-datasets/pii_dataset.jsonl -l 10 --project evaluation-project -c 2 --rate-limit 2
```

Both report detection accuracy on evaluable rows and request-latency percentiles from the same population. Concurrent mode adds actual executor queue wait, worker-session identity, and end-to-end timing. Attempt throughput includes failed attempts; compare coverage alongside speed.

Concurrency doesn't guarantee a speedup, and changed latency alone doesn't establish an API bottleneck or overload root cause. Compare multiple controlled samples and retain configuration provenance. Don't compare `/prompts` provider-pipeline latency with `/scans` and attribute the difference solely to scheduling.

Default main output is JSONL in both scan tools, with `_concurrent_results` distinguishing the concurrent run. Sequential scans generate PDFs automatically; concurrent results need manual reporting:

```bash
python report_generator.py --dataset pii_dataset
python report_generator.py --dataset pii_dataset_concurrent
```

See [concurrent controls](CONCURRENT_EVALUATION.md), [metric definitions](evaluation-metrics.md), and [usage](usage.md).

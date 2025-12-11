# Concurrent Prompt Evaluation

## Overview

The concurrent prompt evaluator (`prompt_evaluator_concurrent.py`) simulates real-world multi-user scenarios by sending multiple API requests in parallel. This provides insights into:

- **API performance under load**: How response times change with concurrent requests
- **Throughput metrics**: Requests per second your API can handle
- **Latency distributions**: p50, p95, p99 percentiles for response times
- **Rate limiting behavior**: Identify throttling thresholds
- **Queue time analysis**: Time waiting for available workers

## ⚠️ Important: Infrastructure Impact Warning

**Running the concurrent evaluator can trigger infrastructure auto-scaling and may impact shared resources.** Before using this tool in any environment, especially non-local development:

1. **Check with your platform/infrastructure team** to:
   - Understand auto-scaling policies
   - Determine safe concurrency levels for your environment
   - Schedule the test during maintenance windows if necessary
   - Get approval for load testing

2. **Start conservatively**:
   - Begin with `--concurrency 5` or lower
   - Use `--lines` to limit dataset size
   - Monitor infrastructure metrics during the run

3. **Use rate limiting** to smooth load:
   ```bash
   --rate-limit 20  # Maximum 20 requests per second
   ```

4. **Avoid peak hours** when running high concurrency tests

**Not following these guidelines could cause:
- Unexpected cloud infrastructure costs
- Service disruptions to other teams or applications
- Cascading failures if auto-scaling can't keep up**

## Quick Start

### Basic Usage

```bash
# Run with 10 concurrent workers (default)
python prompt_evaluator_concurrent.py -i datasets/combined_dataset.jsonl

# Run with 20 concurrent workers
python prompt_evaluator_concurrent.py -i datasets/combined_dataset.jsonl --concurrency 20

# Run with rate limiting (50 requests/sec)
python prompt_evaluator_concurrent.py -i datasets/combined_dataset.jsonl --rate-limit 50

# Test with small dataset
python prompt_evaluator_concurrent.py -i datasets/combined_dataset.jsonl -l 50 -c 5
```

### Using Makefile

```bash
# Run concurrent evaluation
make run-concurrent DATASET=datasets/combined_dataset.jsonl

# With custom settings
make run-concurrent DATASET=datasets/combined_dataset.jsonl CONCURRENCY=20 LINES=100

# Quick test
make test-concurrent
```

## How It Works

### Architecture

The concurrent evaluator uses Python's `ThreadPoolExecutor` to manage a pool of worker threads that send API requests in parallel:

```
┌─────────────────────────────────────────────────────────┐
│                    Load Dataset                          │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│          ConcurrentScanPromptsNode                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐              │
│  │ Worker 1 │  │ Worker 2 │  │ Worker N │              │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘              │
│       │             │              │                     │
│       └─────────────┴──────────────┘                     │
│              Shared Result Pool                          │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│     Calculate Metrics & Generate Reports                │
└─────────────────────────────────────────────────────────┘
```

### Key Components

#### ConcurrentScanPromptsNode
- **Thread Pool**: Configurable number of concurrent workers
- **Connection Pooling**: Reuses HTTP connections for efficiency
- **Thread-Safe Progress Tracking**: Lock-protected counters
- **Enhanced Timing**: Tracks queue time, request time, and total time

#### ConcurrentMetricsNode
Calculates performance metrics:
- **Throughput**: Total prompts processed per second
- **Latency Percentiles**: p50 (median), p95, p99
- **Queue Statistics**: Time waiting for available worker
- **Request Distribution**: How work is spread across workers

## Output Format

### Enhanced Results Fields

Concurrent evaluation adds these fields to each result:

| Field | Description |
|-------|-------------|
| `queue_time_ms` | Time waiting for an available worker (milliseconds) |
| `request_time_ms` | Actual API call duration (milliseconds) |
| `total_time_ms` | Queue time + request time (milliseconds) |
| `worker_id` | Which worker processed this request (0 to N-1) |
| `timestamp` | ISO 8601 timestamp when request was sent |

### Files Created

All output files include `_concurrent` suffix to distinguish from sequential runs:

```
results/
├── dataset_concurrent_results.jsonl
├── dataset_concurrent_false_positives.jsonl
└── dataset_concurrent_false_negatives.jsonl
```

## Performance Metrics

### Example Output

```
Concurrent Performance Metrics:
==============================

Configuration:
--------------
Concurrent Workers: 10
Rate Limit: None requests/sec
Total Prompts: 100
Total Elapsed Time: 15.32 seconds

Throughput:
-----------
Overall: 6.53 prompts/sec

Request Latency (API call time):
--------------------------------
Average: 245.12 ms
Minimum: 89.34 ms
Maximum: 1523.45 ms
p50 (median): 221.67 ms
p95: 456.78 ms
p99: 1234.56 ms

Queue Time (waiting for worker):
--------------------------------
Average: 12.34 ms
Maximum: 45.67 ms

Total Time (queue + request):
-----------------------------
Average: 257.46 ms
```

## Use Cases

### 1. Load Testing

Determine how many concurrent requests your API can handle:

```bash
# Start with low concurrency
python prompt_evaluator_concurrent.py -i datasets/test.jsonl -c 5

# Gradually increase
python prompt_evaluator_concurrent.py -i datasets/test.jsonl -c 10
python prompt_evaluator_concurrent.py -i datasets/test.jsonl -c 20
python prompt_evaluator_concurrent.py -i datasets/test.jsonl -c 50
```

Watch for:
- **Increasing latency**: p95/p99 times grow significantly
- **Error rates**: API starts returning errors
- **Throughput plateau**: Adding workers doesn't improve throughput

### 2. Comparing Sequential vs Concurrent

Run the same dataset with both evaluators:

```bash
# Sequential baseline
python prompt_evaluator.py -i datasets/test.jsonl

# Concurrent with 10 workers
python prompt_evaluator_concurrent.py -i datasets/test.jsonl -c 10
```

Compare:
- Total execution time
- Average latency (should be similar if API is not overloaded)
- Throughput improvement

### 3. Finding Rate Limits

Identify API rate limiting thresholds:

```bash
# Without rate limiting
python prompt_evaluator_concurrent.py -i datasets/test.jsonl -c 20

# With rate limiting
python prompt_evaluator_concurrent.py -i datasets/test.jsonl -c 20 --rate-limit 50
```

If the unlimited version shows errors or throttling, use `--rate-limit` to stay within API limits.

### 4. Realistic Production Simulation

Simulate your production traffic patterns:

```bash
# Example: API receives ~100 requests/sec from ~50 concurrent users
python prompt_evaluator_concurrent.py -i datasets/large_dataset.jsonl \
  --concurrency 50 \
  --rate-limit 100
```

## Best Practices

### Coordinate with Infrastructure Teams
**Before running concurrent evaluation against shared environments:**
- Notify your platform/infrastructure team
- Get explicit approval for the load test
- Provide concurrency levels and duration
- Confirm no scheduled maintenance or production deployments

This prevents unexpected service disruptions and cost overruns.

### Start Small
Begin with low concurrency and small datasets:
```bash
python prompt_evaluator_concurrent.py -i datasets/test.jsonl -l 20 -c 5
```

### Monitor Resource Usage
- Watch CPU usage (threading overhead)
- Monitor network connections
- Check memory consumption with large datasets

### Respect API Limits
- Use `--rate-limit` to avoid overwhelming the API
- Start with conservative concurrency levels
- Gradually increase to find optimal settings

### Analyze Results
1. **Check for errors**: Review results for failed requests
2. **Look at latency trends**: Compare p50 vs p95 vs p99
3. **Watch queue times**: High queue time indicates worker bottleneck
4. **Compare with sequential**: Ensure accuracy metrics match

## Configuration Options

### Command-Line Arguments

| Argument | Short | Default | Description |
|----------|-------|---------|-------------|
| `--input` | `-i` | Required | Input dataset file |
| `--lines` | `-l` | None | Limit number of prompts to process |
| `--concurrency` | `-c` | 10 | Number of concurrent workers |
| `--rate-limit` | | None | Maximum requests per second |
| `--format` | `-f` | json | Output format for FP/FN files |
| `--results-format` | `-r` | json | Output format for main results |

### Choosing Concurrency Level

**Guidelines:**
- **5-10 workers**: Safe starting point, good for testing
- **10-20 workers**: Typical production simulation
- **20-50 workers**: Heavy load testing
- **50+ workers**: Stress testing (monitor closely)

**Factors to consider:**
- API rate limits
- Available CPU cores
- Network bandwidth
- Dataset size

### Rate Limiting

Use `--rate-limit` to control request frequency:

```bash
# 50 requests per second maximum
python prompt_evaluator_concurrent.py -i dataset.jsonl --rate-limit 50
```

**When to use:**
- API has documented rate limits
- Testing specific throughput levels
- Avoiding overwhelming shared infrastructure

## Troubleshooting

### High Error Rates
**Symptoms**: Many results show `"outcome": "error: ..."`

**Solutions:**
- Reduce concurrency: `--concurrency 5`
- Add rate limiting: `--rate-limit 20`
- Check API credentials and network connectivity

### Queue Times Very High
**Symptoms**: `queue_time_ms` >> `request_time_ms`

**Solutions:**
- Workers are waiting for each other (good!)
- Consider increasing concurrency if API can handle it
- This indicates workers are kept busy

### Throughput Not Improving
**Symptoms**: Adding workers doesn't increase prompts/sec

**Solutions:**
- API may have rate limiting
- Network bottleneck
- Try rate limiting to smooth out traffic

### Memory Issues
**Symptoms**: Script crashes or slows down significantly

**Solutions:**
- Process smaller chunks: `--lines 100`
- Reduce concurrency
- Use JSONL format for streaming (less memory)

## Advanced Usage

### Batch Testing Different Configurations

Create a shell script to test multiple configurations:

```bash
#!/bin/bash
DATASET="datasets/test_dataset.jsonl"

for concurrency in 5 10 20 50; do
    echo "Testing with concurrency=$concurrency"
    python prompt_evaluator_concurrent.py \
        -i "$DATASET" \
        -c $concurrency \
        -l 100
done
```

### Analyzing Results Programmatically

```python
import json

# Load concurrent results
with open('results/dataset_concurrent_results.jsonl') as f:
    results = [json.loads(line) for line in f]

# Analyze latency by worker
worker_latencies = {}
for result in results:
    worker_id = result['worker_id']
    if worker_id not in worker_latencies:
        worker_latencies[worker_id] = []
    worker_latencies[worker_id].append(result['request_time_ms'])

# Print average latency per worker
for worker_id, latencies in sorted(worker_latencies.items()):
    avg = sum(latencies) / len(latencies)
    print(f"Worker {worker_id}: {avg:.2f}ms average")
```

## Comparison with Sequential Evaluator

| Feature | Sequential | Concurrent |
|---------|-----------|-----------|
| Processing | One at a time | Parallel workers |
| Speed | Baseline | 5-10x faster (typical) |
| Metrics | Basic latency | Enhanced timing & throughput |
| Use Case | Baseline accuracy | Load testing, performance |
| API Load | Minimal | Simulates production |
| Complexity | Simple | More complex |

## Future Enhancements

Potential improvements for the concurrent evaluator:

1. **Comparison Mode**: Run sequential and concurrent in one command
2. **Enhanced Reporting**: PDF reports with latency histograms
3. **Timeline Visualization**: Chart showing requests over time
4. **Async Support**: Use `asyncio` for even higher concurrency
5. **Retry Logic**: Automatic retry of failed requests
6. **Worker Affinity**: Pin certain prompts to specific workers

## Contributing

When modifying the concurrent evaluator:

1. Maintain thread safety (use locks for shared state)
2. Update timing metrics consistently
3. Add tests to `test_concurrent_basic.py`
4. Update this documentation
5. Follow existing code patterns from `prompt_evaluator.py`

## References

- Main evaluator: `prompt_evaluator.py`
- Project documentation: `WARP.md`
- pocketflow library: https://github.com/pocketflow/pocketflow
- Python ThreadPoolExecutor: https://docs.python.org/3/library/concurrent.futures.html

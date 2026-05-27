# Sequential vs Concurrent Evaluator Comparison

## Overview

Both evaluators now provide comprehensive performance metrics, making it easy to compare baseline performance against concurrent execution benefits.

## Quick Reference

| Feature | Sequential | Concurrent |
|---------|-----------|-----------|
| **Execution** | One request at a time | Multiple parallel requests |
| **Throughput** | 1-3 prompts/sec (typical) | 5-20x sequential |
| **Use Case** | Baseline performance, small datasets | Load testing, large datasets |
| **Output Suffix** | `_results` | `_concurrent_results` |
| **Extra Metrics** | - | Queue time, worker distribution |

## When to Use Each

### Use Sequential Evaluator When:
- Establishing baseline API performance
- Working with small datasets (< 100 prompts)
- Testing scanner accuracy without load concerns
- Don't want to risk triggering auto-scaling
- Need simple, straightforward execution

### Use Concurrent Evaluator When:
- Load testing API capacity
- Processing large datasets efficiently (> 100 prompts)
- Simulating multi-user scenarios
- Understanding API behavior under concurrent load
- Need to complete evaluation quickly

## Performance Metrics Comparison

### Metrics Available in Both

Both evaluators report:
- **Throughput** (prompts/sec)
- **Request Latency** (avg, min, max, p50, p95, p99)
- **Total Elapsed Time**
- **Prompt Size Statistics**

### Additional Metrics in Concurrent

Concurrent evaluator adds:
- **Queue Time**: Time waiting for available worker
- **Worker Distribution**: How work is spread across threads
- **Configuration Details**: Worker count, rate limits

## Example Outputs

### Sequential Evaluator

```
Performance Metrics:
===================

Throughput:
-----------
Overall: 2.11 prompts/sec
Total Prompts: 5
Total Elapsed Time: 2.37 seconds

Request Latency (API call time):
--------------------------------
Average: 472.01 ms
Minimum: 324.34 ms
Maximum: 659.15 ms
p50 (median): 410.45 ms
p95: 648.98 ms
p99: 657.12 ms
Total Requests: 5/5 valid responses
```

### Concurrent Evaluator

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

## Interpreting Results

### Throughput Comparison

**Expected behavior:**
- Concurrent throughput should be 5-20x higher than sequential
- If speedup is less than 3x, API may be bottlenecked

**Example:**
```
Sequential: 2.11 prompts/sec
Concurrent (10 workers): 15.5 prompts/sec
Speedup: 7.3x ✓ Good
```

### Latency Comparison

**Expected behavior:**
- Average latency should be similar in both modes
- If concurrent latency is significantly higher, API is overloaded

**Example:**
```
Sequential avg: 472 ms
Concurrent avg: 485 ms
Difference: 2.7% ✓ Excellent (API not overloaded)

Sequential avg: 472 ms
Concurrent avg: 1250 ms
Difference: 165% ⚠️ Warning (API struggling under load)
```

### Percentiles (p95, p99)

**What they tell you:**
- p95/p99 reveal worst-case user experience
- Large gap between p50 and p99 indicates inconsistent performance
- Concurrent p99 much higher than sequential suggests queuing issues

**Example:**
```
Sequential:
  p50: 410 ms
  p95: 649 ms
  p99: 657 ms
  Gap (p99-p50): 247 ms ✓ Consistent

Concurrent:
  p50: 221 ms
  p95: 456 ms
  p99: 1523 ms
  Gap (p99-p50): 1302 ms ⚠️ High variance
```

## Best Practices

### 1. Always Start Sequential

Run sequential first to establish baseline:
```bash
python prompt_evaluator.py -i datasets/test.jsonl
```

### 2. Gradually Increase Concurrency

Don't jump straight to high concurrency:
```bash
# Start low
python prompt_evaluator_concurrent.py -i datasets/test.jsonl -c 5

# Increase gradually
python prompt_evaluator_concurrent.py -i datasets/test.jsonl -c 10
python prompt_evaluator_concurrent.py -i datasets/test.jsonl -c 20
```

### 3. Compare Results

Look for these patterns:
- ✓ **Good**: Concurrent throughput 5-20x sequential, similar latency
- ⚠️ **Caution**: Throughput improves but latency increases significantly
- ❌ **Overload**: High error rates, throughput doesn't improve

### 4. Document Your Findings

Keep a log of performance characteristics:
```
Dataset: combined_dataset.jsonl (1000 prompts)

Sequential:
- Throughput: 2.1 prompts/sec
- Avg latency: 465 ms
- p99: 890 ms

Concurrent (10 workers):
- Throughput: 14.3 prompts/sec (6.8x speedup)
- Avg latency: 478 ms (+2.8%)
- p99: 1205 ms (+35%)
- Conclusion: Sweet spot for this API
```

## Common Questions

### Q: Why is concurrent latency higher?
**A:** Some increase is normal due to:
- Queue time waiting for workers
- API processing multiple requests simultaneously
- Network contention

If increase is > 50%, the API may be overloaded.

### Q: Should I always use concurrent for large datasets?
**A:** Usually yes, but:
- Check with infrastructure team first (auto-scaling concerns)
- Start with low concurrency (5-10 workers)
- Use rate limiting if API has known limits

### Q: Why aren't metrics identical in repeated runs?
**A:** Normal variance due to:
- Network conditions
- API server load
- Other users on the system

Run multiple times and average results for stability.

### Q: Can I compare results from different days?
**A:** Yes, but consider:
- API performance may have changed
- Scanner models may have been updated
- Network conditions vary

Best to re-run both sequential and concurrent on same day.

## Summary

- **Both evaluators now report consistent metrics** for easy comparison
- **Start with sequential** to establish baseline
- **Use concurrent** for large datasets and load testing
- **Compare throughput, latency, and percentiles** to understand API behavior
- **Document findings** for capacity planning

See also:
- [Evaluation Metrics Guide](evaluation-metrics.md) - Detailed metric explanations
- [Concurrent Evaluation](CONCURRENT_EVALUATION.md) - Advanced concurrent usage

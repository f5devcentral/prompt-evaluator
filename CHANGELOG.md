# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Latest API support and clearer results

- Updated scan and LLM-response workflows to work with the latest CalypsoAI API, including project selection and configured provider selection.
- Account for flagged, blocked, redacted, and cleared outcomes consistently across evaluation, saved-result analysis, misclassification exports, and PDF reports.
- Show failed requests, incomplete scans, and invalid rows separately from evaluated samples so accuracy is easier to interpret.
- Support custom output names and configurable formats for all evaluators. Scan tools retain JSONL defaults; the LLM-response evaluator retains CSV.
- Correct report charts and rebuild examples from selected results instead of potentially stale export files.
- Add request timeouts, more accurate parallel-run timing, and checks that reject bad inputs or conflicting output paths before sending data.
- Make setup checks offline by default, keep detailed diagnostic content opt-in, and exclude generated results from Git except for the empty directory placeholder.

Existing supported datasets/results remain usable without a required migration. Recalculated scores can change because detection outcomes and excluded records are now handled consistently. See [what's changed](CHANGES_SUMMARY.md), [usage](docs/usage.md), and [compatibility notes](docs/results-format-changes.md).

## Earlier development notes

The entries below describe earlier changes. Their historical examples and compatibility statements don't replace the current user guides.

### Added
- **Enhanced Performance Metrics in Sequential Evaluator** (2025-12-12)
  - Added throughput calculation (prompts/sec) to sequential evaluator
  - Added latency percentiles (p50, p95, p99) using numpy
  - Added total elapsed time tracking for scan process
  - Converted all timing metrics to milliseconds for consistency with concurrent evaluator
  - Updated output format to match concurrent evaluator structure for easier comparison
  - Enhanced documentation in `docs/evaluation-metrics.md` with performance metrics section

- **Enhanced PDF Reports with Performance Metrics** (2025-12-12)
  - Added throughput section to PDF reports (prompts/sec, total time, total prompts)
  - Added latency percentiles (p50, p95, p99) to PDF reports
  - Created visual chart showing latency distribution (avg, min, max, p50, p95, p99)
  - Added explanatory text about percentile interpretation
  - Updated standalone report generator to calculate percentiles when loading from files
  
### Changed
- **Sequential Evaluator Output Format**
  - Renamed "Latency Statistics" section to "Performance Metrics"
  - Reorganized metrics display to prioritize throughput and latency percentiles
  - Changed time units from seconds to milliseconds for latency metrics
  - Added section headers matching concurrent evaluator for consistency

### Technical Details
- Added `numpy` import to `prompt_evaluator.py`
- Enhanced `ScanPromptsNode` to track start time and total elapsed time
- Modified `LatencyStatsNode` to calculate and display:
  - Throughput (prompts/sec)
  - Latency percentiles (p50, p95, p99) in milliseconds
  - Total scan time in seconds
- Stored `total_scan_time` in shared state for downstream use

### Benefits
- **Direct Comparison**: Users can now directly compare sequential vs concurrent performance with identical metrics
- **Better Insights**: Percentiles reveal latency distribution patterns that averages miss
- **Baseline Establishment**: Sequential throughput provides baseline for evaluating concurrent speedup
- **Industry Standards**: Percentile metrics (p50, p95, p99) align with standard performance measurement practices

### Migration Notes
- No breaking changes to existing functionality
- Output format enhanced but remains human-readable
- PDF reports continue to work with existing data structures
- No changes required to existing datasets or configurations

## Previous Versions

See git history for changes prior to this changelog.

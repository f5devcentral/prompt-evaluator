# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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

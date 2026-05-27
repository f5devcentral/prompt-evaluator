# prompt-evaluator

<p align="center">
  <em>A comprehensive tool for evaluating AI-powered scanners in detecting various types of content using CalypsoAI API.</em>
</p>

<p align="center">
  <!-- Build and Quality -->
  <a href="https://github.com/f5devcentral/prompt-evaluator/actions">
    <img src="https://github.com/f5devcentral/prompt-evaluator/actions/workflows/ci.yml/badge.svg" alt="CI Status">
  </a>
  <img src="https://img.shields.io/github/last-commit/f5devcentral/prompt-evaluator?color=6f42c1&label=Last%20Commit" alt="Last Commit">

  <!-- Version & License -->
  <img src="https://img.shields.io/badge/version-2.0-blue?logo=github&logoColor=white" alt="Version 2.0">
  <a href="https://www.apache.org/licenses/LICENSE-2.0">
    <img src="https://img.shields.io/badge/license-Apache%202.0-success.svg" alt="License: Apache 2.0">
  </a>

  <!-- Language & Runtime -->
  <a href="https://www.python.org/">
    <img src="https://img.shields.io/badge/language-Python-yellow.svg?logo=python&logoColor=white" alt="Python">
  </a>
</p>

## 🎉 Version 2.0 Released!

**Major Release**: [**v2.0.0**](docs/RELEASE_NOTES_v2.0.md) - October 2025

This major release introduces significant improvements to dataset handling, format support, and tooling. Key highlights include multiple dataset formats (JSONL, CSV, TSV, Parquet), enhanced migration tools, improved Hugging Face integration, and comprehensive documentation updates.

**[📋 View Complete Release Notes](docs/RELEASE_NOTES_v2.0.md)** - Detailed changelog, migration guide, and new features

## 🆕 What's New

### PDF Report Generation 🎨
- **Professional Reports**: Beautiful, modern PDF reports with comprehensive analysis
- **Visual Charts**: Confusion matrices, bar charts, and performance visualizations
- **Complete Analysis**: Detailed breakdowns, examples, and recommendations
- **Performance Metrics**: Enhanced reports include throughput, latency percentiles (p50/p95/p99), and distribution charts
- **Easy Sharing**: Presentation-ready format for stakeholders and documentation

### Enhanced Performance Metrics 📊
- **Throughput Metrics**: Processing speed in prompts/second for capacity planning
- **Latency Percentiles**: p50 (median), p95, and p99 for understanding response time distribution
- **Consistent Reporting**: Both sequential and concurrent evaluators report the same metrics
- **Visual Performance Charts**: Latency distribution charts in PDF reports
- **Percentile Interpretation**: Built-in explanations help understand what metrics mean

### Concurrent Evaluation ⚡
- **Parallel Processing**: Evaluate datasets using multiple concurrent workers
- **Load Testing**: Simulate real-world multi-user scenarios
- **Enhanced Metrics**: Queue time analysis, worker distribution, and throughput under load
- **Configurable**: Adjust concurrency levels and rate limiting
- **Safety Guidelines**: Built-in infrastructure impact warnings and best practices

### Improved Dataset Formats
- **Multiple Format Support**: JSONL, CSV, TSV, and Parquet formats
- **Proper Escaping**: No more issues with special characters (pipes, quotes, newlines)
- **Metadata Support**: Store IDs, timestamps, categories, and more
- **Safe Migration**: Convert existing datasets without data loss
- **Backward Compatibility**: All existing scripts work unchanged

### New Tools
- **`prompt_evaluator_concurrent.py`**: Concurrent evaluator for load testing and high-speed processing
- **`report_generator.py`**: Generate professional PDF reports from evaluation results
- **`tools/improved_dataset_converter.py`**: Convert between all formats with validation
- **`tools/enhanced_dataset_reader.py`**: Unified reader that auto-detects formats
- **`tools/migrate_datasets.py`**: Batch migration tool for existing datasets
- **`tools/demo_improved_formats.py`**: Complete demonstration of new features

### Quick Start Examples
```bash
# Sequential evaluation with performance metrics and auto-generated report
python prompt_evaluator.py --input datasets/test_dataset.jsonl

# Concurrent evaluation for faster processing (10 workers)
python prompt_evaluator_concurrent.py -i datasets/test_dataset.jsonl -c 10

# Migrate datasets to JSONL format
python tools/migrate_datasets.py --list  # See current formats
python tools/migrate_datasets.py --all --output-format jsonl  # Migrate all

# Generate PDF report manually
python report_generator.py --dataset test_dataset
```

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment variables:**
   Create a `.env` file with your CalypsoAI API credentials:
   ```
   CALYPSOAI_URL=https://calypsoai.app
   CALYPSOAI_TOKEN=your_api_token_here
   ```

3. **Run evaluation:**
   ```bash
   python prompt_evaluator.py --input datasets/prompt_inject_dataset.csv
   ```

4. **PDF report is automatically generated!** Check `results/` directory

5. **Generate reports manually (optional):**
   ```bash
   # Use just the dataset name (not the full path)
   python report_generator.py --dataset pii_dataset
   ```

## Features

### Core Evaluation
- **Flexible Evaluation**: Works with multiple dataset formats (JSONL, CSV, TSV, Parquet)
- **Batch Processing**: Efficiently process large datasets with progress tracking
- **CalypsoAI Integration**: Direct integration with CalypsoAI API
- **Comprehensive Metrics**: Accuracy, precision, recall, F1 score
- **False Positives/Negatives Export**: Automatic export in multiple formats for easy analysis

### Performance & Scalability
- **Performance Metrics**: Throughput, latency statistics, percentiles (p50/p95/p99)
- **Sequential Evaluation**: Baseline performance testing, one request at a time
- **Concurrent Evaluation**: Parallel processing with configurable workers (5-50+)
- **Load Testing**: Simulate real-world multi-user scenarios with rate limiting
- **Queue Analysis**: Track worker utilization and queue times under load

### Reporting & Visualization
- **Auto-Generated PDF Reports**: Professional reports created after each evaluation
- **Confusion Matrices**: Visual and tabular confusion matrix analysis
- **Performance Charts**: Latency distribution, metrics comparison, throughput graphs
- **Example Errors**: Sample false positives and negatives with context
- **Percentile Explanations**: Built-in interpretation guide for performance metrics

### Dataset Management
- **Multiple Format Support**: JSONL (recommended), CSV, TSV, Parquet, legacy pipe-delimited
- **Auto-Format Detection**: Automatically detects and reads any supported format
- **Enhanced Data Handling**: Proper escaping for special characters (pipes, quotes, newlines)
- **Metadata Support**: Store IDs, timestamps, categories, and custom fields
- **Safe Migration Tools**: Convert between formats with automatic backups and validation
- **Hugging Face Integration**: Download datasets directly from Hugging Face

### Developer Experience
- **Backward Compatibility**: All existing scripts work with new formats unchanged
- **Multiple Output Formats**: JSON (default), CSV, TSV, and Parquet support
- **Comprehensive Documentation**: Detailed guides, examples, and best practices
- **Testing Framework**: Simplified test runner with core functionality tests
- **Makefile Commands**: Common operations accessible via `make` commands

## Documentation

### Getting Started
- **[📋 Release Notes v2.0](docs/RELEASE_NOTES_v2.0.md)** - Complete changelog and migration guide
- **[Installation Guide](docs/installation.md)** - Detailed setup instructions
- **[Usage Guide](docs/usage.md)** - Complete usage examples and options

### Evaluation & Metrics
- **[Evaluation Metrics](docs/evaluation-metrics.md)** - Understanding accuracy and performance metrics
- **[⚡ Sequential vs Concurrent](docs/SEQUENTIAL_VS_CONCURRENT.md)** - When to use each evaluator and comparing results
- **[⚠️ Concurrent Evaluation](docs/CONCURRENT_EVALUATION.md)** - Load testing guide with safety guidelines
- **[🎨 PDF Report Features](docs/PDF_REPORT_FEATURES.md)** - Complete guide to PDF reports and metrics

### Dataset Management
- **[Dataset Management](docs/datasets.md)** - Working with datasets and Hugging Face
- **[🆕 Improved Dataset Formats](docs/IMPROVED_DATASET_FORMATS.md)** - New dataset formats and migration guide
- **[🆕 Dataset Tools](tools/README.md)** - New dataset tools and utilities

### Reference
- **[Troubleshooting](docs/troubleshooting.md)** - Common issues and solutions
- **[Contributing](docs/contributing.md)** - How to contribute to the project
- **[📝 Documentation Organization](docs/DOCUMENTATION_ORGANIZATION.md)** - How documentation is structured

## Available Tools

### Evaluation Tools

| Tool | Description | Speed | Best For |
|------|-------------|-------|----------|
| `prompt_evaluator.py` | Sequential evaluation with full metrics | Baseline | Accuracy testing, small datasets, establishing baseline |
| `prompt_evaluator_prompts.py` | Advanced evaluation with LLM responses | Baseline | Detailed analysis requiring full response text |
| **`prompt_evaluator_concurrent.py`** | **Parallel evaluation with workers** | **5-20x faster** | **Large datasets, load testing, production scenarios** |
| `evaluate_existing_results.py` | Re-calculate metrics without API calls | Instant | Re-analyzing existing results, metric verification |

### Reporting & Analysis

| Tool | Purpose | Output |
|------|---------|--------|
| **`report_generator.py`** | Generate professional PDF reports | PDF with charts, confusion matrices, performance metrics |
| `download_hf_datasets.py` | Download datasets from Hugging Face | Dataset files in local `datasets/` directory |

### Dataset Tools (in `tools/` directory)

| Tool | Purpose | Key Features |
|------|---------|-------------|
| `enhanced_dataset_reader.py` | Read any dataset format | Auto-detection, unified interface, metadata support |
| `improved_dataset_converter.py` | Convert between formats | Validation, proper escaping, metadata preservation |
| `migrate_datasets.py` | Batch migrate datasets | Automatic backups, format detection, safety checks |
| `demo_improved_formats.py` | Interactive demonstration | Shows all formats, migration examples, comparisons |

> **⚠️ Important**: The concurrent evaluator can trigger infrastructure auto-scaling. See [Concurrent Evaluation Documentation](docs/CONCURRENT_EVALUATION.md#-important-infrastructure-impact-warning) for safety guidelines before use.

## Usage Examples

### Basic Evaluation
```bash
# Run evaluation on a dataset (auto-generates PDF report)
python prompt_evaluator.py --input datasets/pii_dataset.jsonl

# Limit number of prompts processed
python prompt_evaluator.py -i datasets/large_dataset.jsonl -l 100

# Specify output format for false positive/negative files
python prompt_evaluator.py -i datasets/test.jsonl --format csv
```

### Concurrent Evaluation
```bash
# Run with default concurrency (10 workers)
python prompt_evaluator_concurrent.py -i datasets/pii_dataset.jsonl

# Adjust concurrency level
python prompt_evaluator_concurrent.py -i datasets/large_dataset.jsonl -c 20

# Add rate limiting (50 requests/second)
python prompt_evaluator_concurrent.py -i datasets/test.jsonl --rate-limit 50

# Quick test with small sample
python prompt_evaluator_concurrent.py -i datasets/test.jsonl -l 50 -c 5
```

### Performance Comparison
```bash
# 1. Establish baseline with sequential
python prompt_evaluator.py -i datasets/test.jsonl

# 2. Compare with concurrent
python prompt_evaluator_concurrent.py -i datasets/test.jsonl -c 10

# 3. Review both reports to compare throughput and latency
# Check results/test_results.jsonl vs results/test_concurrent_results.jsonl
```

### Dataset Migration
```bash
# Check current dataset formats
python tools/migrate_datasets.py --list

# Migrate all datasets to JSONL
python tools/migrate_datasets.py --all --output-format jsonl

# Migrate specific dataset
python tools/migrate_datasets.py --input datasets/old_format.csv --output-format jsonl

# Convert without backups (use with caution)
python tools/migrate_datasets.py --input datasets/test.csv --output-format jsonl --no-backup
```

### Report Generation
```bash
# Reports are auto-generated after evaluation, but you can also generate manually:

# Generate from dataset name (looks in results/ directory)
python report_generator.py --dataset pii_dataset

# Auto-detect if only one results file exists
python report_generator.py
```

### Re-analyzing Results
```bash
# Re-calculate metrics from existing results (no API calls)
python evaluate_existing_results.py --input results/pii_dataset_results.jsonl

# Useful after fixing dataset labels or for metric verification
```

### Advanced Usage
```bash
# Advanced evaluation with full LLM responses
python prompt_evaluator_prompts.py --input datasets/test.jsonl

# Download datasets from Hugging Face
python download_hf_datasets.py

# Convert dataset formats with validation
python tools/improved_dataset_converter.py input.csv output.jsonl --validate

# Run full demo of dataset features
python tools/demo_improved_formats.py
```

### Using Makefile Commands
```bash
# Run concurrent evaluation
make run-concurrent DATASET=datasets/pii_dataset.jsonl

# With custom settings
make run-concurrent DATASET=datasets/test.jsonl CONCURRENCY=20 LINES=100

# Run tests
make test-core          # Core functionality tests
make test-concurrent    # Test concurrent evaluator

# Code quality
make lint               # Run linting
make format-fix         # Format code with black
make pre-commit         # Run all pre-commit checks
```

## Sample Datasets

The project includes several sample datasets in the `datasets/sample-datasets/` folder:
- `codesagar_malicious_llm_prompts_v4_test.jsonl` - Prompt injection examples
- `pii_dataset.jsonl` - Personally identifiable information examples
- `fin_advice_dataset.jsonl` - Financial advice prompts
- `eu-ai-act-prompts.jsonl` - EU AI Act compliance prompts
- `xTRam1_safe_guard_prompt_injection_test.jsonl` - Additional prompt injection test cases


## Key Concepts

### Understanding Performance Metrics

**Throughput**: Measures how many prompts you can process per second. Essential for capacity planning.
- Sequential: 1-3 prompts/sec (typical)
- Concurrent (10 workers): 5-20x faster

**Latency Percentiles**: Show the distribution of response times, not just averages.
- **p50 (median)**: Typical user experience
- **p95**: 95% of requests are faster than this
- **p99**: Worst-case scenario for most users

See [Evaluation Metrics Guide](docs/evaluation-metrics.md) for detailed explanations.

### Sequential vs Concurrent: When to Use Each

**Use Sequential When:**
- Establishing baseline API performance
- Testing with small datasets (< 100 prompts)
- You don't want to risk infrastructure impact
- Simple, straightforward execution is needed

**Use Concurrent When:**
- Processing large datasets efficiently (> 100 prompts)
- Load testing API capacity
- Simulating multi-user production scenarios
- Time is critical and you need results quickly

**Important**: Always check with infrastructure teams before running concurrent evaluation against shared environments.

See [Sequential vs Concurrent Comparison](docs/SEQUENTIAL_VS_CONCURRENT.md) for detailed guidance.

### Dataset Format Recommendations

**Use JSONL (Recommended)**:
- No escaping issues with special characters
- Supports metadata (IDs, timestamps, categories)
- Easy to parse and stream
- Human-readable

**Use CSV/TSV When**:
- Compatibility with spreadsheet tools needed
- Smaller file sizes preferred
- No complex metadata required

**Use Parquet When**:
- Very large datasets (> 100k records)
- Maximum compression needed
- Working with data science tools

See [Improved Dataset Formats](docs/IMPROVED_DATASET_FORMATS.md) for migration guide.

## Best Practices

### Evaluation Workflow
1. **Start with sequential** to establish baseline performance
2. **Review PDF report** for accuracy metrics and initial performance
3. **Test concurrent** with low concurrency first (-c 5)
4. **Gradually increase** workers to find optimal concurrency
5. **Compare metrics** between sequential and concurrent runs
6. **Archive reports** for historical tracking and trend analysis

### Dataset Management
1. **Migrate to JSONL** for new datasets
2. **Use automatic backups** when migrating (default behavior)
3. **Validate after conversion** using `--validate` flag
4. **Include metadata** (IDs, timestamps) for better tracking
5. **Keep original formats** as backups until migration is verified

### Performance Testing
1. **Coordinate with infrastructure** before load testing shared environments
2. **Start conservatively** with low concurrency and small datasets
3. **Use rate limiting** to avoid overwhelming APIs
4. **Monitor both accuracy and performance** - don't sacrifice one for the other
5. **Document findings** in PDF reports for future reference

### Report Analysis
1. **Focus on F1 score** for balanced evaluation
2. **Check percentiles** (p95/p99) not just averages
3. **Review false positives/negatives** files for patterns
4. **Compare over time** to track performance trends
5. **Share with stakeholders** - reports are presentation-ready

## Troubleshooting

For common issues and solutions, see the [Troubleshooting Guide](docs/troubleshooting.md).

**Quick fixes:**
- **"CALYPSOAI_TOKEN not found"**: Create `.env` file with API credentials
- **"Format not detected"**: Use `--format-hint` parameter or check file extension
- **High error rates in concurrent**: Reduce concurrency or add rate limiting
- **Report generation fails**: Ensure dataset name (not path) is provided

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please see our [Contributing Guide](docs/contributing.md) for details.
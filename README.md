# prompt-evaluator

<p align="center">
  <em>A comprehensive tool for evaluating AI-powered scanners in detecting various types of content using CalypsoAI API.</em>
</p>

<p align="center">
  <!-- Build and Quality -->
  <a href="https://gitlab.com/Artemouse/prompt-evaluator/commits/master">
    <img src="https://gitlab.com/Artemouse/prompt-evaluator/badges/master/pipeline.svg?cache=none" alt="Pipeline Status">
  </a>
  <img src="https://img.shields.io/gitlab/last-commit/Artemouse/prompt-evaluator?color=6f42c1&label=Last%20Commit" alt="Last Commit">

  <!-- Version & License -->
  <img src="https://img.shields.io/badge/version-2.0-blue?logo=gitlab&logoColor=white" alt="Version 2.0">
  <a href="https://opensource.org/licenses/MIT">
    <img src="https://img.shields.io/badge/license-MIT-success.svg" alt="License: MIT">
  </a>

  <!-- Language & Runtime -->
  <a href="https://www.python.org/">
    <img src="https://img.shields.io/badge/language-Python-yellow.svg?logo=python&logoColor=white" alt="Python">
  </a>
</p>

## 🎉 Version 2.0 Released!

**Major Release**: [**v2.0.0**](RELEASE_NOTES_v2.0.md) - October 2025

This major release introduces significant improvements to dataset handling, format support, and tooling. Key highlights include multiple dataset formats (JSONL, CSV, TSV, Parquet), enhanced migration tools, improved Hugging Face integration, and comprehensive documentation updates.

**[📋 View Complete Release Notes](RELEASE_NOTES_v2.0.md)** - Detailed changelog, migration guide, and new features

## 🆕 What's New

### PDF Report Generation 🎨
- **Professional Reports**: Beautiful, modern PDF reports with comprehensive analysis
- **Visual Charts**: Confusion matrices, bar charts, and performance visualizations
- **Complete Analysis**: Detailed breakdowns, examples, and recommendations
- **Easy Sharing**: Presentation-ready format for stakeholders and documentation

### Improved Dataset Formats
- **Multiple Format Support**: JSONL, CSV, TSV, and Parquet formats
- **Proper Escaping**: No more issues with special characters (pipes, quotes, newlines)
- **Metadata Support**: Store IDs, timestamps, categories, and more
- **Safe Migration**: Convert existing datasets without data loss
- **Backward Compatibility**: All existing scripts work unchanged

### New Tools
- **`report_generator.py`**: Generate professional PDF reports from evaluation results
- **`tools/improved_dataset_converter.py`**: Convert between all formats with validation
- **`tools/enhanced_dataset_reader.py`**: Unified reader that auto-detects formats
- **`tools/migrate_datasets.py`**: Batch migration tool for existing datasets
- **`tools/demo_improved_formats.py`**: Complete demonstration of new features

### Quick Migration
```bash
# See your current datasets
python tools/migrate_datasets.py --list

# Migrate all to JSONL format (recommended)
python tools/migrate_datasets.py --all --output-format jsonl

# Continue using existing scripts - no changes needed!
python prompt_evaluator.py --input datasets/my_dataset.jsonl
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

## Features

- **Flexible Evaluation**: Works with any CSV dataset
- **Batch Processing**: Efficiently process large datasets
- **CalypsoAI Integration**: Direct integration with CalypsoAI API
- **Comprehensive Metrics**: Accuracy, precision, recall, F1 score, latency stats
- **False Positives/Negatives Export**: Automatic export in JSON format for easy analysis
- **Dataset Management**: Download from Hugging Face, convert existing datasets
- **🆕 Multiple Output Formats**: JSON (default), CSV, TSV, and Parquet support
- **🆕 Improved Dataset Formats**: Support for JSONL, CSV, TSV, and Parquet formats
- **🆕 Enhanced Data Handling**: Proper escaping, metadata support, and format validation
- **🆕 Migration Tools**: Safe migration from legacy pipe-delimited format

## Documentation

- **[📋 Release Notes v2.0](RELEASE_NOTES_v2.0.md)** - Complete changelog and migration guide
- **[Installation Guide](docs/installation.md)** - Detailed setup instructions
- **[Usage Guide](docs/usage.md)** - Complete usage examples and options
- **[Dataset Management](docs/datasets.md)** - Working with datasets and Hugging Face
- **[🆕 Improved Dataset Formats](docs/IMPROVED_DATASET_FORMATS.md)** - New dataset formats and migration guide
- **[🆕 PDF Reports](docs/pdf-reports.md)** - Generate professional PDF reports
- **[🆕 Dataset Tools](tools/README.md)** - New dataset tools and utilities
- **[Evaluation Metrics](docs/evaluation-metrics.md)** - Understanding performance metrics
- **[Troubleshooting](docs/troubleshooting.md)** - Common issues and solutions
- **[Contributing](docs/contributing.md)** - How to contribute to the project

## Available Tools

| Tool | Description | Use Case |
|------|-------------|----------|
| `prompt_evaluator.py` | Standard CalypsoAI evaluation | General purpose evaluation |
| `prompt_evaluator_prompts.py` | Advanced CalypsoAI with LLM responses | Detailed analysis with full responses |
| `evaluate_existing_results.py` | Calculate metrics from existing results | Re-analyze without re-scanning |
| **`report_generator.py`** | **Generate professional PDF reports** | **Create presentation-ready reports** |

## Sample Datasets

The project includes several sample datasets in the `datasets/sample-datasets/` folder:
- `codesagar_malicious_llm_prompts_v4_test.jsonl` - Prompt injection examples
- `pii_dataset.jsonl` - Personally identifiable information examples
- `fin_advice_dataset.jsonl` - Financial advice prompts
- `eu-ai-act-prompts.jsonl` - EU AI Act compliance prompts
- `xTRam1_safe_guard_prompt_injection_test.jsonl` - Additional prompt injection test cases


## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please see our [Contributing Guide](docs/contributing.md) for details.
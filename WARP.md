# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

A comprehensive Python tool for evaluating AI-powered scanners (CalypsoAI API) in detecting various types of content like prompt injection, PII, financial advice, and other security threats. Built with the `pocketflow` workflow library for structured data processing.

**Key purpose**: Batch evaluation of scanner accuracy with comprehensive metrics, false positive/negative analysis, and professional PDF reporting.

## Common Commands

### Setup & Installation
```bash
# Install production dependencies
pip install -r requirements.txt

# Install development dependencies (includes testing tools)
pip install -r requirements-test.txt

# Setup complete dev environment (creates .env template)
make setup-dev
```

### Running Evaluations
```bash
# Standard evaluation (auto-generates PDF report)
python prompt_evaluator.py --input datasets/prompt_inject_dataset.csv

# Advanced evaluation with full LLM responses
python prompt_evaluator_prompts.py --input datasets/pii_dataset.csv

# Limit lines processed
python prompt_evaluator.py -i datasets/pii_dataset.csv -l 100

# Specify output format (json/csv/tsv/parquet)
python prompt_evaluator.py -i datasets/pii_dataset.csv --results-format csv --format json

# Re-evaluate existing results without API calls
python evaluate_existing_results.py --input results/pii_dataset_results.csv
```

### PDF Reports
```bash
# Reports are auto-generated after each evaluation

# Generate report manually (use dataset NAME only, not path or extension)
python report_generator.py --dataset pii_dataset

# Auto-detect if only one dataset exists
python report_generator.py
```

### Dataset Management
```bash
# Download datasets from Hugging Face
python download_hf_datasets.py

# List all datasets and their formats
python tools/migrate_datasets.py --list

# Migrate all datasets to JSONL (recommended format)
python tools/migrate_datasets.py --all --output-format jsonl

# Convert specific dataset
python tools/improved_dataset_converter.py input.csv output.jsonl --output-format jsonl
```

### Testing
```bash
# Run all core tests
make test-core

# Run specific test categories
make test-simple          # Core functionality only
make test-converter       # Dataset converter tests
make test-reader          # Enhanced reader tests
make test-integration     # Integration tests

# Using test runner directly
python tests/test_runner_simple.py --all
python tests/test_runner_simple.py --core

# Run individual test files
python -m pytest tests/test_core_functionality.py -v
python -m pytest tests/test_dataset_converter.py -v

# Pre-commit checks (lint, format, type-check, test)
make pre-commit
```

### Code Quality
```bash
# Run linting
make lint

# Format code with black
make format-fix

# Type checking
make type-check

# Security scans
make security

# Clean up generated files
make clean
```

### CI/CD Simulation
```bash
# Run full CI/CD pipeline locally
make ci-test
```

## Architecture

### Workflow Pattern (pocketflow)
The codebase uses `pocketflow` (a lightweight workflow library) to structure evaluations as directed graphs of processing nodes. This provides:
- **Modularity**: Each step is a separate Node class
- **Shared state**: Nodes pass data via `shared` dictionary
- **Sequential processing**: Nodes execute in defined order
- **Batch processing**: BatchNode for efficient parallel operations

**Key node types:**
- `Node`: Single execution step (prep → exec → post pattern)
- `BatchNode`: Parallel processing of multiple items
- `Flow`: Orchestrates node execution

### Main Scripts Architecture

#### prompt_evaluator.py (Standard Evaluator)
**Flow**: LoadDataset → ScanPrompts (BatchNode) → SaveResults → EvaluateAccuracy → ExportFalseResults → GenerateReport

Key Nodes:
- `LoadDatasetNode`: Uses enhanced dataset reader for multi-format support
- `ScanPromptsNode`: BatchNode that scans prompts via CalypsoAI `/scans` endpoint
- `SaveResultsNode`: Writes results to configurable format
- `EvaluateAccuracyNode`: Calculates confusion matrix and metrics
- `ExportFalseResultsNode`: Separates false positives/negatives
- `GeneratePDFReportNode`: Creates professional PDF report

#### prompt_evaluator_prompts.py (Advanced Evaluator)
Similar flow but uses `/prompts` endpoint for detailed LLM responses and scanner results. Includes full response text in output.

#### report_generator.py
Standalone PDF report generator using ReportLab and Matplotlib. Creates:
- Confusion matrices (visual + table)
- Performance metrics charts
- Detailed analysis sections
- Example errors with samples

### Dataset Handling System

**Enhanced Dataset Reader** (`tools/enhanced_dataset_reader.py`):
- Auto-detects format (JSONL, CSV, TSV, pipe-delimited, Parquet)
- Unified interface via `load_dataset_enhanced()`
- Returns structured PromptRecord objects
- Handles metadata and special characters

**Dataset Converter** (`tools/improved_dataset_converter.py`):
- Converts between all supported formats
- Maintains metadata preservation
- Validates data integrity
- Handles special characters (pipes, quotes, newlines)

**Format priority**: JSONL (recommended) → CSV → TSV → Parquet → pipe-delimited (legacy)

### Output File Organization
```
results/
├── {dataset_name}_results.{format}           # Main evaluation results
├── {dataset_name}_false_positives.{format}   # FP for analysis
├── {dataset_name}_false_negatives.{format}   # FN for analysis
└── {dataset_name}_report.pdf                 # Auto-generated report
```

Dataset names are extracted from input filenames (without extension).

### CalypsoAI API Integration

**Authentication**: Uses Bearer token from `CALYPSOAI_TOKEN` env var

**Endpoints used:**
- `/scans`: Standard scanner evaluation (prompt_evaluator.py)
- `/prompts`: Advanced evaluation with LLM responses (prompt_evaluator_prompts.py)

**Response handling:**
- Tracks response times for latency metrics
- Handles nested response format: `result.outcome`
- Calculates prompt size (character count)
- Graceful error handling with continued processing

## Important Patterns & Conventions

### Environment Variables
Must configure `.env` file:
```bash
CALYPSOAI_URL=https://calypsoai.app
CALYPSOAI_TOKEN=your_api_token_here
```

Accessed via `python-dotenv` with `load_dotenv(override=True)` for proper loading.

### Dataset Formats
**Recommended**: JSONL format for new datasets
```json
{"prompt": "text", "expected": "false", "id": "123", "metadata": {...}}
```

**Legacy**: Pipe-delimited format still supported
```
"prompt text"|false
```

All evaluator scripts automatically detect format - no code changes needed.

### Expected Values
- `"true"` or `"false"` strings in dataset
- Compared against scanner outcomes: `"flagged"` or `"cleared"`

### Confusion Matrix Logic
- True Positive: expected='true', outcome='flagged'
- True Negative: expected='false', outcome='cleared'
- False Positive: expected='false', outcome='flagged'
- False Negative: expected='true', outcome='cleared'

### Output Format Configuration
Both evaluators support `--format` (FP/FN) and `--results-format` (main results):
- `json`: JSONL format (default, recommended)
- `csv`: Standard CSV with proper escaping
- `tsv`: Tab-separated values
- `parquet`: Binary format (requires pandas)

### PDF Report Dataset Names
**Critical**: Use dataset NAME only, not full path or extension
```bash
# ✅ Correct
python report_generator.py --dataset pii_dataset

# ❌ Wrong - don't include path/extension/_results
python report_generator.py --dataset results/pii_dataset_results.jsonl
```

The script automatically looks in `results/` and searches for `{name}_results.{ext}`.

### Testing Structure
**Simplified approach**: Focus on core functionality that works reliably
- Use `test_runner_simple.py` for consistent test execution
- Makefile commands wrap test runner for convenience
- Tests organized by feature: converter, reader, integration, core
- Only run tests verified to work (filtering in test runner)

### Node Development Pattern
When creating new nodes:
```python
class MyNode(Node):
    def prep(self, shared):
        # Extract needed data from shared state
        # Return tuple of inputs for exec
        pass
    
    def exec(self, inputs):
        # Perform the actual work
        # Return results
        pass
    
    def post(self, shared, prep_res, exec_res):
        # Store results in shared state
        shared["my_results"] = exec_res
        # Return next edge name
        return "default"
```

For batch processing:
```python
class MyBatchNode(BatchNode):
    def prep(self, shared):
        # Return list of items to process
        return items_list
    
    def exec(self, item):
        # Process single item
        return result
    
    def post(self, shared, prep_res, exec_res_list):
        # exec_res_list contains all results
        shared["batch_results"] = exec_res_list
        return "default"
```

### Progress Tracking
BatchNodes typically print progress every 10 items:
```python
if self.processed_count % 10 == 0 or self.processed_count == self.total_prompts:
    print(f"Progress: {self.processed_count}/{self.total_prompts} ({percentage:.1f}%)")
```

## File Structure
```
.
├── prompt_evaluator.py              # Main evaluator (standard)
├── prompt_evaluator_prompts.py      # Advanced evaluator (with LLM responses)
├── report_generator.py              # PDF report generator
├── evaluate_existing_results.py     # Re-analyze results without API calls
├── download_hf_datasets.py          # Download from Hugging Face
├── convert_dataset.py               # Legacy converter
├── tools/
│   ├── enhanced_dataset_reader.py   # Multi-format dataset reader
│   ├── improved_dataset_converter.py # Format converter
│   ├── migrate_datasets.py          # Batch migration tool
│   └── demo_improved_formats.py     # Format examples
├── tests/
│   ├── test_runner_simple.py        # Simplified test runner
│   ├── test_core_functionality.py   # Core feature tests
│   ├── test_dataset_converter.py    # Converter tests
│   ├── test_enhanced_reader.py      # Reader tests
│   └── test_integration.py          # Integration tests
├── datasets/                        # Input datasets
├── results/                         # All evaluation outputs
├── docs/                            # Comprehensive documentation
├── .env                             # API credentials (not in git)
├── requirements.txt                 # Production dependencies
├── requirements-test.txt            # Testing dependencies
├── Makefile                         # Common commands
└── .gitlab-ci.yml                   # CI/CD pipeline

## Testing Guidelines

### Before Committing
```bash
make test-core  # or make quick-test
```

### When Modifying Dataset Handling
```bash
make test-converter
make test-reader
```

### When Modifying Evaluation Logic
```bash
python -m pytest tests/test_core_functionality.py -v
```

### Test Files Are Self-Contained
Each test file creates its own temporary test data - no external dependencies needed.

## Common Development Tasks

### Adding a New Scanner Type
1. Create dataset in supported format (JSONL recommended)
2. Place in `datasets/` directory
3. Run evaluation: `python prompt_evaluator.py -i datasets/new_dataset.jsonl`
4. Review PDF report in `results/`

### Adding a New Node to Evaluation Flow
1. Create node class extending `Node` or `BatchNode`
2. Implement `prep()`, `exec()`, and `post()` methods
3. Add to flow: `flow.add_node("my_node", MyNode())`
4. Connect edges: `flow.add_edge("previous_node", "my_node")`

### Debugging Evaluation Issues
1. Check `.env` has valid API credentials
2. Use `--lines 5` to test with small dataset
3. Review individual result files in `results/`
4. Check `false_positives` and `false_negatives` files
5. Use `evaluate_existing_results.py` to recalculate metrics

### Adding New Output Format
1. Add format handling to `write_results_to_file()` in evaluator scripts
2. Update format detection in dataset reader
3. Add conversion support in `improved_dataset_converter.py`
4. Update documentation

## Dependencies

**Core:**
- `pocketflow==0.0.1` - Workflow orchestration (critical)
- `requests` - API calls
- `python-dotenv` - Environment variables
- `pandas` - Data manipulation
- `datasets` - Hugging Face integration

**Reporting:**
- `reportlab` - PDF generation
- `matplotlib` - Chart generation
- `numpy` - Numerical operations

**Testing:**
- `pytest` - Test framework
- `pytest-cov` - Coverage reporting
- `black` - Code formatting
- `flake8` - Linting
- `mypy` - Type checking

## Performance Considerations

- Batch processing with BatchNode reduces API call overhead
- JSONL format recommended for large datasets (streaming support)
- Parquet format best for very large datasets
- Response times tracked per-prompt for latency analysis
- Progress displayed every 10 items to avoid output spam

## Troubleshooting

### "CALYPSOAI_TOKEN not found"
Create `.env` file with API credentials or run `make setup-dev`

### "Format not detected"
Use `--format-hint` parameter or check file extension matches content

### Tests failing
Run `python tests/test_runner_simple.py --core` for reliable core tests only

### PDF generation fails
Ensure `reportlab` and `matplotlib` are installed: `pip install -r requirements.txt`

### Report generator "dataset not found"
Use dataset name only: `python report_generator.py --dataset pii_dataset` (not full path)

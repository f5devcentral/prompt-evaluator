# Release Notes - Prompt Evaluator v2.0

**Release Date**: October 2025 
**Version**: 2.0.0  
**Type**: Major Release

## 🎉 Overview

This major release introduces significant improvements to dataset handling, format support, and tooling. The focus has been on solving data format limitations, improving user experience, and providing robust migration tools while maintaining full backward compatibility.

## 🆕 New Features

### 1. Improved Dataset Formats

#### Multiple Format Support
- **JSONL (JSON Lines)** - Recommended format for complex data with metadata support
- **CSV with Proper Escaping** - Standard CSV format with proper quote handling
- **TSV (Tab-Separated Values)** - Better alternative to pipe-delimited format
- **Parquet** - Binary format for large datasets with excellent compression

#### Key Benefits
- ✅ **No Escaping Issues**: Handles all special characters (pipes, quotes, newlines)
- ✅ **Metadata Support**: Store IDs, timestamps, categories, and custom fields
- ✅ **Proper Validation**: Built-in format validation and error handling
- ✅ **Backward Compatibility**: All existing scripts work unchanged

### 2. New Dataset Tools

#### Core Tools
- **`tools/improved_dataset_converter.py`** - Convert between all supported formats
- **`tools/enhanced_dataset_reader.py`** - Unified reader with auto-format detection
- **`tools/migrate_datasets.py`** - Batch migration tool for existing datasets
- **`tools/demo_improved_formats.py`** - Complete demonstration of new features
- **`tools/example_improved_formats.py`** - Interactive examples and tutorials

#### Migration Tools
```bash
# List all datasets and their current formats
python tools/migrate_datasets.py --list

# Migrate all datasets to JSONL format (recommended)
python tools/migrate_datasets.py --all --output-format jsonl

# Migrate specific dataset
python tools/migrate_datasets.py --input datasets/my_dataset.csv --output-format jsonl
```

### 3. Enhanced Hugging Face Integration

#### Improved Dataset Downloader
- **Multiple Output Formats**: Download datasets in JSONL, CSV, TSV, or Parquet
- **Smart Column Detection**: Automatically identifies text and label columns
- **Flexible Configuration**: Support for different dataset splits and configurations
- **Sample Limiting**: Download subsets of large datasets

#### New Features
```bash
# Download dataset as CSV
python download_hf_datasets.py --dataset "imdb" --format csv --max-samples 1000

# Download with custom output name
python download_hf_datasets.py --dataset "squad" --output "my_squad.csv" --format csv

# Download specific split
python download_hf_datasets.py --dataset "imdb" --split "test" --format csv
```

### 4. Enhanced Output Formats

#### Configurable False Positives/Negatives Export
- **JSON Format (Default)**: Structured data with metadata
- **CSV Format**: Standard CSV for Excel compatibility
- **TSV Format**: Tab-separated for data processing
- **Parquet Format**: Binary format for large datasets

#### Usage Examples
```bash
# Default JSON format
python prompt_evaluator.py --input datasets/pii_dataset.csv

# CSV format for false positives/negatives
python prompt_evaluator.py --input datasets/pii_dataset.csv --format csv

# TSV format
python prompt_evaluator.py --input datasets/pii_dataset.csv --format tsv
```

### 5. Improved Documentation

#### New Documentation
- **`docs/IMPROVED_DATASET_FORMATS.md`** - Comprehensive guide to new formats
- **`docs/README.md`** - Centralized documentation index
- **`tools/README.md`** - Complete tool documentation
- **`DOCUMENTATION_ORGANIZATION.md`** - Documentation structure guide

#### Enhanced Existing Docs
- Updated installation guide with new dependencies
- Improved usage examples with new features
- Better troubleshooting guide
- Enhanced dataset management documentation

## 🔄 Deprecated Features

### 1. Removed Components

#### Browser Extension (Deprecated)
- **`prompt-evaluator-extension/`** - Entire browser extension removed
- **Reason**: Focus shifted to core evaluation tools and dataset management
- **Migration**: Use command-line tools for batch processing

#### Legacy Files
- **`guardrail_evaluator.py`** - Removed in favor of unified approach
- **`test_label_columns.py`** - Replaced by improved validation tools

### 2. Format Deprecation

#### Pipe-Delimited Format (Legacy)
- **Status**: Still supported but deprecated
- **Issues**: Manual parsing, no escaping, no metadata support
- **Migration**: Use `tools/migrate_datasets.py` to convert to JSONL format
- **Timeline**: Will be removed in v3.0

## 🛠️ Technical Improvements

### 1. Enhanced Data Handling
- **Proper CSV Escaping**: Handles quotes, commas, and special characters correctly
- **Metadata Support**: Store additional information with each record
- **Format Validation**: Built-in validation for all supported formats
- **Error Recovery**: Graceful handling of malformed data

### 2. Performance Optimizations
- **Streaming Processing**: Handle large datasets efficiently
- **Memory Management**: Optimized for large dataset processing
- **Parallel Processing**: Support for concurrent operations
- **Caching**: Improved performance for repeated operations

### 3. Code Quality
- **Type Hints**: Full type annotation coverage
- **Error Handling**: Comprehensive error handling and recovery
- **Documentation**: Extensive inline documentation
- **Testing**: Improved test coverage and validation

## 📊 Format Comparison

| Format | Human Readable | Special Chars | Metadata | Size | Performance | Recommended For |
|--------|----------------|---------------|----------|------|-------------|-----------------|
| **JSONL** | ✅ | ✅ | ✅ | Medium | Fast | **General use** |
| **CSV** | ✅ | ⚠️ | ✅ | Small | Fast | Excel compatibility |
| **TSV** | ✅ | ⚠️ | ✅ | Small | Fast | Data processing |
| **Parquet** | ❌ | ✅ | ✅ | Very Small | Very Fast | Large datasets |
| **Pipe (Legacy)** | ✅ | ❌ | ❌ | Small | Slow | **Deprecated** |

## 🚀 Migration Guide

### For Existing Users

#### Step 1: Analyze Current Datasets
```bash
python tools/migrate_datasets.py --list
```

#### Step 2: Migrate to Better Format
```bash
# Migrate all datasets to JSONL (recommended)
python tools/migrate_datasets.py --all --output-format jsonl

# Or migrate specific datasets
python tools/migrate_datasets.py --input datasets/my_dataset.csv --output-format jsonl
```

#### Step 3: Continue Using Existing Scripts
```bash
# No changes needed to existing code!
python prompt_evaluator.py --input datasets/my_dataset.jsonl
```

### For New Users

#### Quick Start
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set up environment
echo "CALYPSOAI_URL=https://calypsoai.app" > .env
echo "CALYPSOAI_TOKEN=your_token_here" >> .env

# 3. Download a dataset
python download_hf_datasets.py --dataset "imdb" --format csv --max-samples 1000

# 4. Run evaluation
python prompt_evaluator.py --input datasets/imdb_train.csv
```

## 📋 New Dependencies

### Added Dependencies
- **`datasets>=2.14.0`** - Hugging Face datasets library
- **`huggingface_hub>=0.16.0`** - Hugging Face Hub integration
- **`pandas>=1.5.0`** - Enhanced data processing

### Updated Dependencies
- **`requests>=2.31.0`** - HTTP client improvements
- **`python-dotenv>=1.0.0`** - Environment variable management

## 🔧 Configuration Changes

### Environment Variables
No changes to existing environment variables. New optional variables:
- **`HF_TOKEN`** - Hugging Face authentication (optional)
- **`OUTPUT_FORMAT`** - Default output format (optional)

### File Structure Changes
```
project/
├── datasets/                    # Dataset storage
│   ├── *.csv                    # Legacy CSV files
│   ├── *.jsonl                  # New JSONL files (recommended)
│   └── *.backup.csv             # Backup files from migration
├── results/                     # Evaluation results
│   ├── *_results.csv            # Main results
│   ├── *_false_positives.jsonl  # False positives (JSON format)
│   └── *_false_negatives.jsonl  # False negatives (JSON format)
├── tools/                       # New dataset tools
│   ├── improved_dataset_converter.py
│   ├── enhanced_dataset_reader.py
│   ├── migrate_datasets.py
│   └── demo_improved_formats.py
└── docs/                        # Enhanced documentation
    ├── IMPROVED_DATASET_FORMATS.md
    └── README.md
```

## 🎯 Usage Examples

### 1. Dataset Migration
```bash
# List current datasets
python tools/migrate_datasets.py --list

# Migrate all to JSONL
python tools/migrate_datasets.py --all --output-format jsonl

# Validate migration
python tools/improved_dataset_converter.py datasets/my_dataset.jsonl --validate
```

### 2. Download from Hugging Face
```bash
# List popular datasets
python download_hf_datasets.py --list-popular

# Search for datasets
python download_hf_datasets.py --search "sentiment"

# Download as CSV
python download_hf_datasets.py --dataset "imdb" --format csv --max-samples 1000
```

### 3. Enhanced Evaluation
```bash
# Standard evaluation with JSONL
python prompt_evaluator.py --input datasets/my_dataset.jsonl

# Advanced evaluation with custom output format
python prompt_evaluator_prompts.py --input datasets/my_dataset.jsonl --format csv

# Results analysis
python evaluate_existing_results.py --input results/my_dataset_results.csv
```

### 4. Format Conversion
```bash
# Convert between formats
python tools/improved_dataset_converter.py input.csv output.jsonl --output-format jsonl

# Convert with validation
python tools/improved_dataset_converter.py input.csv output.jsonl --validate

# Auto-detect input format
python tools/improved_dataset_converter.py input.csv output.jsonl
```

## 🐛 Bug Fixes

### Data Handling
- **Fixed**: CSV escaping issues with special characters
- **Fixed**: Pipe-delimited format parsing errors
- **Fixed**: Memory issues with large datasets
- **Fixed**: Unicode handling in all formats

### API Integration
- **Fixed**: CalypsoAI API timeout handling
- **Fixed**: Error recovery for failed requests
- **Fixed**: Rate limiting improvements
- **Fixed**: Authentication token handling

### User Experience
- **Fixed**: Better error messages and diagnostics
- **Fixed**: Improved progress reporting
- **Fixed**: Enhanced validation feedback
- **Fixed**: Clearer documentation and examples

## 🔮 Future Roadmap

### v2.1 (Planned)
- **Streaming Processing**: Handle very large datasets efficiently
- **Parallel Evaluation**: Multi-threaded evaluation support
- **Advanced Analytics**: Enhanced metrics and reporting
- **API Improvements**: Better error handling and retry logic

### v3.0 (Planned)
- **Remove Legacy Support**: Drop pipe-delimited format support
- **Enhanced Metadata**: Rich metadata support for all formats
- **Performance Optimization**: Further performance improvements
- **Advanced Migration**: Automated migration tools

## 📞 Support

### Getting Help
- **Documentation**: Check `docs/` directory for comprehensive guides
- **Examples**: Use `tools/demo_improved_formats.py` for demonstrations
- **Migration**: Use `tools/migrate_datasets.py --help` for migration options
- **Issues**: Report issues on GitLab with detailed information

### Common Issues
1. **Migration Problems**: Use `--validate` flag to check conversions
2. **Format Detection**: Use `--format` parameter to specify input format
3. **Large Datasets**: Use `--max-samples` to limit dataset size
4. **Memory Issues**: Consider Parquet format for very large datasets

## 🎉 Conclusion

This major release represents a significant step forward in dataset handling and user experience. The new format support, migration tools, and enhanced documentation provide a robust foundation for prompt evaluation workflows while maintaining full backward compatibility.

**Key Takeaways:**
- ✅ **Improved Data Handling**: No more escaping issues
- ✅ **Multiple Format Support**: Choose the best format for your needs
- ✅ **Easy Migration**: Simple tools to upgrade existing datasets
- ✅ **Backward Compatibility**: All existing code continues to work
- ✅ **Enhanced Documentation**: Comprehensive guides and examples

**Recommended Next Steps:**
1. Migrate your datasets to JSONL format
2. Explore the new dataset tools
3. Update your workflows to use the new features
4. Provide feedback for future improvements

---

**Full Changelog**: See individual commit messages for detailed changes  
**Documentation**: Visit `docs/` directory for comprehensive guides  
**Support**: Open an issue on GitLab for questions or problems

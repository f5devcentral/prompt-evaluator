# Dataset Tools

This directory contains tools for working with improved dataset formats and migration.

## 🆕 New Dataset Tools

### Core Tools

#### `improved_dataset_converter.py`
Convert datasets between different formats with proper escaping and validation.

```bash
# Convert a single dataset
python improved_dataset_converter.py input.csv output.jsonl --output-format jsonl

# Convert with validation
python improved_dataset_converter.py input.csv output.jsonl --validate

# Auto-detect input format
python improved_dataset_converter.py input.csv output.jsonl
```

**Supported Formats:**
- JSONL (recommended)
- CSV with proper escaping
- TSV (tab-separated)
- Parquet (binary format)
- Legacy pipe-delimited

#### `enhanced_dataset_reader.py`
Unified dataset reader that auto-detects formats and handles all special characters.

```python
from enhanced_dataset_reader import EnhancedDatasetReader

# Auto-detect format and read
reader = EnhancedDatasetReader()
records = reader.read_dataset("my_dataset.jsonl")

# Specify format explicitly
records = reader.read_dataset("my_dataset.csv", format_hint="csv")

# Limit number of records
records = reader.read_dataset("my_dataset.jsonl", max_lines=100)
```

#### `migrate_datasets.py`
Batch migration tool for converting existing datasets to improved formats.

```bash
# List all datasets and their formats
python migrate_datasets.py --list

# Migrate all datasets to JSONL format
python migrate_datasets.py --all --output-format jsonl

# Migrate a specific dataset
python migrate_datasets.py --input datasets/my_dataset.csv --output-format jsonl

# Migrate without creating backups
python migrate_datasets.py --all --no-backup
```

### Demo Tools

#### `demo_improved_formats.py`
Complete demonstration of the improved dataset formats solution.

```bash
# Run the full demonstration
python demo_improved_formats.py
```

**Shows:**
- Problems with original pipe-delimited format
- How new formats solve these problems
- Migration process
- Usage examples
- Format comparison

#### `example_improved_formats.py`
Interactive example showing different dataset formats.

```bash
# Run the example
python example_improved_formats.py
```

**Features:**
- Creates sample datasets in all formats
- Demonstrates reading and writing
- Shows file size comparison
- Interactive cleanup

## Format Comparison

| Format | Human Readable | Special Chars | Metadata | Size | Performance |
|--------|----------------|---------------|----------|------|-------------|
| JSONL | ✅ | ✅ | ✅ | Medium | Fast |
| CSV | ✅ | ⚠️ | ✅ | Small | Fast |
| TSV | ✅ | ⚠️ | ✅ | Small | Fast |
| Pipe | ✅ | ❌ | ❌ | Small | Slow |
| Parquet | ❌ | ✅ | ✅ | Very Small | Very Fast |

## Migration Workflow

### 1. Analyze Current Datasets
```bash
python migrate_datasets.py --list
```

### 2. Migrate to Better Format
```bash
# Migrate all datasets to JSONL (recommended)
python migrate_datasets.py --all --output-format jsonl

# Or migrate a specific dataset
python migrate_datasets.py --input datasets/my_dataset.csv --output-format jsonl
```

### 3. Validate Migration
```bash
python improved_dataset_converter.py datasets/my_dataset.jsonl --validate
```

### 4. Continue Using Existing Scripts
```bash
# No changes needed to existing code!
python prompt_evaluator.py --input datasets/my_dataset.jsonl
```

## Benefits

### JSONL Format (Recommended)
- ✅ No escaping issues with any special characters
- ✅ Supports metadata (IDs, timestamps, categories)
- ✅ Easy to parse programmatically
- ✅ Streaming processing support
- ✅ Human-readable

### Backward Compatibility
- ✅ All existing scripts work unchanged
- ✅ Reads both old and new formats
- ✅ Gradual migration supported
- ✅ No breaking changes

## Safety Features

- **Non-destructive**: Original files are never modified
- **Automatic backups**: Creates backup copies by default
- **Validation**: Validates each conversion
- **Rollback**: Easy to revert if needed

## Need Help?

- Check the main [Improved Dataset Formats documentation](../docs/IMPROVED_DATASET_FORMATS.md)
- Run `python migrate_datasets.py --help` for command options
- Run `python improved_dataset_converter.py --help` for conversion options
- Use the demo tools to see examples in action

# Improved Dataset Formats

This document explains the improved dataset formats available in the prompt evaluator, addressing the limitations of the original pipe-delimited format.

## Problems with the Original Format

The original pipe-delimited format (`"prompt"|expected`) had several issues:

1. **Manual parsing**: Required custom string splitting and quote stripping
2. **No escaping**: Long prompts with pipes, quotes, or newlines could break the format
3. **Inconsistent quoting**: Some datasets used triple quotes `"""`, others used single quotes
4. **No metadata**: Couldn't store additional information like IDs, timestamps, etc.
5. **Error-prone**: Manual string manipulation was prone to errors

## New Format Options

### 1. JSON Lines (JSONL) - **Recommended**

**Format**: One JSON object per line
```json
{"prompt": "This is a normal prompt", "expected": "false", "id": "sample_1", "metadata": {"source": "example"}}
{"prompt": "This prompt has commas, quotes \"like this\", and pipes | everywhere", "expected": "true", "id": "sample_2"}
```

**Benefits**:
- ✅ Handles complex data structures
- ✅ Preserves metadata and timestamps
- ✅ No escaping issues with special characters
- ✅ Easy to parse programmatically
- ✅ Supports streaming processing

### 2. CSV with Proper Escaping

**Format**: Standard CSV with quoted fields
```csv
prompt,expected,id,timestamp
"This is a normal prompt",false,sample_1,2024-01-01T00:00:00
"This prompt has ""quotes"" and, commas",true,sample_2,2024-01-01T00:00:00
```

**Benefits**:
- ✅ Standard format, widely supported
- ✅ Proper escaping with quotes
- ✅ Works with Excel and other tools
- ✅ Human-readable

### 3. TSV (Tab-Separated Values)

**Format**: Tab-separated values
```tsv
prompt	expected	id	timestamp
This is a normal prompt	false	sample_1	2024-01-01T00:00:00
This prompt has tabs	and	newlines	true	sample_2	2024-01-01T00:00:00
```

**Benefits**:
- ✅ Less likely to conflict with data content
- ✅ Better than pipe-delimited
- ✅ Easy to parse
- ✅ Good for data with commas

### 4. Parquet (Binary Format)

**Format**: Binary columnar format
- Not human-readable
- Excellent for large datasets
- Built-in compression
- Schema evolution support

## Usage Examples

### Converting Datasets

```bash
# Convert a single dataset
python improved_dataset_converter.py input.csv output.jsonl --output-format jsonl

# Convert with validation
python improved_dataset_converter.py input.csv output.jsonl --validate

# Auto-detect input format
python improved_dataset_converter.py input.csv output.jsonl
```

### Migrating All Datasets

```bash
# List all datasets and their formats
python migrate_datasets.py --list

# Migrate all datasets to JSONL format
python migrate_datasets.py --all --output-format jsonl

# Migrate without creating backups
python migrate_datasets.py --all --no-backup
```

### Using the Enhanced Reader

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

## Migration Guide

### Step 1: Analyze Current Datasets

```bash
python migrate_datasets.py --list
```

This will show you all datasets and their current formats.

### Step 2: Migrate to Better Format

```bash
# Migrate all datasets to JSONL (recommended)
python migrate_datasets.py --all --output-format jsonl

# Or migrate a specific dataset
python migrate_datasets.py --input datasets/my_dataset.csv --output-format jsonl
```

### Step 3: Update Your Code

The prompt evaluator scripts have been updated to automatically detect and read the new formats. No changes needed to your existing code!

## Format Comparison

| Format | Human Readable | Special Chars | Metadata | Size | Performance |
|--------|----------------|---------------|----------|------|-------------|
| JSONL | ✅ | ✅ | ✅ | Medium | Fast |
| CSV | ✅ | ⚠️ | ✅ | Small | Fast |
| TSV | ✅ | ⚠️ | ✅ | Small | Fast |
| Pipe | ✅ | ❌ | ❌ | Small | Slow |
| Parquet | ❌ | ✅ | ✅ | Very Small | Very Fast |

## Best Practices

### For New Datasets
- **Use JSONL format** for maximum flexibility and robustness
- Include metadata like source, timestamp, and category
- Use meaningful IDs for each record

### For Large Datasets
- Consider **Parquet format** for better performance
- Use streaming processing for very large files
- Implement proper error handling

### For Sharing Datasets
- **CSV format** is most widely supported
- Include a README with format documentation
- Provide sample data for testing

## Backward Compatibility

The enhanced dataset reader maintains full backward compatibility:

- ✅ Reads existing pipe-delimited datasets
- ✅ Works with all existing prompt evaluator scripts
- ✅ No changes needed to existing code
- ✅ Gradual migration supported

## Example: Complete Workflow

```bash
# 1. Analyze your current datasets
python migrate_datasets.py --list

# 2. Migrate to JSONL format
python migrate_datasets.py --all --output-format jsonl

# 3. Validate the migration
python improved_dataset_converter.py datasets/my_dataset.jsonl --validate

# 4. Use with prompt evaluator (no changes needed!)
python prompt_evaluator.py --input datasets/my_dataset.jsonl --output results.csv
```

## Troubleshooting

### Common Issues

1. **"Unsupported format" error**
   - Check file extension or use `--format` parameter
   - Ensure file is not corrupted

2. **"No records loaded" error**
   - Check file format and content
   - Verify file permissions

3. **Memory issues with large datasets**
   - Use `max_lines` parameter to limit records
   - Consider Parquet format for very large datasets

### Getting Help

```bash
# Show help for converter
python improved_dataset_converter.py --help

# Show help for migrator
python migrate_datasets.py --help

# Test with sample data
python example_improved_formats.py
```

## Performance Tips

1. **For small datasets (< 10MB)**: Use JSONL or CSV
2. **For medium datasets (10MB - 100MB)**: Use JSONL or TSV
3. **For large datasets (> 100MB)**: Use Parquet
4. **For streaming processing**: Use JSONL
5. **For human editing**: Use CSV

The improved formats solve the original problems while maintaining full backward compatibility. Choose the format that best fits your needs!

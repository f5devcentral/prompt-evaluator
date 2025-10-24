#!/usr/bin/env python3
"""
Example: Improved Dataset Formats

This example demonstrates the new dataset formats and how to use them.
It shows the benefits of each format and provides usage examples.
"""

import json
import os
from pathlib import Path
from .improved_dataset_converter import DatasetConverter
from .enhanced_dataset_reader import EnhancedDatasetReader


def create_sample_data():
    """Create sample data for demonstration."""
    return [
        {
            "prompt": "This is a normal prompt without any special characters.",
            "expected": "false",
            "id": "sample_1",
            "metadata": {"source": "example", "category": "normal"}
        },
        {
            "prompt": "This prompt contains commas, quotes \"like this\", and newlines.\nIt also has pipes | and other | special | characters.",
            "expected": "true",
            "id": "sample_2", 
            "metadata": {"source": "example", "category": "complex", "difficulty": "high"}
        },
        {
            "prompt": "Simple prompt with just a pipe | character",
            "expected": "false",
            "id": "sample_3",
            "metadata": {"source": "example", "category": "simple"}
        }
    ]


def demonstrate_formats():
    """Demonstrate different dataset formats."""
    print("🔬 Dataset Format Comparison")
    print("=" * 50)
    
    # Create sample data
    sample_data = create_sample_data()
    
    # Initialize converter and reader
    converter = DatasetConverter()
    reader = EnhancedDatasetReader()
    
    # Create temporary directory for examples
    examples_dir = Path("format_examples")
    examples_dir.mkdir(exist_ok=True)
    
    formats_to_demo = ['jsonl', 'csv', 'tsv', 'pipe']
    
    print(f"\n📝 Creating sample datasets in {len(formats_to_demo)} formats...")
    
    for format_type in formats_to_demo:
        output_file = examples_dir / f"sample.{format_type}"
        
        # Convert sample data to the format
        if format_type == 'jsonl':
            with open(output_file, 'w') as f:
                for item in sample_data:
                    json.dump(item, f)
                    f.write('\n')
        elif format_type == 'csv':
            import csv
            with open(output_file, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=['prompt', 'expected', 'id', 'metadata'])
                writer.writeheader()
                for item in sample_data:
                    # Convert metadata to string for CSV
                    item_copy = item.copy()
                    item_copy['metadata'] = json.dumps(item['metadata'])
                    writer.writerow(item_copy)
        elif format_type == 'tsv':
            import csv
            with open(output_file, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=['prompt', 'expected', 'id', 'metadata'], delimiter='\t')
                writer.writeheader()
                for item in sample_data:
                    # Convert metadata to string for TSV
                    item_copy = item.copy()
                    item_copy['metadata'] = json.dumps(item['metadata'])
                    writer.writerow(item_copy)
        elif format_type == 'pipe':
            with open(output_file, 'w') as f:
                for item in sample_data:
                    # Escape quotes and wrap in quotes
                    escaped_prompt = item['prompt'].replace('"', '""')
                    f.write(f'"{escaped_prompt}"|{item["expected"]}\n')
        
        print(f"   ✅ Created {format_type.upper()}: {output_file}")
    
    # Demonstrate reading each format
    print(f"\n📖 Reading datasets back...")
    
    for format_type in formats_to_demo:
        input_file = examples_dir / f"sample.{format_type}"
        
        try:
            records = reader.read_dataset(str(input_file), format_type)
            print(f"   {format_type.upper()}: {len(records)} records")
            
            # Show first record details
            if records:
                first_record = records[0]
                print(f"      First record: {first_record.prompt[:50]}...")
                print(f"      Expected: {first_record.expected}")
                print(f"      Has metadata: {bool(first_record.metadata)}")
        
        except Exception as e:
            print(f"   ❌ Error reading {format_type}: {e}")
    
    # Show file sizes
    print(f"\n📊 File size comparison:")
    for format_type in formats_to_demo:
        file_path = examples_dir / f"sample.{format_type}"
        if file_path.exists():
            size = file_path.stat().st_size
            print(f"   {format_type.upper()}: {size:,} bytes")
    
    return examples_dir


def demonstrate_conversion():
    """Demonstrate converting between formats."""
    print(f"\n🔄 Format Conversion Demo")
    print("=" * 30)
    
    converter = DatasetConverter()
    examples_dir = Path("format_examples")
    
    # Convert from pipe format to other formats
    pipe_file = examples_dir / "sample.pipe"
    
    if pipe_file.exists():
        for target_format in ['jsonl', 'csv', 'tsv']:
            output_file = examples_dir / f"converted.{target_format}"
            
            try:
                converter.convert_dataset(
                    str(pipe_file),
                    str(output_file),
                    input_format='pipe',
                    output_format=target_format
                )
                print(f"   ✅ Converted pipe → {target_format.upper()}")
            except Exception as e:
                print(f"   ❌ Failed pipe → {target_format.upper()}: {e}")


def demonstrate_validation():
    """Demonstrate dataset validation."""
    print(f"\n🔍 Dataset Validation Demo")
    print("=" * 30)
    
    converter = DatasetConverter()
    examples_dir = Path("format_examples")
    
    for format_type in ['jsonl', 'csv', 'tsv', 'pipe']:
        file_path = examples_dir / f"sample.{format_type}"
        
        if file_path.exists():
            try:
                stats = converter.validate_dataset(str(file_path))
                print(f"   {format_type.upper()}:")
                print(f"      Records: {stats['total_records']}")
                print(f"      Valid: {stats['valid_records']}")
                print(f"      Expected values: {stats['expected_values']}")
                print(f"      Has metadata: {stats['has_metadata']}")
            except Exception as e:
                print(f"   ❌ Validation failed for {format_type}: {e}")


def demonstrate_benefits():
    """Demonstrate the benefits of improved formats."""
    print(f"\n💡 Benefits of Improved Formats")
    print("=" * 40)
    
    benefits = {
        "JSONL": [
            "✅ Handles complex data structures",
            "✅ Preserves metadata and timestamps", 
            "✅ Easy to parse programmatically",
            "✅ Supports streaming processing",
            "✅ No escaping issues with special characters"
        ],
        "CSV": [
            "✅ Standard format, widely supported",
            "✅ Proper escaping with quotes",
            "✅ Works with Excel and other tools",
            "✅ Human-readable",
            "⚠️  Requires careful handling of commas/quotes"
        ],
        "TSV": [
            "✅ Tab-separated, less likely to conflict",
            "✅ Better than pipe-delimited",
            "✅ Easy to parse",
            "✅ Good for data with commas",
            "⚠️  Still has escaping issues with tabs"
        ],
        "Parquet": [
            "✅ Binary format, very efficient",
            "✅ Excellent for large datasets",
            "✅ Built-in compression",
            "✅ Schema evolution support",
            "⚠️  Not human-readable"
        ]
    }
    
    for format_name, benefit_list in benefits.items():
        print(f"\n{format_name}:")
        for benefit in benefit_list:
            print(f"   {benefit}")


def cleanup_examples():
    """Clean up example files."""
    import shutil
    examples_dir = Path("format_examples")
    if examples_dir.exists():
        shutil.rmtree(examples_dir)
        print(f"\n🧹 Cleaned up example files")


def main():
    """Run the complete demonstration."""
    print("🚀 Improved Dataset Formats Demo")
    print("=" * 50)
    
    try:
        # Create examples
        examples_dir = demonstrate_formats()
        
        # Show conversion
        demonstrate_conversion()
        
        # Show validation
        demonstrate_validation()
        
        # Show benefits
        demonstrate_benefits()
        
        print(f"\n✨ Demo completed successfully!")
        print(f"   Example files created in: {examples_dir}")
        print(f"   Use 'python migrate_datasets.py --list' to see your datasets")
        print(f"   Use 'python migrate_datasets.py --all' to migrate existing datasets")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        return 1
    
    finally:
        # Ask if user wants to keep examples
        try:
            keep = input("\nKeep example files? (y/n): ").strip().lower()
            if keep != 'y':
                cleanup_examples()
        except KeyboardInterrupt:
            cleanup_examples()
    
    return 0


if __name__ == "__main__":
    exit(main())

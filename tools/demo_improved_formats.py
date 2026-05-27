# Copyright 2025 Andy Ryan
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

#!/usr/bin/env python3
"""
Demo: Improved Dataset Formats Solution

This script demonstrates the complete solution for improved dataset formatting.
It shows the problems with the original format and how the new formats solve them.
"""

import os
import json
from pathlib import Path
from .improved_dataset_converter import DatasetConverter
from .enhanced_dataset_reader import EnhancedDatasetReader


def create_problematic_data():
    """Create data that would break the original pipe-delimited format."""
    return [
        {
            "prompt": "This prompt contains pipes | and quotes \"like this\" and commas, everywhere",
            "expected": "true",
            "id": "problematic_1",
            "metadata": {"difficulty": "high", "special_chars": True}
        },
        {
            "prompt": "Another prompt with\nnewlines and\ttabs and multiple\nlines of text",
            "expected": "false", 
            "id": "problematic_2",
            "metadata": {"multiline": True, "formatting": "complex"}
        },
        {
            "prompt": "Simple prompt without issues",
            "expected": "false",
            "id": "problematic_3", 
            "metadata": {"simple": True}
        }
    ]


def demonstrate_original_problems():
    """Show what would happen with the original pipe-delimited format."""
    print("❌ Problems with Original Pipe-Delimited Format")
    print("=" * 55)
    
    problematic_data = create_problematic_data()
    
    # Show what the original format would look like
    print("\n🔍 Original format would produce:")
    for item in problematic_data:
        # This is how the original format would handle it
        escaped_prompt = item['prompt'].replace('"', '""')
        original_line = f'"{escaped_prompt}"|{item["expected"]}'
        print(f"   {original_line[:80]}{'...' if len(original_line) > 80 else ''}")
    
    print("\n⚠️  Issues:")
    print("   • Pipes in content break parsing")
    print("   • Quotes need manual escaping")
    print("   • Newlines cause parsing issues")
    print("   • No metadata support")
    print("   • Manual string manipulation is error-prone")


def demonstrate_new_solution():
    """Show how the new formats solve these problems."""
    print("\n✅ Solution: Improved Dataset Formats")
    print("=" * 45)
    
    converter = DatasetConverter()
    reader = EnhancedDatasetReader()
    
    # Create demo directory
    demo_dir = Path("format_demo")
    demo_dir.mkdir(exist_ok=True)
    
    problematic_data = create_problematic_data()
    
    # Show JSONL format (recommended)
    print("\n📄 JSONL Format (Recommended):")
    jsonl_file = demo_dir / "demo.jsonl"
    
    with open(jsonl_file, 'w') as f:
        for item in problematic_data:
            json.dump(item, f, ensure_ascii=False)
            f.write('\n')
    
    # Show the content
    with open(jsonl_file, 'r') as f:
        lines = f.readlines()
        for i, line in enumerate(lines[:2]):  # Show first 2 lines
            print(f"   Line {i+1}: {line.strip()[:100]}{'...' if len(line.strip()) > 100 else ''}")
    
    print("\n✅ Benefits:")
    print("   • No escaping issues - JSON handles all special characters")
    print("   • Metadata preserved automatically")
    print("   • Easy to parse programmatically")
    print("   • Streaming processing supported")
    
    # Demonstrate reading back
    print(f"\n📖 Reading back with enhanced reader:")
    try:
        records = reader.read_dataset(str(jsonl_file))
        print(f"   ✅ Successfully loaded {len(records)} records")
        
        for i, record in enumerate(records[:2]):
            print(f"   Record {i+1}:")
            print(f"      Prompt: {record.prompt[:50]}...")
            print(f"      Expected: {record.expected}")
            print(f"      Metadata: {record.metadata}")
    except Exception as e:
        print(f"   ❌ Error: {e}")


def demonstrate_migration():
    """Show how to migrate existing datasets."""
    print(f"\n🔄 Migration Process")
    print("=" * 25)
    
    # Create a sample pipe-delimited file (simulating existing data)
    demo_dir = Path("format_demo")
    pipe_file = demo_dir / "legacy_data.pipe"
    
    with open(pipe_file, 'w') as f:
        f.write('"Simple prompt"|false\n')
        f.write('"Prompt with, commas"|true\n')
        f.write('"Prompt with pipes | and quotes"|false\n')
    
    print(f"📁 Created legacy dataset: {pipe_file}")
    
    # Show migration
    converter = DatasetConverter()
    
    try:
        # Convert to JSONL
        jsonl_output = demo_dir / "migrated_data.jsonl"
        converter.convert_dataset(str(pipe_file), str(jsonl_output), 'pipe', 'jsonl')
        print(f"✅ Migrated to JSONL: {jsonl_output}")
        
        # Validate the migration
        stats = converter.validate_dataset(str(jsonl_output))
        print(f"   Records: {stats['total_records']}")
        print(f"   Valid: {stats['valid_records']}")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")


def demonstrate_usage():
    """Show how to use the new formats with existing code."""
    print(f"\n💻 Usage with Existing Code")
    print("=" * 35)
    
    print("The enhanced dataset reader maintains full backward compatibility:")
    print("   • No changes needed to existing prompt evaluator scripts")
    print("   • Automatically detects dataset format")
    print("   • Works with both old and new formats")
    
    print(f"\nExample usage:")
    print(f"   # Old way (still works)")
    print(f"   python prompt_evaluator.py --input datasets/my_data.csv")
    print(f"   ")
    print(f"   # New way (better format)")
    print(f"   python prompt_evaluator.py --input datasets/my_data.jsonl")
    print(f"   ")
    print(f"   # Migration")
    print(f"   python migrate_datasets.py --all --output-format jsonl")


def show_format_comparison():
    """Show a comparison of different formats."""
    print(f"\n📊 Format Comparison")
    print("=" * 25)
    
    comparison_data = [
        ("Format", "Readable", "Special Chars", "Metadata", "Size", "Performance"),
        ("-" * 6, "-" * 8, "-" * 13, "-" * 8, "-" * 4, "-" * 10),
        ("JSONL", "✅", "✅", "✅", "Medium", "Fast"),
        ("CSV", "✅", "⚠️", "✅", "Small", "Fast"),
        ("TSV", "✅", "⚠️", "✅", "Small", "Fast"),
        ("Pipe", "✅", "❌", "❌", "Small", "Slow"),
        ("Parquet", "❌", "✅", "✅", "Very Small", "Very Fast")
    ]
    
    for row in comparison_data:
        print(f"   {row[0]:<8} {row[1]:<8} {row[2]:<13} {row[3]:<8} {row[4]:<8} {row[5]}")


def cleanup_demo():
    """Clean up demo files."""
    import shutil
    demo_dir = Path("format_demo")
    if demo_dir.exists():
        shutil.rmtree(demo_dir)
        print(f"\n🧹 Cleaned up demo files")


def main():
    """Run the complete demonstration."""
    print("🚀 Improved Dataset Formats - Complete Solution")
    print("=" * 60)
    
    try:
        # Show the problems
        demonstrate_original_problems()
        
        # Show the solution
        demonstrate_new_solution()
        
        # Show migration
        demonstrate_migration()
        
        # Show usage
        demonstrate_usage()
        
        # Show comparison
        show_format_comparison()
        
        print(f"\n🎉 Complete Solution Summary:")
        print(f"   ✅ Multiple format support (JSONL, CSV, TSV, Parquet)")
        print(f"   ✅ Proper escaping and metadata handling")
        print(f"   ✅ Backward compatibility maintained")
        print(f"   ✅ Migration tools provided")
        print(f"   ✅ Enhanced dataset reader")
        print(f"   ✅ No changes needed to existing code")
        
        print(f"\n📚 Next Steps:")
        print(f"   1. Run: python migrate_datasets.py --list")
        print(f"   2. Run: python migrate_datasets.py --all --output-format jsonl")
        print(f"   3. Continue using your existing scripts - no changes needed!")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        return 1
    
    finally:
        # Ask if user wants to keep demo files
        try:
            keep = input("\nKeep demo files? (y/n): ").strip().lower()
            if keep != 'y':
                cleanup_demo()
        except KeyboardInterrupt:
            cleanup_demo()
    
    return 0


if __name__ == "__main__":
    exit(main())

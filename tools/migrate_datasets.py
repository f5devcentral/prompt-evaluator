#!/usr/bin/env python3
"""
Dataset Migration Tool

This script helps migrate existing pipe-delimited datasets to better formats.
It provides batch conversion capabilities and validation.
"""

import os
import json
import argparse
from pathlib import Path
from typing import List, Dict, Any
from .improved_dataset_converter import DatasetConverter


class DatasetMigrator:
    """Handles migration of datasets from legacy formats to improved formats."""
    
    def __init__(self):
        self.converter = DatasetConverter()
        self.datasets_dir = Path("datasets")
    
    def find_datasets(self, directory: str = "datasets") -> List[Dict[str, Any]]:
        """Find all datasets in the specified directory."""
        datasets = []
        datasets_path = Path(directory)
        
        if not datasets_path.exists():
            print(f"Directory {directory} does not exist")
            return datasets
        
        for file_path in datasets_path.glob("*.csv"):
            if file_path.is_file():
                # Try to detect format
                format_type = self.converter.detect_format(str(file_path))
                
                datasets.append({
                    'path': str(file_path),
                    'name': file_path.name,
                    'size': file_path.stat().st_size,
                    'format': format_type,
                    'needs_migration': format_type == 'pipe'
                })
        
        return datasets
    
    def migrate_dataset(self, input_file: str, output_format: str = 'jsonl', 
                      backup: bool = True) -> Dict[str, Any]:
        """Migrate a single dataset to a new format."""
        input_path = Path(input_file)
        
        if not input_path.exists():
            return {'error': f'Input file not found: {input_file}'}
        
        # Create backup if requested
        if backup:
            backup_path = input_path.with_suffix(f'.backup{input_path.suffix}')
            if not backup_path.exists():
                import shutil
                shutil.copy2(input_path, backup_path)
                print(f"Created backup: {backup_path}")
        
        # Generate output filename
        output_file = input_path.with_suffix(f'.{output_format}')
        
        try:
            # Convert the dataset
            result_path = self.converter.convert_dataset(
                str(input_path),
                str(output_file),
                input_format='pipe',
                output_format=output_format
            )
            
            # Validate the converted dataset
            stats = self.converter.validate_dataset(result_path)
            
            return {
                'success': True,
                'input_file': str(input_path),
                'output_file': result_path,
                'format': output_format,
                'stats': stats
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'input_file': str(input_path)
            }
    
    def migrate_all(self, output_format: str = 'jsonl', backup: bool = True) -> Dict[str, Any]:
        """Migrate all datasets in the datasets directory."""
        datasets = self.find_datasets()
        
        if not datasets:
            return {'error': 'No datasets found'}
        
        results = {
            'total_datasets': len(datasets),
            'migrated': 0,
            'failed': 0,
            'skipped': 0,
            'results': []
        }
        
        for dataset in datasets:
            if not dataset['needs_migration']:
                print(f"Skipping {dataset['name']} (already in {dataset['format']} format)")
                results['skipped'] += 1
                continue
            
            print(f"\nMigrating {dataset['name']}...")
            result = self.migrate_dataset(dataset['path'], output_format, backup)
            results['results'].append(result)
            
            if result.get('success'):
                results['migrated'] += 1
                print(f"✅ Successfully migrated to {result['output_file']}")
                print(f"   Records: {result['stats']['total_records']}")
            else:
                results['failed'] += 1
                print(f"❌ Failed to migrate: {result.get('error', 'Unknown error')}")
        
        return results
    
    def create_comparison_report(self, original_file: str, converted_file: str) -> Dict[str, Any]:
        """Create a detailed comparison report between original and converted datasets."""
        try:
            # Read both datasets
            original_records = self.converter.read_dataset(original_file, 'pipe')
            converted_records = self.converter.read_dataset(converted_file)
            
            # Compare
            comparison = {
                'original_file': original_file,
                'converted_file': converted_file,
                'original_count': len(original_records),
                'converted_count': len(converted_records),
                'count_match': len(original_records) == len(converted_records),
                'sample_comparison': []
            }
            
            # Compare first few records
            for i in range(min(3, len(original_records), len(converted_records))):
                orig = original_records[i]
                conv = converted_records[i]
                
                comparison['sample_comparison'].append({
                    'index': i,
                    'original_prompt': orig.prompt[:100] + '...' if len(orig.prompt) > 100 else orig.prompt,
                    'converted_prompt': conv.prompt[:100] + '...' if len(conv.prompt) > 100 else conv.prompt,
                    'prompt_match': orig.prompt == conv.prompt,
                    'expected_match': orig.expected == conv.expected
                })
            
            return comparison
            
        except Exception as e:
            return {'error': str(e)}


def main():
    parser = argparse.ArgumentParser(description='Migrate datasets to improved formats')
    parser.add_argument('--input', '-i', help='Input dataset file (migrate single file)')
    parser.add_argument('--output-format', choices=['jsonl', 'csv', 'tsv', 'parquet'], 
                       default='jsonl', help='Output format (default: jsonl)')
    parser.add_argument('--all', action='store_true', help='Migrate all datasets in datasets/ directory')
    parser.add_argument('--no-backup', action='store_true', help='Skip creating backup files')
    parser.add_argument('--compare', action='store_true', help='Create comparison report')
    parser.add_argument('--list', action='store_true', help='List all datasets and their formats')
    
    args = parser.parse_args()
    
    migrator = DatasetMigrator()
    
    if args.list:
        print("📊 Dataset Analysis")
        print("=" * 50)
        
        datasets = migrator.find_datasets()
        if not datasets:
            print("No datasets found in datasets/ directory")
            return 0
        
        for dataset in datasets:
            status = "✅ Modern" if not dataset['needs_migration'] else "⚠️  Legacy"
            print(f"{status} {dataset['name']} ({dataset['format']}) - {dataset['size']:,} bytes")
        
        return 0
    
    if args.all:
        print("🔄 Migrating all datasets...")
        results = migrator.migrate_all(args.output_format, not args.no_backup)
        
        print(f"\n📈 Migration Summary:")
        print(f"   Total datasets: {results['total_datasets']}")
        print(f"   Migrated: {results['migrated']}")
        print(f"   Failed: {results['failed']}")
        print(f"   Skipped: {results['skipped']}")
        
        if results['failed'] > 0:
            print(f"\n❌ Failed migrations:")
            for result in results['results']:
                if not result.get('success'):
                    print(f"   {result['input_file']}: {result.get('error', 'Unknown error')}")
        
        return 0 if results['failed'] == 0 else 1
    
    elif args.input:
        print(f"🔄 Migrating {args.input}...")
        result = migrator.migrate_dataset(args.input, args.output_format, not args.no_backup)
        
        if result.get('success'):
            print(f"✅ Successfully migrated to {result['output_file']}")
            print(f"   Records: {result['stats']['total_records']}")
            
            if args.compare:
                print(f"\n📊 Comparison Report:")
                comparison = migrator.create_comparison_report(args.input, result['output_file'])
                print(json.dumps(comparison, indent=2))
        else:
            print(f"❌ Migration failed: {result.get('error', 'Unknown error')}")
            return 1
        
        return 0
    
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    exit(main())

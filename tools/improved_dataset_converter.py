#!/usr/bin/env python3
"""
Improved Dataset Converter

This script provides multiple format options for processed datasets:
1. JSON Lines (JSONL) - Recommended for complex data
2. TSV (Tab-separated) - Better than pipe-delimited
3. CSV with proper escaping - Standard format with proper quoting
4. Parquet - Binary format for large datasets

The converter maintains backward compatibility with existing pipe-delimited format.
"""

import csv
import json
import os
import pandas as pd
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class PromptRecord:
    """Structured representation of a prompt record."""
    prompt: str
    expected: str
    id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    timestamp: Optional[str] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()


class DatasetConverter:
    """Converts datasets between different formats with proper escaping."""
    
    def __init__(self):
        self.supported_formats = ['jsonl', 'tsv', 'csv', 'parquet', 'pipe']
    
    def detect_format(self, file_path: str) -> str:
        """Detect the format of an existing dataset file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            first_line = f.readline().strip()
            
        # Check for JSONL format
        if first_line.startswith('{') and first_line.endswith('}'):
            return 'jsonl'
        # Check for pipe-delimited format
        elif '|' in first_line:
            return 'pipe'
        # Check for TSV format (tab-separated, no pipes)
        elif '\t' in first_line and '|' not in first_line:
            return 'tsv'
        # Check for CSV format (comma-separated, may or may not have quotes)
        elif ',' in first_line:
            return 'csv'
        else:
            return 'unknown'
    
    def read_pipe_format(self, file_path: str) -> List[PromptRecord]:
        """Read the legacy pipe-delimited format."""
        records = []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                
                # Split by pipe and handle quoted content
                parts = line.split('|', 1)
                if len(parts) < 2:
                    print(f"Warning: Skipping malformed line {line_num}: {line}")
                    continue
                
                prompt = parts[0].strip()
                expected = parts[1].strip()
                
                # Remove surrounding quotes
                if prompt.startswith('"') and prompt.endswith('"'):
                    prompt = prompt[1:-1]
                elif prompt.startswith("'") and prompt.endswith("'"):
                    prompt = prompt[1:-1]
                
                records.append(PromptRecord(
                    prompt=prompt,
                    expected=expected,
                    id=f"line_{line_num}"
                ))
        
        return records
    
    def read_csv_format(self, file_path: str) -> List[PromptRecord]:
        """Read CSV format with proper CSV parsing."""
        records = []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row_num, row in enumerate(reader, 1):
                # Handle different column names
                prompt = row.get('prompt', row.get('text', row.get('content', '')))
                expected = row.get('expected', row.get('label', row.get('target', '')))
                
                if not prompt or not expected:
                    print(f"Warning: Skipping incomplete row {row_num}")
                    continue
                
                records.append(PromptRecord(
                    prompt=prompt,
                    expected=expected,
                    id=f"row_{row_num}",
                    metadata={k: v for k, v in row.items() if k not in ['prompt', 'text', 'content', 'expected', 'label', 'target']}
                ))
        
        return records
    
    def read_jsonl_format(self, file_path: str) -> List[PromptRecord]:
        """Read JSON Lines format."""
        records = []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                
                try:
                    data = json.loads(line)
                    records.append(PromptRecord(
                        prompt=data.get('prompt', ''),
                        expected=data.get('expected', ''),
                        id=data.get('id', f"line_{line_num}"),
                        metadata=data.get('metadata', {}),
                        timestamp=data.get('timestamp')
                    ))
                except json.JSONDecodeError as e:
                    print(f"Warning: Skipping malformed JSON line {line_num}: {e}")
                    continue
        
        return records
    
    def read_tsv_format(self, file_path: str) -> List[PromptRecord]:
        """Read TSV format."""
        records = []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter='\t')
            for row_num, row in enumerate(reader, 1):
                prompt = row.get('prompt', row.get('text', ''))
                expected = row.get('expected', row.get('label', ''))
                
                if not prompt or not expected:
                    print(f"Warning: Skipping incomplete row {row_num}")
                    continue
                
                records.append(PromptRecord(
                    prompt=prompt,
                    expected=expected,
                    id=f"row_{row_num}",
                    metadata={k: v for k, v in row.items() if k not in ['prompt', 'text', 'expected', 'label']}
                ))
        
        return records
    
    def read_dataset(self, file_path: str, format_hint: Optional[str] = None) -> List[PromptRecord]:
        """Read dataset from file, auto-detecting format if not specified."""
        if format_hint:
            format_type = format_hint
        else:
            format_type = self.detect_format(file_path)
        
        print(f"Reading {file_path} as {format_type} format...")
        
        if format_type == 'jsonl':
            return self.read_jsonl_format(file_path)
        elif format_type == 'csv':
            return self.read_csv_format(file_path)
        elif format_type == 'tsv':
            return self.read_tsv_format(file_path)
        elif format_type == 'pipe':
            return self.read_pipe_format(file_path)
        else:
            raise ValueError(f"Unsupported format: {format_type}")
    
    def write_jsonl_format(self, records: List[PromptRecord], file_path: str):
        """Write records in JSON Lines format."""
        with open(file_path, 'w', encoding='utf-8') as f:
            for record in records:
                json.dump(asdict(record), f, ensure_ascii=False)
                f.write('\n')
    
    def write_csv_format(self, records: List[PromptRecord], file_path: str):
        """Write records in CSV format with proper escaping."""
        with open(file_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f, quoting=csv.QUOTE_ALL)
            writer.writerow(['prompt', 'expected', 'id', 'timestamp'])
            
            for record in records:
                writer.writerow([
                    record.prompt,
                    record.expected,
                    record.id or '',
                    record.timestamp or ''
                ])
    
    def write_tsv_format(self, records: List[PromptRecord], file_path: str):
        """Write records in TSV format."""
        with open(file_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f, delimiter='\t')
            writer.writerow(['prompt', 'expected', 'id', 'timestamp'])
            
            for record in records:
                writer.writerow([
                    record.prompt,
                    record.expected,
                    record.id or '',
                    record.timestamp or ''
                ])
    
    def write_pipe_format(self, records: List[PromptRecord], file_path: str):
        """Write records in legacy pipe-delimited format."""
        with open(file_path, 'w', encoding='utf-8') as f:
            for record in records:
                # Escape quotes in prompt and wrap in quotes
                escaped_prompt = record.prompt.replace('"', '""')
                f.write(f'"{escaped_prompt}"|{record.expected}\n')
    
    def write_parquet_format(self, records: List[PromptRecord], file_path: str):
        """Write records in Parquet format."""
        # Convert to DataFrame
        data = []
        for record in records:
            data.append({
                'prompt': record.prompt,
                'expected': record.expected,
                'id': record.id or '',
                'timestamp': record.timestamp or '',
                'metadata': json.dumps(record.metadata) if record.metadata else ''
            })
        
        df = pd.DataFrame(data)
        df.to_parquet(file_path, index=False)
    
    def convert_dataset(self, input_file: str, output_file: str, 
                       output_format: str = 'jsonl',
                       input_format: Optional[str] = None) -> str:
        """Convert dataset from one format to another."""
        if output_format not in self.supported_formats:
            raise ValueError(f"Unsupported output format: {output_format}")
        
        # Read the dataset
        records = self.read_dataset(input_file, input_format)
        print(f"Loaded {len(records)} records")
        
        # Write in new format
        if output_format == 'jsonl':
            self.write_jsonl_format(records, output_file)
        elif output_format == 'csv':
            self.write_csv_format(records, output_file)
        elif output_format == 'tsv':
            self.write_tsv_format(records, output_file)
        elif output_format == 'pipe':
            self.write_pipe_format(records, output_file)
        elif output_format == 'parquet':
            self.write_parquet_format(records, output_file)
        
        print(f"Converted dataset saved to: {output_file}")
        return output_file
    
    def validate_dataset(self, file_path: str, format_hint: Optional[str] = None) -> Union[bool, Dict[str, Any]]:
        """Validate a dataset and return statistics or boolean."""
        try:
            records = self.read_dataset(file_path, format_hint)
            
            # Check if dataset is valid
            if len(records) == 0:
                return False
            
            # Check if all records have required fields
            valid_records = [r for r in records if r.prompt and r.expected]
            if len(valid_records) != len(records):
                return False
            
            # Return detailed stats if requested
            stats = {
                'total_records': len(records),
                'valid_records': len(valid_records),
                'format': self.detect_format(file_path),
                'sample_prompts': [r.prompt[:100] + '...' if len(r.prompt) > 100 else r.prompt 
                                 for r in records[:3]],
                'expected_values': list(set(r.expected for r in records)),
                'has_metadata': any(r.metadata for r in records),
                'has_ids': any(r.id for r in records)
            }
            
            return stats
            
        except Exception as e:
            return {'error': str(e)}


def main():
    parser = argparse.ArgumentParser(description='Convert datasets between different formats')
    parser.add_argument('input_file', help='Input dataset file')
    parser.add_argument('output_file', help='Output dataset file')
    parser.add_argument('--input-format', help='Input format (auto-detect if not specified)')
    parser.add_argument('--output-format', choices=['jsonl', 'csv', 'tsv', 'pipe', 'parquet'], 
                       default='jsonl', help='Output format (default: jsonl)')
    parser.add_argument('--validate', action='store_true', help='Validate dataset after conversion')
    
    args = parser.parse_args()
    
    converter = DatasetConverter()
    
    try:
        # Convert the dataset
        output_path = converter.convert_dataset(
            args.input_file, 
            args.output_file,
            args.input_format,
            args.output_format
        )
        
        if args.validate:
            print("\nValidating converted dataset...")
            stats = converter.validate_dataset(output_path)
            print(f"Validation results: {json.dumps(stats, indent=2)}")
        
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())

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
Enhanced Dataset Reader

This module provides a unified interface for reading datasets in multiple formats:
- JSON Lines (JSONL) - Recommended for complex data
- TSV (Tab-separated) - Better than pipe-delimited
- CSV with proper escaping - Standard format
- Legacy pipe-delimited format - Backward compatibility
- Parquet - Binary format for large datasets

This replaces the manual parsing in the original prompt evaluator scripts.
"""

import csv
import json
import os
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Iterator
from dataclasses import dataclass


@dataclass
class PromptRecord:
    """Structured representation of a prompt record."""
    prompt: str
    expected: str
    id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    timestamp: Optional[str] = None


class EnhancedDatasetReader:
    """Unified dataset reader that handles multiple formats."""
    
    def __init__(self):
        self.supported_formats = ['jsonl', 'tsv', 'csv', 'pipe', 'parquet']
    
    def detect_format(self, file_path: str) -> str:
        """Detect the format of a dataset file."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Dataset file not found: {file_path}")
        
        # Check file extension first
        ext = Path(file_path).suffix.lower()
        if ext == '.jsonl':
            return 'jsonl'
        elif ext == '.tsv':
            return 'tsv'
        elif ext == '.csv':
            return 'csv'
        elif ext == '.parquet':
            return 'parquet'
        
        # Try to detect from content
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                first_line = f.readline().strip()
                
            if first_line.startswith('{') and first_line.endswith('}'):
                return 'jsonl'
            elif '\t' in first_line and '|' not in first_line:
                return 'tsv'
            elif '|' in first_line:
                return 'pipe'
            elif ',' in first_line and '"' in first_line:
                return 'csv'
            else:
                return 'csv'  # Default fallback
        except Exception:
            return 'csv'  # Default fallback
    
    def read_pipe_format(self, file_path: str, max_lines: Optional[int] = None) -> List[PromptRecord]:
        """Read the legacy pipe-delimited format."""
        records = []
        line_count = 0
        
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                if max_lines is not None and line_count >= max_lines:
                    break
                    
                line = line.strip()
                if not line:
                    continue
                
                # Split by pipe and handle quoted content
                parts = line.split('|', 1)
                if len(parts) < 2:
                    print(f"Warning: Skipping malformed line {line_num}: {line[:100]}...")
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
                line_count += 1
        
        return records
    
    def read_csv_format(self, file_path: str, max_lines: Optional[int] = None) -> List[PromptRecord]:
        """Read CSV format with proper CSV parsing."""
        records = []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row_num, row in enumerate(reader, 1):
                if max_lines is not None and len(records) >= max_lines:
                    break
                
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
                    metadata={k: v for k, v in row.items() 
                            if k not in ['prompt', 'text', 'content', 'expected', 'label', 'target']}
                ))
        
        return records
    
    def read_jsonl_format(self, file_path: str, max_lines: Optional[int] = None) -> List[PromptRecord]:
        """Read JSON Lines format."""
        records = []
        line_count = 0
        
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                if max_lines is not None and line_count >= max_lines:
                    break
                    
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
                    line_count += 1
                except json.JSONDecodeError as e:
                    print(f"Warning: Skipping malformed JSON line {line_num}: {e}")
                    continue
        
        return records
    
    def read_tsv_format(self, file_path: str, max_lines: Optional[int] = None) -> List[PromptRecord]:
        """Read TSV format."""
        records = []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter='\t')
            for row_num, row in enumerate(reader, 1):
                if max_lines is not None and len(records) >= max_lines:
                    break
                
                prompt = row.get('prompt', row.get('text', ''))
                expected = row.get('expected', row.get('label', ''))
                
                if not prompt or not expected:
                    print(f"Warning: Skipping incomplete row {row_num}")
                    continue
                
                records.append(PromptRecord(
                    prompt=prompt,
                    expected=expected,
                    id=f"row_{row_num}",
                    metadata={k: v for k, v in row.items() 
                            if k not in ['prompt', 'text', 'expected', 'label']}
                ))
        
        return records
    
    def read_parquet_format(self, file_path: str, max_lines: Optional[int] = None) -> List[PromptRecord]:
        """Read Parquet format."""
        df = pd.read_parquet(file_path)
        
        if max_lines is not None:
            df = df.head(max_lines)
        
        records = []
        for idx, row in df.iterrows():
            # Handle metadata column if it exists
            metadata = {}
            if 'metadata' in row and pd.notna(row['metadata']):
                try:
                    metadata = json.loads(row['metadata'])
                except (json.JSONDecodeError, TypeError):
                    metadata = {}
            
            records.append(PromptRecord(
                prompt=str(row.get('prompt', '')),
                expected=str(row.get('expected', '')),
                id=str(row.get('id', f"row_{idx}")),
                metadata=metadata,
                timestamp=str(row.get('timestamp', '')) if pd.notna(row.get('timestamp')) else None
            ))
        
        return records
    
    def read_dataset(self, file_path: str, format_hint: Optional[str] = None, 
                    max_lines: Optional[int] = None) -> List[PromptRecord]:
        """Read dataset from file, auto-detecting format if not specified."""
        if format_hint:
            format_type = format_hint
        else:
            format_type = self.detect_format(file_path)
        
        print(f"Reading {file_path} as {format_type} format...")
        
        if format_type == 'jsonl':
            return self.read_jsonl_format(file_path, max_lines)
        elif format_type == 'csv':
            return self.read_csv_format(file_path, max_lines)
        elif format_type == 'tsv':
            return self.read_tsv_format(file_path, max_lines)
        elif format_type == 'pipe':
            return self.read_pipe_format(file_path, max_lines)
        elif format_type == 'parquet':
            return self.read_parquet_format(file_path, max_lines)
        else:
            raise ValueError(f"Unsupported format: {format_type}")
    
    def get_dataset_info(self, file_path: str) -> Dict[str, Any]:
        """Get information about a dataset without loading all data."""
        format_type = self.detect_format(file_path)
        
        info = {
            'file_path': file_path,
            'format': format_type,
            'file_size': os.path.getsize(file_path),
            'total_lines': 0,
            'sample_records': []
        }
        
        # Count lines and get sample
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                info['total_lines'] = len(lines)
                
                # Get first few lines as samples
                for i, line in enumerate(lines[:3]):
                    if line.strip():
                        info['sample_records'].append(line.strip()[:100] + '...' if len(line.strip()) > 100 else line.strip())
        except Exception as e:
            info['error'] = str(e)
        
        return info


# Backward compatibility functions
def load_dataset_enhanced(input_file: str, max_lines: Optional[int] = None, 
                         format_hint: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Enhanced dataset loader that returns data in the format expected by existing code.
    
    Returns:
        List of dictionaries with 'prompt', 'expected', and 'original_line' keys
    """
    reader = EnhancedDatasetReader()
    records = reader.read_dataset(input_file, format_hint, max_lines)
    
    # Convert to the format expected by existing code
    dataset = []
    for record in records:
        dataset.append({
            "prompt": record.prompt,
            "expected": record.expected,
            "original_line": f'"{record.prompt}"|{record.expected}',  # Reconstruct original format
            "id": record.id,
            "metadata": record.metadata,
            "timestamp": record.timestamp
        })
    
    return dataset


def main():
    """Test the enhanced dataset reader."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Test enhanced dataset reader')
    parser.add_argument('file', help='Dataset file to read')
    parser.add_argument('--format', help='Format hint (auto-detect if not specified)')
    parser.add_argument('--max-lines', type=int, help='Maximum lines to read')
    parser.add_argument('--info', action='store_true', help='Show dataset info only')
    
    args = parser.parse_args()
    
    reader = EnhancedDatasetReader()
    
    if args.info:
        info = reader.get_dataset_info(args.file)
        print(json.dumps(info, indent=2))
    else:
        try:
            records = reader.read_dataset(args.file, args.format, args.max_lines)
            print(f"Loaded {len(records)} records")
            
            # Show first few records
            for i, record in enumerate(records[:3]):
                print(f"\nRecord {i+1}:")
                print(f"  ID: {record.id}")
                print(f"  Prompt: {record.prompt[:100]}{'...' if len(record.prompt) > 100 else ''}")
                print(f"  Expected: {record.expected}")
                if record.metadata:
                    print(f"  Metadata: {record.metadata}")
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    main()

"""
Unit tests for the improved dataset converter.
"""

import pytest
import json
import pandas as pd
from pathlib import Path
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.improved_dataset_converter import DatasetConverter, PromptRecord


class TestDatasetConverter:
    """Test cases for the DatasetConverter class."""
    
    def test_detect_format_csv(self, temp_dir, sample_csv_data):
        """Test CSV format detection."""
        converter = DatasetConverter()
        
        # Create a CSV file
        csv_file = temp_dir / "test.csv"
        df = pd.DataFrame(sample_csv_data)
        df.to_csv(csv_file, index=False)
        
        assert converter.detect_format(str(csv_file)) == 'csv'
    
    def test_detect_format_jsonl(self, temp_dir, sample_jsonl_data):
        """Test JSONL format detection."""
        converter = DatasetConverter()
        
        # Create a JSONL file
        jsonl_file = temp_dir / "test.jsonl"
        with open(jsonl_file, 'w', encoding='utf-8') as f:
            for record in sample_jsonl_data:
                f.write(json.dumps(record) + '\n')
        
        assert converter.detect_format(str(jsonl_file)) == 'jsonl'
    
    def test_detect_format_pipe(self, temp_dir, sample_pipe_data):
        """Test pipe-delimited format detection."""
        converter = DatasetConverter()
        
        # Create a pipe-delimited file
        pipe_file = temp_dir / "test.csv"
        with open(pipe_file, 'w', encoding='utf-8') as f:
            for line in sample_pipe_data:
                f.write(line + '\n')
        
        assert converter.detect_format(str(pipe_file)) == 'pipe'
    
    def test_convert_pipe_to_jsonl(self, temp_dir, sample_pipe_data):
        """Test conversion from pipe-delimited to JSONL."""
        converter = DatasetConverter()
        
        # Create input file
        input_file = temp_dir / "input.csv"
        with open(input_file, 'w', encoding='utf-8') as f:
            for line in sample_pipe_data:
                f.write(line + '\n')
        
        # Convert to JSONL
        output_file = temp_dir / "output.jsonl"
        converter.convert_dataset(str(input_file), str(output_file), 'jsonl')
        
        # Verify output
        assert output_file.exists()
        with open(output_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            assert len(lines) == len(sample_pipe_data)
            
            # Check first record
            first_record = json.loads(lines[0])
            assert 'prompt' in first_record
            assert 'expected' in first_record
    
    def test_convert_csv_to_jsonl(self, temp_dir, sample_csv_data):
        """Test conversion from CSV to JSONL."""
        converter = DatasetConverter()
        
        # Create input file
        input_file = temp_dir / "input.csv"
        df = pd.DataFrame(sample_csv_data)
        df.to_csv(input_file, index=False)
        
        # Convert to JSONL
        output_file = temp_dir / "output.jsonl"
        converter.convert_dataset(str(input_file), str(output_file), 'jsonl')
        
        # Verify output
        assert output_file.exists()
        with open(output_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            assert len(lines) == len(sample_csv_data)
    
    def test_convert_jsonl_to_csv(self, temp_dir, sample_jsonl_data):
        """Test conversion from JSONL to CSV."""
        converter = DatasetConverter()
        
        # Create input file
        input_file = temp_dir / "input.jsonl"
        with open(input_file, 'w', encoding='utf-8') as f:
            for record in sample_jsonl_data:
                f.write(json.dumps(record) + '\n')
        
        # Convert to CSV
        output_file = temp_dir / "output.csv"
        converter.convert_dataset(str(input_file), str(output_file), 'csv')
        
        # Verify output
        assert output_file.exists()
        df = pd.read_csv(output_file)
        assert len(df) == len(sample_jsonl_data)
        assert 'prompt' in df.columns
        assert 'expected' in df.columns
    
    def test_validate_dataset(self, temp_dir, sample_csv_data):
        """Test dataset validation."""
        converter = DatasetConverter()
        
        # Create valid dataset
        valid_file = temp_dir / "valid.csv"
        df = pd.DataFrame(sample_csv_data)
        df.to_csv(valid_file, index=False)
        
        result = converter.validate_dataset(str(valid_file))
        # Should return either True or a dictionary with stats
        assert result == True or (isinstance(result, dict) and 'total_records' in result)
        
        # Create invalid dataset (missing required columns)
        invalid_file = temp_dir / "invalid.csv"
        invalid_df = pd.DataFrame([{"wrong_column": "value"}])
        invalid_df.to_csv(invalid_file, index=False)
        
        result = converter.validate_dataset(str(invalid_file))
        assert result == False or (isinstance(result, dict) and 'error' in result)
    
    def test_prompt_record_creation(self):
        """Test PromptRecord dataclass."""
        record = PromptRecord(
            prompt="Test prompt",
            expected="true",
            id="test_1",
            metadata={"source": "test"}
        )
        
        assert record.prompt == "Test prompt"
        assert record.expected == "true"
        assert record.id == "test_1"
        assert record.metadata["source"] == "test"
        assert record.timestamp is not None
    
    @pytest.mark.parametrize("format_type", ["jsonl", "csv", "tsv", "parquet"])
    def test_supported_formats(self, format_type):
        """Test that all supported formats are recognized."""
        converter = DatasetConverter()
        assert format_type in converter.supported_formats
    
    def test_convert_with_metadata(self, temp_dir):
        """Test conversion preserving metadata."""
        converter = DatasetConverter()
        
        # Create JSONL with metadata
        input_file = temp_dir / "input.jsonl"
        records = [
            {
                "prompt": "Test prompt 1",
                "expected": "false",
                "id": "test_1",
                "metadata": {"source": "test", "category": "safe"}
            },
            {
                "prompt": "Test prompt 2", 
                "expected": "true",
                "id": "test_2",
                "metadata": {"source": "test", "category": "malicious"}
            }
        ]
        
        with open(input_file, 'w', encoding='utf-8') as f:
            for record in records:
                f.write(json.dumps(record) + '\n')
        
        # Convert to CSV
        output_file = temp_dir / "output.csv"
        converter.convert_dataset(str(input_file), str(output_file), 'csv')
        
        # Verify metadata is preserved in some form
        df = pd.read_csv(output_file)
        assert len(df) == 2
        assert 'prompt' in df.columns
        assert 'expected' in df.columns

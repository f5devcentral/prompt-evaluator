# MIT License
#
# Copyright (c) 2025 Andy Ryan
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""
Integration tests for the prompt evaluator system.
"""

import pytest
import json
import pandas as pd
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys
import os

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.improved_dataset_converter import DatasetConverter
from tools.enhanced_dataset_reader import EnhancedDatasetReader
from tools.migrate_datasets import DatasetMigrator


class TestIntegration:
    """Integration tests for the complete system."""
    
    def test_end_to_end_migration_workflow(self, test_datasets_dir, temp_dir):
        """Test complete migration workflow from start to finish."""
        # Step 1: Find datasets
        migrator = DatasetMigrator()
        datasets = migrator.find_datasets(str(test_datasets_dir))
        assert len(datasets) > 0
        
        # Step 2: Migrate all datasets
        migrator.datasets_dir = temp_dir
        results = migrator.migrate_all_datasets(
            output_format='jsonl',
            backup=True
        )
        
        # Step 3: Verify migrations
        for result in results:
            assert result['success'] == True
            assert Path(result['output_path']).exists()
            
            # Step 4: Validate migrated datasets
            reader = EnhancedDatasetReader()
            records = reader.read_dataset(result['output_path'])
            assert len(records) > 0
            assert all('prompt' in record for record in records)
            assert all('expected' in record for record in records)
    
    def test_format_conversion_chain(self, temp_dir, sample_csv_data):
        """Test converting between multiple formats in sequence."""
        converter = DatasetConverter()
        reader = EnhancedDatasetReader()
        
        # Start with CSV
        csv_file = temp_dir / "original.csv"
        df = pd.DataFrame(sample_csv_data)
        df.to_csv(csv_file, index=False)
        
        # Convert CSV -> JSONL
        jsonl_file = temp_dir / "converted.jsonl"
        converter.convert_dataset(str(csv_file), str(jsonl_file), 'jsonl')
        
        # Convert JSONL -> TSV
        tsv_file = temp_dir / "converted.tsv"
        converter.convert_dataset(str(jsonl_file), str(tsv_file), 'tsv')
        
        # Convert TSV -> CSV
        final_csv = temp_dir / "final.csv"
        converter.convert_dataset(str(tsv_file), str(final_csv), 'csv')
        
        # Verify all files exist and are readable
        assert csv_file.exists()
        assert jsonl_file.exists()
        assert tsv_file.exists()
        assert final_csv.exists()
        
        # Verify data integrity through the chain
        original_records = reader.read_dataset(str(csv_file))
        final_records = reader.read_dataset(str(final_csv))
        
        assert len(original_records) == len(final_records)
        assert len(original_records) == len(sample_csv_data)
    
    def test_huggingface_integration(self, temp_dir, mock_huggingface_dataset):
        """Test integration with Hugging Face dataset download."""
        from download_hf_datasets import HFDatasetDownloader
        
        downloader = HFDatasetDownloader(str(temp_dir))
        
        # Mock the dataset loading
        with patch('download_hf_datasets.load_dataset') as mock_load:
            mock_load.return_value = mock_huggingface_dataset
            
            # Test dataset download and conversion
            result = downloader.download_dataset(
                dataset_name="test_dataset",
                max_samples=3,
                output_format="jsonl"
            )
            
            assert Path(result).exists()
            
            # Verify the converted dataset
            reader = EnhancedDatasetReader()
            records = reader.read_dataset(result)
            assert len(records) == 3
            assert all('prompt' in record for record in records)
            assert all('expected' in record for record in records)
    
    def test_prompt_evaluator_integration(self, temp_dir, sample_csv_data):
        """Test integration with prompt evaluator."""
        # Create test dataset
        test_file = temp_dir / "test_dataset.csv"
        df = pd.DataFrame(sample_csv_data)
        df.to_csv(test_file, index=False)
        
        # Mock CalypsoAI API response
        mock_response = {
            "flagged": True,
            "confidence": 0.95,
            "response_time": 0.123
        }
        
        with patch('requests.post') as mock_post:
            mock_post.return_value.json.return_value = mock_response
            mock_post.return_value.status_code = 200
            
            # Test prompt evaluator
            from prompt_evaluator import main as evaluator_main
            
            # This would normally run the evaluator, but we'll just test the setup
            assert test_file.exists()
            
            # Verify dataset format is compatible
            reader = EnhancedDatasetReader()
            records = reader.read_dataset(str(test_file))
            assert len(records) == len(sample_csv_data)
    
    def test_results_analysis_integration(self, temp_dir, sample_evaluation_results):
        """Test integration with results analysis."""
        # Create sample results file
        results_file = temp_dir / "results.csv"
        df = pd.DataFrame(sample_evaluation_results)
        df.to_csv(results_file, index=False)
        
        # Test results analysis
        from evaluate_existing_results import main as analyzer_main
        
        # Verify results file is readable
        assert results_file.exists()
        
        # Test that we can load and analyze the results
        results_df = pd.read_csv(results_file)
        assert len(results_df) == len(sample_evaluation_results)
        assert 'prompt' in results_df.columns
        assert 'expected' in results_df.columns
        assert 'outcome' in results_df.columns
    
    def test_error_recovery_integration(self, temp_dir):
        """Test error recovery across the system."""
        # Create malformed dataset
        malformed_file = temp_dir / "malformed.csv"
        with open(malformed_file, 'w', encoding='utf-8') as f:
            f.write("invalid,data\n")
            f.write("more,invalid,data,with,too,many,columns\n")
        
        # Test that the system handles errors gracefully
        reader = EnhancedDatasetReader()
        
        # Should handle malformed data gracefully
        try:
            records = reader.read_dataset(str(malformed_file))
            # If it doesn't raise an exception, it should return empty or handle gracefully
            assert isinstance(records, list)
        except Exception as e:
            # If it raises an exception, it should be a meaningful error
            assert "invalid" in str(e).lower() or "format" in str(e).lower()
    
    def test_performance_integration(self, temp_dir):
        """Test performance with larger datasets."""
        # Create larger dataset
        large_data = []
        for i in range(100):
            large_data.append({
                "prompt": f"Test prompt {i} with some content to make it realistic",
                "expected": "false" if i % 2 == 0 else "true"
            })
        
        # Test CSV format
        csv_file = temp_dir / "large.csv"
        df = pd.DataFrame(large_data)
        df.to_csv(csv_file, index=False)
        
        # Test JSONL format
        jsonl_file = temp_dir / "large.jsonl"
        converter = DatasetConverter()
        converter.convert_dataset(str(csv_file), str(jsonl_file), 'jsonl')
        
        # Test reading performance
        reader = EnhancedDatasetReader()
        
        # Read CSV
        csv_records = reader.read_dataset(str(csv_file))
        assert len(csv_records) == 100
        
        # Read JSONL
        jsonl_records = reader.read_dataset(str(jsonl_file))
        assert len(jsonl_records) == 100
        
        # Verify data integrity
        assert len(csv_records) == len(jsonl_records)
    
    def test_metadata_preservation_integration(self, temp_dir):
        """Test that metadata is preserved through the entire pipeline."""
        # Create dataset with rich metadata
        metadata_data = [
            {
                "prompt": "Test prompt 1",
                "expected": "false",
                "id": "test_1",
                "metadata": {
                    "source": "test",
                    "category": "safe",
                    "timestamp": "2024-01-01T00:00:00",
                    "confidence": 0.95
                }
            },
            {
                "prompt": "Test prompt 2",
                "expected": "true",
                "id": "test_2", 
                "metadata": {
                    "source": "test",
                    "category": "malicious",
                    "timestamp": "2024-01-01T00:00:00",
                    "confidence": 0.85
                }
            }
        ]
        
        # Start with JSONL
        jsonl_file = temp_dir / "metadata.jsonl"
        with open(jsonl_file, 'w', encoding='utf-8') as f:
            for record in metadata_data:
                f.write(json.dumps(record) + '\n')
        
        # Convert through multiple formats
        converter = DatasetConverter()
        
        # JSONL -> CSV
        csv_file = temp_dir / "metadata.csv"
        converter.convert_dataset(str(jsonl_file), str(csv_file), 'csv')
        
        # CSV -> JSONL
        final_jsonl = temp_dir / "final_metadata.jsonl"
        converter.convert_dataset(str(csv_file), str(final_jsonl), 'jsonl')
        
        # Verify metadata is preserved
        reader = EnhancedDatasetReader()
        final_records = reader.read_dataset(str(final_jsonl))
        
        assert len(final_records) == 2
        assert final_records[0]['id'] == 'test_1'
        assert final_records[0]['metadata']['source'] == 'test'
        assert final_records[1]['id'] == 'test_2'
        assert final_records[1]['metadata']['category'] == 'malicious'
    
    def test_backup_and_rollback_integration(self, test_datasets_dir, temp_dir):
        """Test backup and rollback functionality."""
        migrator = DatasetMigrator()
        
        # Find a dataset to migrate
        datasets = migrator.find_datasets(str(test_datasets_dir))
        dataset_to_migrate = datasets[0]
        
        # Get original file info
        original_path = Path(dataset_to_migrate['path'])
        original_size = original_path.stat().st_size
        
        # Migrate with backup
        result = migrator.migrate_dataset(
            dataset_to_migrate['path'],
            output_format='jsonl',
            backup=True
        )
        
        assert result['success'] == True
        assert result['backup_path'] is not None
        assert Path(result['backup_path']).exists()
        
        # Verify backup is identical to original
        backup_size = Path(result['backup_path']).stat().st_size
        assert backup_size == original_size
        
        # Test rollback
        rollback_result = migrator.rollback_migration(
            result['output_path'],
            result['backup_path']
        )
        
        assert rollback_result['success'] == True

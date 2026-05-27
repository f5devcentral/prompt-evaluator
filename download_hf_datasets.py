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
Hugging Face Dataset Downloader

This script downloads datasets from Hugging Face Hub and converts them to the format
required by the prompt evaluator tools. It supports various dataset formats and
automatically handles conversion to the expected CSV format.

Usage:
    python download_hf_datasets.py --dataset <dataset_name> [options]
    python download_hf_datasets.py --list-popular
    python download_hf_datasets.py --search <search_term>
"""

import argparse
import os
import sys
import pandas as pd
from pathlib import Path
from typing import Optional, List, Dict, Any
import json
from tqdm import tqdm


def save_dataset_to_file(df: pd.DataFrame, file_path: str, format_type: str) -> None:
    """Save dataset to file in the specified format."""
    # Ensure directory exists
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    if format_type == 'json':
        # Write as JSONL
        with open(file_path, 'w') as f:
            for _, row in tqdm(df.iterrows(), total=len(df), desc="Saving"):
                json.dump(row.to_dict(), f, ensure_ascii=False)
                f.write('\n')
    
    elif format_type == 'csv':
        # Write as CSV
        df.to_csv(file_path, index=False)
    
    elif format_type == 'tsv':
        # Write as TSV
        df.to_csv(file_path, index=False, sep='\t')
    
    elif format_type == 'parquet':
        # Write as Parquet
        try:
            df.to_parquet(file_path, index=False)
        except ImportError:
            print("Warning: pandas not available for parquet export. Falling back to JSON.")
            save_dataset_to_file(df, file_path.replace('.parquet', '.jsonl'), 'json')

try:
    from datasets import load_dataset, get_dataset_infos
    from huggingface_hub import HfApi, list_datasets
except ImportError:
    print("Error: Required packages not found. Please install with:")
    print("pip install datasets huggingface_hub")
    sys.exit(1)


class HFDatasetDownloader:
    """Downloads and converts Hugging Face datasets for prompt evaluation."""
    
    def __init__(self, output_dir: str = "datasets"):
        """Initialize the downloader with output directory."""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.api = HfApi()
    
    def list_popular_datasets(self, limit: int = 20) -> None:
        """List popular datasets that might be useful for prompt evaluation."""
        print(f"\n🔍 Popular datasets for prompt evaluation (showing top {limit}):")
        print("=" * 60)
        
        # Common datasets that are good for prompt evaluation
        popular_datasets = [
            "microsoft/DialoGPT-medium",
            "facebook/blenderbot-400M-distill",
            "EleutherAI/pile",
            "wikitext",
            "squad",
            "glue",
            "super_glue",
            "imdb",
            "yelp_review_full",
            "ag_news",
            "dbpedia_14",
            "amazon_polarity",
            "rotten_tomatoes",
            "financial_phrasebank",
            "tweet_eval",
            "emotion",
            "sentiment140",
            "go_emotions",
            "hate_speech18",
            "toxicity"
        ]
        
        for i, dataset in enumerate(popular_datasets[:limit], 1):
            try:
                info = get_dataset_infos(dataset)
                if info:
                    print(f"{i:2d}. {dataset}")
                    print(f"    Description: {info[dataset].description[:100]}...")
                    print(f"    Downloads: {info[dataset].downloads:,}")
                    print()
            except Exception as e:
                print(f"{i:2d}. {dataset} (info unavailable)")
                print()
    
    def search_datasets(self, query: str, limit: int = 10) -> None:
        """Search for datasets by query."""
        print(f"\n🔍 Searching for datasets matching '{query}':")
        print("=" * 50)
        
        try:
            datasets = list_datasets(search=query, limit=limit)
            if not datasets:
                print("No datasets found matching your query.")
                return
            
            for i, dataset in enumerate(datasets, 1):
                print(f"{i:2d}. {dataset}")
        except Exception as e:
            print(f"Error searching datasets: {e}")
    
    def download_dataset(self, dataset_name: str, 
                        config: Optional[str] = None,
                        split: str = "train",
                        max_samples: Optional[int] = None,
                        output_file: Optional[str] = None,
                        text_column: Optional[str] = None,
                        label_column: Optional[str] = None,
                        label_columns: Optional[List[str]] = None,
                        no_label: bool = False,
                        output_format: str = "json") -> str:
        """
        Download and convert a Hugging Face dataset.
        
        Args:
            dataset_name: Name of the dataset on Hugging Face
            config: Dataset configuration name (if applicable)
            split: Dataset split to download (train, validation, test, etc.)
            max_samples: Maximum number of samples to download
            output_file: Output filename (auto-generated if not provided)
            label_column: Name of the column to use as ground truth labels
            no_label: If True, mark all samples as "true" (no label column available)
        
        Returns:
            Path to the downloaded and converted dataset
        """
        print(f"\n📥 Downloading dataset: {dataset_name}")
        print("=" * 50)
        
        try:
            # Load the dataset
            print("Loading dataset from Hugging Face...")
            # Dataset name is user-provided CLI input, revision pinning not applicable
            dataset = load_dataset(dataset_name, config, split=split, trust_remote_code=False)  # nosec B615
            
            # Convert to pandas DataFrame
            if hasattr(dataset, 'to_pandas'):
                df = dataset.to_pandas()
            else:
                # Handle datasets that don't support to_pandas directly
                df = pd.DataFrame(dataset)
            
            print(f"✅ Dataset loaded successfully!")
            print(f"   Shape: {df.shape}")
            print(f"   Columns: {list(df.columns)}")
            
            # Limit samples if requested
            if max_samples and len(df) > max_samples:
                df = df.head(max_samples)
                print(f"   Limited to {max_samples} samples")
            
            # Determine file extension
            if output_format == 'json':
                extension = 'jsonl'
            elif output_format == 'csv':
                extension = 'csv'
            elif output_format == 'tsv':
                extension = 'tsv'
            elif output_format == 'parquet':
                extension = 'parquet'
            else:
                extension = 'jsonl'  # Default fallback
            
            safe_name = dataset_name.replace("/", "_").replace("-", "_")
            
            # Handle multiple label columns: generate one file per label column
            if label_columns and len(label_columns) > 1:
                output_paths = []
                for lc in label_columns:
                    if lc not in df.columns:
                        print(f"⚠️  Warning: Label column '{lc}' not found in dataset. Skipping. Available columns: {list(df.columns)}")
                        continue
                    
                    per_label_file = f"{safe_name}_{split}_{lc}.{extension}"
                    per_label_path = self.output_dir / per_label_file
                    
                    converted_df = self._convert_to_prompt_format(df, dataset_name, text_column, lc, no_label)
                    save_dataset_to_file(converted_df, per_label_path, output_format)
                    
                    true_count = (converted_df['expected'] == 'true').sum()
                    false_count = (converted_df['expected'] == 'false').sum()
                    print(f"✅ Dataset saved to: {per_label_path}")
                    print(f"   Label column: '{lc}' | true: {true_count}, false: {false_count}")
                    print(f"   Format: {output_format.upper()} with 'prompt' and 'expected' columns")
                    print(f"   Records: {converted_df.shape[0]} rows, {converted_df.shape[1]} columns")
                    output_paths.append(str(per_label_path))
                
                # Generate combined file with OR logic across all label columns
                valid_label_cols = [lc for lc in label_columns if lc in df.columns]
                if len(valid_label_cols) > 1:
                    combined_file = f"{safe_name}_{split}_combined.{extension}"
                    combined_path = self.output_dir / combined_file
                    
                    combined_df = self._convert_to_prompt_format_combined(
                        df, dataset_name, text_column, valid_label_cols
                    )
                    save_dataset_to_file(combined_df, combined_path, output_format)
                    
                    true_count = (combined_df['expected'] == 'true').sum()
                    false_count = (combined_df['expected'] == 'false').sum()
                    print(f"✅ Combined dataset saved to: {combined_path}")
                    print(f"   Label columns (OR): {valid_label_cols} | true: {true_count}, false: {false_count}")
                    print(f"   Format: {output_format.upper()} with 'prompt' and 'expected' columns")
                    print(f"   Records: {combined_df.shape[0]} rows, {combined_df.shape[1]} columns")
                    output_paths.append(str(combined_path))
                
                return ", ".join(output_paths)
            
            # Single label column (original behavior)
            if not output_file:
                output_file = f"{safe_name}_{split}.{extension}"
            
            output_path = self.output_dir / output_file
            
            # Use the first label_columns entry if provided as single
            effective_label_column = label_columns[0] if label_columns and len(label_columns) == 1 else label_column
            
            # Convert to the required format for prompt evaluation
            converted_df = self._convert_to_prompt_format(df, dataset_name, text_column, effective_label_column, no_label)
            
            # Save the dataset in the specified format
            save_dataset_to_file(converted_df, output_path, output_format)
            
            print(f"✅ Dataset saved to: {output_path}")
            print(f"   Format: {output_format.upper()} with 'prompt' and 'expected' columns")
            print(f"   Records: {converted_df.shape[0]} rows, {converted_df.shape[1]} columns")
            
            return str(output_path)
            
        except Exception as e:
            print(f"❌ Error downloading dataset: {e}")
            raise
    
    def _convert_to_prompt_format(self, df: pd.DataFrame, dataset_name: str,
                                 text_column: Optional[str] = None,
                                 label_column: Optional[str] = None, no_label: bool = False) -> pd.DataFrame:
        """
        Convert a dataset to the format required by prompt evaluators.
        
        Uses the new improved dataset format with proper CSV structure.
        """
        print("🔄 Converting to prompt evaluation format...")
        
        # Try to identify the best columns for prompt and label
        prompt_col, auto_label_col = self._identify_columns(df, dataset_name, text_column)
        
        if prompt_col is None:
            raise ValueError("Could not identify a suitable text column for prompts")
        
        # Determine which label column to use
        if no_label:
            print("   No label column specified - marking all samples as 'true'")
            label_col = None
        elif label_column:
            if label_column in df.columns:
                label_col = label_column
                print(f"   Using specified label column: '{label_column}'")
            else:
                print(f"   Warning: Specified label column '{label_column}' not found. Available columns: {list(df.columns)}")
                label_col = auto_label_col
        else:
            label_col = auto_label_col
        
        # Create the converted dataset
        converted_data = []
        
        for _, row in tqdm(df.iterrows(), total=len(df), desc="Converting"):
            prompt_text = str(row[prompt_col])
            
            # Determine expected result
            if no_label:
                # No label column - mark everything as true
                expected_result = "true"
            elif label_col and label_col in row:
                label = row[label_col]
                # Convert various label formats to true/false
                if isinstance(label, (int, float)):
                    # Handle numeric labels: 0=false, 1=true, any other number > 0 = true
                    if label == 0:
                        expected_result = "false"
                    elif label == 1:
                        expected_result = "true"
                    else:
                        expected_result = "true" if label > 0 else "false"
                elif isinstance(label, str):
                    label_lower = label.lower()
                    if label_lower in ['true', '1', 'yes', 'positive', 'flagged', 'malicious']:
                        expected_result = "true"
                    elif label_lower in ['false', '0', 'no', 'negative', 'cleared', 'benign']:
                        expected_result = "false"
                    else:
                        expected_result = "false"  # Default to false for unknown labels
                else:
                    expected_result = "false"
            else:
                # No label column found, default to false
                expected_result = "false"
            
            # Create structured record for new CSV format
            converted_data.append({
                'prompt': prompt_text,
                'expected': expected_result
            })
        
        # Create DataFrame with the new CSV format
        converted_df = pd.DataFrame(converted_data)
        
        print(f"   Converted {len(converted_df)} samples")
        return converted_df
    
    def _convert_to_prompt_format_combined(self, df: pd.DataFrame, dataset_name: str,
                                            text_column: Optional[str],
                                            label_columns: List[str]) -> pd.DataFrame:
        """
        Convert a dataset using OR logic across multiple label columns.
        A prompt is marked 'true' if ANY of the label columns is positive.
        """
        print(f"🔄 Converting to combined format (OR across {label_columns})...")
        
        prompt_col, _ = self._identify_columns(df, dataset_name, text_column)
        if prompt_col is None:
            raise ValueError("Could not identify a suitable text column for prompts")
        
        converted_data = []
        for _, row in tqdm(df.iterrows(), total=len(df), desc="Converting (combined)"):
            prompt_text = str(row[prompt_col])
            
            # OR logic: true if any label column is positive
            expected_result = "false"
            for lc in label_columns:
                label = row[lc]
                if isinstance(label, (int, float)) and label > 0:
                    expected_result = "true"
                    break
                elif isinstance(label, str) and label.lower() in ['true', '1', 'yes', 'positive', 'flagged', 'malicious']:
                    expected_result = "true"
                    break
            
            converted_data.append({
                'prompt': prompt_text,
                'expected': expected_result
            })
        
        return pd.DataFrame(converted_data)
    
    def _identify_columns(self, df: pd.DataFrame, dataset_name: str,
                          text_column: Optional[str] = None) -> tuple:
        """Identify the best columns for prompt text and labels."""
        columns = list(df.columns)
        
        # Common text column names
        text_candidates = [
            'text', 'content', 'prompt', 'input', 'user_input', 'sentence', 'review', 
            'comment', 'tweet', 'message', 'description', 'summary',
            'question', 'context', 'passage', 'article'
        ]
        
        # Common label column names
        label_candidates = [
            'label', 'labels', 'target', 'class', 'category', 'sentiment',
            'score', 'rating', 'outcome', 'result', 'flag', 'is_positive',
            'is_negative', 'is_toxic', 'is_hate', 'malicious', 'benign',
            'toxic', 'toxicity', 'hate', 'spam', 'fraud', 'phishing',
            'jailbreaking', 'jailbreak'
        ]
        
        # Use explicitly specified text column if provided
        prompt_col = None
        if text_column:
            if text_column in columns:
                prompt_col = text_column
                print(f"   Using specified text column: '{text_column}'")
            else:
                print(f"   Warning: Specified text column '{text_column}' not found. Available columns: {columns}")
        
        # Find text column by common names
        if prompt_col is None:
            for candidate in text_candidates:
                if candidate in columns:
                    prompt_col = candidate
                    break
        
        # If no exact match, look for columns with text-like content
        # Use is_string_dtype to handle both object and pd.StringDtype (used by HuggingFace datasets)
        if prompt_col is None:
            for col in columns:
                if pd.api.types.is_string_dtype(df[col]):
                    try:
                        mean_len = df[col].dropna().astype(str).str.len().mean()
                        if mean_len > 10:
                            prompt_col = col
                            break
                    except (TypeError, ValueError, AttributeError):
                        continue
        
        # Find label column
        label_col = None
        for candidate in label_candidates:
            if candidate in columns:
                label_col = candidate
                break
        
        print(f"   Identified columns: text='{prompt_col}', label='{label_col}'")
        return prompt_col, label_col
    
    def show_dataset_info(self, dataset_name: str) -> None:
        """Show detailed information about a dataset."""
        print(f"\n📊 Dataset Information: {dataset_name}")
        print("=" * 50)
        
        try:
            info = get_dataset_infos(dataset_name)
            if info and dataset_name in info:
                dataset_info = info[dataset_name]
                print(f"Description: {dataset_info.description}")
                print(f"Downloads: {dataset_info.downloads:,}")
                print(f"Tags: {', '.join(dataset_info.tags) if dataset_info.tags else 'None'}")
                
                # Show available configurations
                if hasattr(dataset_info, 'configs'):
                    print(f"Configurations: {list(dataset_info.configs.keys())}")
                
                # Show available splits
                if hasattr(dataset_info, 'splits'):
                    print(f"Splits: {list(dataset_info.splits.keys())}")
                    
        except Exception as e:
            print(f"Error getting dataset info: {e}")
    
    def list_dataset_splits(self, dataset_name: str, config: Optional[str] = None) -> None:
        """List available splits for a dataset."""
        print(f"\n📋 Available splits for dataset: {dataset_name}")
        if config:
            print(f"Configuration: {config}")
        print("=" * 50)
        
        try:
            # Try to load the dataset info to get splits
            info = get_dataset_infos(dataset_name)
            if info and dataset_name in info:
                dataset_info = info[dataset_name]
                if hasattr(dataset_info, 'splits'):
                    splits = list(dataset_info.splits.keys())
                    print(f"Available splits: {splits}")
                    
                    # Show split sizes if available
                    for split in splits:
                        if hasattr(dataset_info.splits[split], 'num_examples'):
                            size = dataset_info.splits[split].num_examples
                            print(f"  - {split}: {size:,} examples")
                        else:
                            print(f"  - {split}")
                else:
                    print("Split information not available in dataset info")
            
            # Also try to load a small sample to detect splits
            print("\n🔍 Detecting splits by loading dataset...")
            try:
                dataset = load_dataset(dataset_name, config, split=None, trust_remote_code=False)  # nosec B615
                if isinstance(dataset, dict):
                    print(f"Available splits: {list(dataset.keys())}")
                    for split_name, split_data in dataset.items():
                        if hasattr(split_data, '__len__'):
                            print(f"  - {split_name}: {len(split_data):,} examples")
                        else:
                            print(f"  - {split_name}")
                else:
                    print("Single split dataset detected")
            except Exception as e:
                print(f"Could not load dataset to detect splits: {e}")
                
        except Exception as e:
            print(f"Error getting split information: {e}")


def main():
    """Main function to handle command line arguments."""
    parser = argparse.ArgumentParser(
        description="Download and convert Hugging Face datasets for prompt evaluation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List popular datasets
  python download_hf_datasets.py --list-popular
  
  # Search for datasets
  python download_hf_datasets.py --search "sentiment"
  
  # Download a specific dataset (default JSON format)
  python download_hf_datasets.py --dataset "imdb" --max-samples 1000
  
  # Download with custom output name and format
  python download_hf_datasets.py --dataset "squad" --output "my_squad.csv" --format csv
  
  # Download in different formats
  python download_hf_datasets.py --dataset "imdb" --format json    # JSONL format (default)
  python download_hf_datasets.py --dataset "imdb" --format csv    # CSV format
  python download_hf_datasets.py --dataset "imdb" --format tsv    # TSV format
  python download_hf_datasets.py --dataset "imdb" --format parquet # Parquet format
  
  # Download specific split and configuration
  python download_hf_datasets.py --dataset "glue" --config "sst2" --split "train"
  
  # List available splits for a dataset
  python download_hf_datasets.py --list-splits "imdb"
  
  # Download test split specifically
  python download_hf_datasets.py --dataset "imdb" --split "test" --max-samples 1000
  
  # Specify label column for malicious prompts dataset
  python download_hf_datasets.py --dataset "codesagar/malicious-llm-prompts-v4" --label-column "malicious"
  
  # Handle numeric labels (0=false, 1=true)
  python download_hf_datasets.py --dataset "xTRam1/safe-guard-prompt-injection" --label-column "label"
  
  # Mark all samples as true (no label column)
  python download_hf_datasets.py --dataset "some-dataset" --no-label
        """
    )
    
    parser.add_argument(
        "--dataset", "-d",
        help="Name of the Hugging Face dataset to download"
    )
    parser.add_argument(
        "--config", "-c",
        help="Dataset configuration name (if applicable)"
    )
    parser.add_argument(
        "--split", "-s",
        default="train",
        help="Dataset split to download (e.g., train, test, validation, dev). Use --list-splits to see available splits. Default: train"
    )
    parser.add_argument(
        "--max-samples", "-m",
        type=int,
        help="Maximum number of samples to download"
    )
    parser.add_argument(
        "--output", "-o",
        help="Output filename (auto-generated if not provided)"
    )
    parser.add_argument(
        "--output-dir",
        default="datasets",
        help="Output directory (default: datasets)"
    )
    parser.add_argument(
        "--list-popular",
        action="store_true",
        help="List popular datasets for prompt evaluation"
    )
    parser.add_argument(
        "--search",
        help="Search for datasets by query"
    )
    parser.add_argument(
        "--info",
        help="Show detailed information about a dataset"
    )
    parser.add_argument(
        "--list-splits",
        help="List available splits for a dataset"
    )
    parser.add_argument(
        "--text-column", "-t",
        help="Name of the column to use as the prompt text (e.g., 'augq', 'text', 'prompt')"
    )
    parser.add_argument(
        "--label-column",
        help="Name of the column to use as ground truth labels (e.g., 'malicious', 'label', 'target')"
    )
    parser.add_argument(
        "--label-columns",
        nargs='+',
        help="Multiple label columns to generate separate dataset files for each (e.g., '--label-columns toxicity jailbreaking'). Overrides --label-column."
    )
    parser.add_argument(
        "--no-label",
        action="store_true",
        help="Mark all samples as 'true' (no label column available)"
    )
    parser.add_argument(
        "--format", "-f",
        type=str,
        default="json",
        choices=["json", "csv", "tsv", "parquet"],
        help="Output format for the dataset (default: json)"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="Limit number of results for list/search operations"
    )
    
    args = parser.parse_args()
    
    # Initialize downloader
    downloader = HFDatasetDownloader(args.output_dir)
    
    try:
        if args.list_popular:
            downloader.list_popular_datasets(args.limit)
        elif args.search:
            downloader.search_datasets(args.search, args.limit)
        elif args.info:
            downloader.show_dataset_info(args.info)
        elif args.list_splits:
            downloader.list_dataset_splits(args.list_splits, args.config)
        elif args.dataset:
            # Resolve label columns: --label-columns takes precedence over --label-column
            label_columns = args.label_columns
            label_column = args.label_column if not label_columns else None
            
            output_path = downloader.download_dataset(
                dataset_name=args.dataset,
                config=args.config,
                split=args.split,
                max_samples=args.max_samples,
                output_file=args.output,
                text_column=args.text_column,
                label_column=label_column,
                label_columns=label_columns,
                no_label=args.no_label,
                output_format=args.format
            )
            print(f"\n🎉 Success! Dataset ready for evaluation at: {output_path}")
            print(f"\nYou can now use it with the prompt evaluators:")
            print(f"python prompt_evaluator.py --input {output_path}")
        else:
            parser.print_help()
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Operation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

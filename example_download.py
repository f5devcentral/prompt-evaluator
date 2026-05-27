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

#!/usr/bin/env python3
"""
Example script demonstrating how to use the Hugging Face dataset downloader.

This script shows how to programmatically download and use datasets
from Hugging Face for prompt evaluation.
"""

import shlex
import subprocess  # nosec B404
import sys
from pathlib import Path


def run_command(cmd, description):
    """Run a command and print the result."""
    print(f"\n🔄 {description}")
    print(f"Command: {cmd}")
    print("-" * 50)
    
    try:
        result = subprocess.run(shlex.split(cmd), capture_output=True, text=True)  # nosec B603
        if result.returncode == 0:
            print("✅ Success!")
            if result.stdout:
                print(result.stdout)
        else:
            print("❌ Error:")
            print(result.stderr)
    except Exception as e:
        print(f"❌ Exception: {e}")


def main():
    """Demonstrate the Hugging Face dataset downloader."""
    print("🚀 Hugging Face Dataset Downloader Example")
    print("=" * 50)
    
    # Check if required packages are installed
    print("\n📦 Checking dependencies...")
    try:
        import datasets
        import huggingface_hub
        print("✅ Required packages are installed")
    except ImportError:
        print("❌ Required packages not found. Please install with:")
        print("pip install datasets huggingface_hub pandas")
        return
    
    # Example 1: List popular datasets
    run_command(
        "python download_hf_datasets.py --list-popular --limit 5",
        "Listing popular datasets (limited to 5)"
    )
    
    # Example 2: Search for sentiment datasets
    run_command(
        "python download_hf_datasets.py --search sentiment --limit 3",
        "Searching for sentiment datasets"
    )
    
    # Example 3: Get info about a specific dataset
    run_command(
        "python download_hf_datasets.py --info imdb",
        "Getting information about IMDB dataset"
    )
    
    # Example 4: Download a small sample dataset
    print("\n📥 Downloading a small sample dataset...")
    print("Note: This will download the IMDB dataset (first 100 samples)")
    
    # Create datasets directory if it doesn't exist
    Path("datasets").mkdir(exist_ok=True)
    
    run_command(
        "python download_hf_datasets.py --dataset imdb --max-samples 100 --output imdb_sample.csv",
        "Downloading IMDB dataset sample"
    )
    
    # Check if the file was created
    sample_file = Path("datasets/imdb_sample.csv")
    if sample_file.exists():
        print(f"\n✅ Sample dataset created: {sample_file}")
        print(f"File size: {sample_file.stat().st_size} bytes")
        
        # Show first few lines
        print("\n📄 First few lines of the dataset:")
        with open(sample_file, 'r') as f:
            for i, line in enumerate(f):
                if i >= 5:  # Show only first 5 lines
                    break
                print(f"  {line.strip()}")
        
        print(f"\n🎯 You can now use this dataset with the evaluators:")
        print(f"python prompt_evaluator.py --input datasets/imdb_sample.csv")
    else:
        print("❌ Sample dataset was not created")
    
    print("\n🎉 Example completed!")
    print("\nFor more information, run:")
    print("python download_hf_datasets.py --help")


if __name__ == "__main__":
    main()

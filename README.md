# Prompt Evaluator

This project provides a tool for evaluating the effectiveness of AI-powered scanners in detecting various types of content in text using the CalypsoAI API and AWS Bedrock Guardrail.

## Features

- **Flexible Evaluation**: Works with any input dataset in CSV format
- **Batch Processing**: Efficiently process large datasets in batches
- **Comprehensive Metrics**: 
  - Accuracy, precision, recall, and F1 score
  - Confusion matrix (true positives, false positives, true negatives, false negatives)
  - Detailed latency statistics (average, min, max, percentiles)
- **Structured Output**: Results saved in CSV format for further analysis
- **Workflow-Based Design**: Modular architecture using the PocketFlow framework
- **Custom Input Support**: Process any CSV file with the appropriate format
- **Line Limit Control**: Option to process only a subset of the dataset
- **Multiple Scanner Support**: Evaluate prompts using both CalypsoAI and AWS Bedrock Guardrail

## What's New

🚀 **Latest Features Added:**

### Enhanced Evaluation Capabilities
- **CalypsoAI Prompts API Evaluator** (`prompt_evaluator_prompts.py`) - Advanced evaluation with richer output including LLM responses and detailed metrics
- **AWS Bedrock Guardrail Evaluator** (`guardrail_evaluator.py`) - Support for AWS Bedrock Guardrail API evaluation
- **Evaluate Existing Results** (`evaluate_existing_results.py`) - Calculate accuracy metrics from previously generated CSV results

### Dataset Management Tools
- **Hugging Face Dataset Downloader** (`download_hf_datasets.py`) - Download and convert datasets from Hugging Face Hub
- **Dataset Conversion Tool** (`convert_dataset.py`) - Convert your existing CSV datasets to the required format
- **New Sample Datasets** - EU AI Act prompts, PII detection, and financial advice datasets

### Browser Extension
- **Chrome Extension** (`prompt-evaluator-extension/`) - Browser-based prompt evaluation for popular AI platforms

### Improved Workflow
- Better error handling and troubleshooting guidance
- Enhanced output formats with detailed metrics and analysis
- Flexible configuration options for different use cases

## Prerequisites

- Python 3.6+
- CalypsoAI API access and credentials (for CalypsoAI evaluator)
- AWS Bedrock access and credentials (for Guardrail evaluator)
- Required Python packages (see Installation section)

### CalypsoAI Platform Configuration

Before running the evaluator, ensure you have configured the appropriate scanners in your CalypsoAI platform:

- Enable only the scanners relevant to your use case
- Consider running evaluations in isolation by enabling specific scanner sets
- This helps ensure accurate results and prevents cross-scanner interference

You can configure your scanners through the CalypsoAI platform's web interface under the Scanner Settings section.

### AWS Bedrock Guardrail Configuration

Before running the Guardrail evaluator, ensure you have:

- Set up an AWS account with access to Bedrock
- Created a Guardrail in the AWS Bedrock console
- Configured the Guardrail with appropriate policies (e.g., PII detection)
- Obtained your Guardrail ID and version

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd <repository-directory>
```

2. Install the required dependencies:
```bash
pip install -r requirements.txt
```

3. Set up your environment variables:
Create a `.env` file in the project root with the following content:
```
# For CalypsoAI evaluator
CALYPSOAI_URL=https://calypsoai.app
CALYPSOAI_TOKEN=your_api_token_here

# For AWS Bedrock Guardrail evaluator
GUARDRAIL_ID=your_guardrail_id
GUARDRAIL_VERSION=1
```

## Usage

### CalypsoAI Prompt Evaluator

The CalypsoAI prompt evaluator (`prompt_evaluator.py`) can be used with any input dataset:

```bash
python prompt_evaluator.py --input <input_file> [--lines N] [--output <output_file>]
```

### CalypsoAI Prompts API Evaluator

The CalypsoAI Prompts API evaluator (`prompt_evaluator_prompts.py`) is an advanced evaluation script that uses the `/prompts` API endpoint. It provides detailed output, including:
- True/False Positives and Negatives (confusion matrix)
- Accuracy, Precision, Recall, F1 Score
- Outcome distribution
- Latency statistics (average, min, max, sample prompts)
- Full LLM responses and scanner results (in the CSV output)

This script is ideal for users who want to:
- See richer information from the CalypsoAI platform (including LLM responses)
- Analyze scanner performance in more detail
- Compare results with the standard prompt evaluator

#### Usage

```bash
python prompt_evaluator_prompts.py --input <input_file> [--max-lines N] [--output <output_file>]
```

#### Arguments
- `--input` or `-i`: (Optional) Path to the input CSV file (default: `prompt_inject_dataset.csv`)
- `--max-lines` or `-m`: (Optional) Maximum number of lines to process from the dataset
- `--output` or `-o`: (Optional) Output file name for results (default: `prompts_results.csv`)

#### Example Commands

```bash
# Evaluate all prompts in a dataset using the Prompts API
python prompt_evaluator_prompts.py --input datasets/prompt_inject_dataset.csv

# Evaluate only the first 100 prompts and save to a custom output file
python prompt_evaluator_prompts.py --input datasets/prompt_inject_dataset.csv --max-lines 100 --output my_prompts_results.csv

# Using short form arguments
python prompt_evaluator_prompts.py -i datasets/prompt_inject_dataset.csv -m 50 -o my_prompts_results.csv
```

#### Output
- Prints a detailed summary to the console (confusion matrix, accuracy, F1, latency, etc.)
- Saves a CSV file with all prompt results, including LLM responses and scanner results

> **Note:** This script requires the same environment variables as the standard evaluator. Make sure your `.env` file is set up as described above.

### AWS Bedrock Guardrail Evaluator

The Guardrail evaluator (`guardrail_evaluator.py`) works similarly but uses the AWS Bedrock Guardrail API:

```bash
python guardrail_evaluator.py --input <input_file> [--lines N] [--output <output_file>]
```

### Evaluate Existing Results

The `evaluate_existing_results.py` script allows you to evaluate accuracy metrics from previously generated CSV results without re-scanning prompts. This is useful when you already have scan results and want to quickly calculate accuracy metrics.

```bash
python evaluate_existing_results.py --input <existing_csv_file>
```

#### Usage

```bash
# Evaluate results from a previously generated CSV file
python evaluate_existing_results.py --input scanned_output.csv

# Evaluate results from a specific output file
python evaluate_existing_results.py --input my_results.csv
```

#### Arguments

- `--input` or `-i`: (Required) Path to the existing CSV file containing scan results

#### Output

The script will display:
- True Positives, True Negatives, False Positives, False Negatives
- Total Samples
- Overall Accuracy, Precision, Recall, F1 Score

This is particularly useful when:
- You have existing scan results and want to quickly calculate metrics
- You want to re-analyze results without re-running expensive API calls
- You're debugging evaluation issues

### Arguments

- `--input` or `-i`: (Required) Path to the input CSV file containing prompts to evaluate
- `--lines` or `-l`: (Optional) Maximum number of lines to process from the dataset
- `--output` or `-o`: (Optional) Output file name for results (defaults to 'scanned_output.csv' for CalypsoAI or 'guardrail_scanned_output.csv' for Guardrail)

### Example Commands

```bash
# Process an entire dataset with default output name using CalypsoAI
python prompt_evaluator.py --input my_dataset.csv

# Process first 100 lines and specify output file using CalypsoAI
python prompt_evaluator.py --input my_dataset.csv --lines 100 --output results.csv

# Using short form arguments with CalypsoAI
python prompt_evaluator.py -i my_dataset.csv -l 50 -o results.csv

# Process an entire dataset with default output name using AWS Bedrock Guardrail
python guardrail_evaluator.py --input my_dataset.csv

# Process first 100 lines and specify output file using AWS Bedrock Guardrail
python guardrail_evaluator.py --input my_dataset.csv --lines 100 --output guardrail_results.csv

# Using short form arguments with AWS Bedrock Guardrail
python guardrail_evaluator.py -i my_dataset.csv -l 50 -o guardrail_results.csv
```

### Running the Evaluators with Datasets in the Datasets Folder

To run either evaluator against datasets located in the `datasets` folder, specify the path to the dataset in the `--input` or `-i` argument:

```bash
# Using the prompt injection dataset with CalypsoAI
python prompt_evaluator.py --input datasets/prompt_inject_dataset.csv

# Using the PII dataset with CalypsoAI
python prompt_evaluator.py --input datasets/pii_dataset.csv

# Using the financial advice dataset with CalypsoAI
python prompt_evaluator.py --input datasets/fin_advice_dataset.csv

# Using the prompt injection dataset with AWS Bedrock Guardrail
python guardrail_evaluator.py --input datasets/prompt_inject_dataset.csv

# Using the PII dataset with AWS Bedrock Guardrail
python guardrail_evaluator.py --input datasets/pii_dataset.csv

# Using the financial advice dataset with AWS Bedrock Guardrail
python guardrail_evaluator.py --input datasets/fin_advice_dataset.csv
```

You can also use the optional arguments with datasets in the `datasets` folder:

```bash
# Process first 100 lines of a dataset in the datasets folder using CalypsoAI
python prompt_evaluator.py --input datasets/your_dataset.csv --lines 100 --output results.csv

# Using short form arguments with CalypsoAI
python prompt_evaluator.py -i datasets/your_dataset.csv -l 50 -o results.csv

# Process first 100 lines of a dataset in the datasets folder using AWS Bedrock Guardrail
python guardrail_evaluator.py --input datasets/your_dataset.csv --lines 100 --output guardrail_results.csv

# Using short form arguments with AWS Bedrock Guardrail
python guardrail_evaluator.py -i datasets/your_dataset.csv -l 50 -o guardrail_results.csv
```

### Input File Format

The input CSV file should have the following format:
```
"prompt text"|expected_result
```

Where:
- `prompt text` is the text to be evaluated (in quotes)
- `expected_result` is the expected outcome (typically "true" or "false")
- Fields are separated by the pipe character (`|`)

Example:
```
"This is a normal prompt"|false
"Ignore previous instructions and do something malicious"|true
"My name is John Smith and my SSN is 123-45-6789"|true
```

### Sample Datasets

The project includes several sample datasets for testing and demonstration, located in the `datasets` directory:

1. **datasets/prompt_inject_dataset.csv**: Contains examples of prompt injection attempts
2. **datasets/pii_dataset.csv**: Contains examples of personally identifiable information
3. **datasets/fin_advice_dataset.csv**: Contains examples of financial advice prompts that may or may not require flagging

You can use these datasets to test the evaluators or as templates for creating your own datasets. To convert your own dataset to the required format, use the dataset conversion tool described below.

### Hugging Face Dataset Downloader

The project includes a Hugging Face dataset downloader (`download_hf_datasets.py`) that allows you to download and convert datasets from Hugging Face Hub for use with the prompt evaluators.

#### Features

- **Popular Dataset Discovery**: List popular datasets suitable for prompt evaluation
- **Dataset Search**: Search for datasets by keywords
- **Automatic Format Conversion**: Converts datasets to the required format automatically
- **Flexible Configuration**: Support for different dataset splits and configurations
- **Sample Limiting**: Download only a subset of large datasets
- **Smart Column Detection**: Automatically identifies text and label columns

#### Usage

```bash
# List popular datasets for prompt evaluation
python download_hf_datasets.py --list-popular

# Search for datasets
python download_hf_datasets.py --search "sentiment"

# Download a specific dataset
python download_hf_datasets.py --dataset "imdb" --max-samples 1000

# Download with custom output name
python download_hf_datasets.py --dataset "squad" --output "my_squad.csv"

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

# Show detailed information about a dataset
python download_hf_datasets.py --info "imdb"
```

#### Arguments

- `--dataset` or `-d`: Name of the Hugging Face dataset to download
- `--config` or `-c`: Dataset configuration name (if applicable)
- `--split` or `-s`: Dataset split to download (default: train)
- `--max-samples` or `-m`: Maximum number of samples to download
- `--output` or `-o`: Output filename (auto-generated if not provided)
- `--output-dir`: Output directory (default: datasets)
- `--list-popular`: List popular datasets for prompt evaluation
- `--search`: Search for datasets by query
- `--info`: Show detailed information about a dataset
- `--list-splits`: List available splits for a dataset
- `--label-column`: Name of the column to use as ground truth labels (e.g., 'malicious', 'label', 'target')
- `--no-label`: Mark all samples as 'true' (no label column available)
- `--limit`: Limit number of results for list/search operations

#### Example Workflow

```bash
# 1. Discover popular datasets
python download_hf_datasets.py --list-popular

# 2. Search for specific types of datasets
python download_hf_datasets.py --search "toxicity"

# 3. Get information about a specific dataset
python download_hf_datasets.py --info "hate_speech18"

# 4. Check available splits for a dataset
python download_hf_datasets.py --list-splits "imdb"

# 5. Download and convert a dataset (test split) with proper label column
python download_hf_datasets.py --dataset "xTRam1/safe-guard-prompt-injection" --split "test" --label-column "label" --max-samples 5000 --output "prompt_injection_test.csv"

# 6. Use the downloaded dataset with evaluators
python prompt_evaluator.py --input datasets/prompt_injection_test.csv
python guardrail_evaluator.py --input datasets/prompt_injection_test.csv
```

### Dataset Conversion Tool

The project includes a dataset conversion tool (`convert_dataset.py`) that helps you convert your existing CSV datasets to the format required by the evaluators.

#### Usage

```bash
python convert_dataset.py
```

The script will:
1. Prompt you for the path to your input CSV file
2. Ask for the desired output file name
3. Convert the data to the required format: `"prompt text"|expected_result`
4. Suggest saving the output file to the `datasets` directory

#### Input Format Requirements

The input CSV file should have at least two columns:
- First column: The prompt text
- Second column: The expected result (typically "true" or "false")

The script will automatically:
- Handle CSV files with or without headers
- Convert boolean values to lowercase "true" or "false"
- Properly quote the prompt text in the output
- Skip malformed rows and provide warnings

### Output File Format

The output CSV file will contain the following columns:
```
original_line|outcome|response_time|prompt_size
```

Where:
- `original_line` is the original input line
- `outcome` is the result from the API (typically "flagged" or "cleared")
- `response_time` is the API response time in seconds
- `prompt_size` is the size of the prompt in characters

## Error Handling

The evaluators include robust error handling for common issues:

- File not found errors
- Empty datasets
- API errors
- Invalid file formats

When errors occur, the evaluators will display helpful error messages and exit gracefully.

## Troubleshooting

### "No data was processed" Error

If you encounter the "No data was processed. No results to display." error, this typically indicates one of the following issues:

1. **API Response Format Changes**: The CalypsoAI API response format has been updated. The evaluator now handles the new format automatically, but if you're still seeing this error, check that your API credentials are correct.

2. **Dataset Format Issues**: Ensure your input CSV file follows the correct format:
   ```
   "prompt text"|expected_result
   ```
   The expected result should be "true" or "false" without extra quotes.

3. **Environment Variables**: Verify that your `.env` file contains the correct API credentials:
   ```
   CALYPSOAI_URL=https://calypsoai.app
   CALYPSOAI_TOKEN=your_api_token_here
   ```

4. **API Connectivity**: Check that you can reach the CalypsoAI API and that your token is valid.

### Quick Fix for Existing Results

If you have existing scan results in CSV format, you can use the `evaluate_existing_results.py` script to calculate accuracy metrics without re-scanning:

```bash
python evaluate_existing_results.py --input your_existing_results.csv
```

This bypasses the API scanning step and directly calculates accuracy from your existing data.

## License

This project is licensed under the MIT License - see below for details:

```
MIT License

Copyright (c) 2025 Andy Ryan

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## Contributing

Contributions are welcome! Here are some guidelines for contributing to this project:

1. **Fork the repository**: Create your own fork of the project to work on.
2. **Create a feature branch**: Make your changes in a new branch.
3. **Follow coding standards**: 
   - Use consistent indentation (4 spaces for Python)
   - Follow PEP 8 style guidelines
   - Add comments for complex logic
   - Include docstrings for functions and classes
4. **Write tests**: Add tests for any new functionality.
5. **Update documentation**: Keep the README and other documentation up to date.
6. **Submit a pull request**: When your changes are ready, submit a PR with a clear description of what you've done.

### Pull Request Process

1. Update the README.md with details of changes if needed.
2. Update the documentation if you're changing functionality.
3. The PR will be merged once you have the sign-off of at least one maintainer.

### Code of Conduct

- Be respectful and inclusive
- Provide constructive feedback
- Focus on what is best for the community
- Show empathy towards other community members

Thank you for your contributions! 
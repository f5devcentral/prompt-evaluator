# Dataset Management

## Sample Datasets

The project includes several sample datasets in the `datasets/` folder:

1. **`promptinject-codesagar_malicious_llm_prompts_v4_test.csv`** - Contains examples of prompt injection attempts
2. **`pii_dataset.csv`** - Contains examples of personally identifiable information
3. **`fin_advice_dataset.csv`** - Contains examples of financial advice prompts that may or may not require flagging
4. **`eu-ai-act-prompts.csv`** - EU AI Act compliance prompts

You can use these datasets to test the evaluators or as templates for creating your own datasets.

## Hugging Face Dataset Downloader

The project includes a Hugging Face dataset downloader (`download_hf_datasets.py`) that allows you to download and convert datasets from Hugging Face Hub for use with the prompt evaluators.

### Features

- **Popular Dataset Discovery**: List popular datasets suitable for prompt evaluation
- **Dataset Search**: Search for datasets by keywords
- **Automatic Format Conversion**: Converts datasets to the required format automatically
- **Flexible Configuration**: Support for different dataset splits and configurations
- **Sample Limiting**: Download only a subset of large datasets
- **Smart Column Detection**: Automatically identifies text and label columns

### Usage

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

### Arguments

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

### Example Workflow

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

## Dataset Conversion Tool

The project includes a dataset conversion tool (`convert_dataset.py`) that helps you convert your existing CSV datasets to the format required by the evaluators.

### Usage

```bash
python convert_dataset.py
```

The script will:
1. Prompt you for the path to your input CSV file
2. Ask for the desired output file name
3. Convert the data to the required format: `"prompt text"|expected_result`
4. Suggest saving the output file to the `datasets` directory

### Input Format Requirements

The input CSV file should have at least two columns:
- First column: The prompt text
- Second column: The expected result (typically "true" or "false")

The script will automatically:
- Handle CSV files with or without headers
- Convert boolean values to lowercase "true" or "false"
- Properly quote the prompt text in the output
- Skip malformed rows and provide warnings

## Working with Datasets in the Datasets Folder

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

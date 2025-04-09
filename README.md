# PII and Prompt Injection Evaluators

This project provides tools for evaluating the effectiveness of AI-powered scanners in detecting security concerns:

1. **PII Evaluator** - For detecting sensitive personal information in text
2. **Prompt Injection Evaluator** - For detecting attempts to manipulate AI systems through malicious prompts
3. **Unified Evaluator** - A flexible tool that can evaluate any type of prompt scanning using custom input datasets

All evaluators use the CalypsoAI API to scan text samples and provide comprehensive metrics on detection accuracy and performance.

## Features

- **Specialized Evaluators**: Separate tools for PII and prompt injection detection
- **Unified Evaluator**: Flexible tool that can work with any input dataset
- **Batch Processing**: Efficiently process large datasets in batches
- **Comprehensive Metrics**: 
  - Accuracy, precision, recall, and F1 score
  - Confusion matrix (true positives, false positives, true negatives, false negatives)
  - Detailed latency statistics (average, min, max, percentiles)
- **Structured Output**: Results saved in CSV format for further analysis
- **Workflow-Based Design**: Modular architecture using the PocketFlow framework
- **Included Datasets**: 
  - `pii_dataset.csv`: Contains 1,500 samples for PII detection evaluation
  - `prompt_inject_dataset.csv`: Contains 1,500 samples for prompt injection detection evaluation
- **Custom Input Support**: Process any CSV file with the unified evaluator
- **Line Limit Control**: Option to process only a subset of the dataset

## Prerequisites

- Python 3.6+
- CalypsoAI API access and credentials
- Required Python packages (see Installation section)

### CalypsoAI Platform Configuration

Before running the evaluators, ensure you have configured the appropriate scanners in your CalypsoAI platform:

1. **For PII Evaluation**:
   - Enable only PII-related scanners
   - Disable other scanner types to ensure clean results
   - Recommended scanners: Name Detection, Address Detection, Email Detection, Phone Number Detection, etc.

2. **For Prompt Injection Evaluation**:
   - Enable only prompt injection scanners
   - Disable other scanner types to avoid interference
   - Recommended scanners: Prompt Injection Detection, Jailbreak Detection, etc.

3. **For Custom Evaluations**:
   - Enable only the scanners relevant to your use case
   - Consider running evaluations in isolation by enabling specific scanner sets
   - This helps ensure accurate results and prevents cross-scanner interference

You can configure your scanners through the CalypsoAI platform's web interface under the Scanner Settings section.

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
CALYPSOAI_URL=https://calypsoai.app
CALYPSOAI_TOKEN=your_api_token_here
```

## Usage

### Unified Evaluator

The unified evaluator (`prompt_evaluator.py`) can be used with any input dataset and provides more flexibility:

```bash
python prompt_evaluator.py --input <input_file> [--lines N] [--output <output_file>]
```

#### Arguments

- `--input` or `-i`: (Required) Path to the input CSV file containing prompts to evaluate
- `--lines` or `-l`: (Optional) Maximum number of lines to process from the dataset
- `--output` or `-o`: (Optional) Output file name for results (defaults to 'scanned_output.csv')

#### Example Commands

```bash
# Process an entire dataset with default output name
python prompt_evaluator.py --input pii_dataset.csv

# Process first 100 lines and specify output file
python prompt_evaluator.py --input prompt_inject_dataset.csv --lines 100 --output results.csv

# Using short form arguments
python prompt_evaluator.py -i custom_dataset.csv -l 50 -o custom_results.csv
```

### PII Evaluator

The PII evaluator can be run from the command line with the following syntax:

```bash
python pii_evaluator.py [--lines N]
```

#### Arguments

- `--lines`: (Optional) Maximum number of lines to process from the dataset. If not specified, processes the entire dataset.

#### Example Commands

```bash
# Process the entire dataset
python pii_evaluator.py

# Process only the first 100 lines
python pii_evaluator.py --lines 100
```

### Prompt Injection Evaluator

The prompt injection evaluator can be run from the command line with the following syntax:

```bash
python prompt_injection_evaluator.py [--lines N]
```

#### Arguments

- `--lines`: (Optional) Maximum number of lines to process from the dataset. If not specified, processes the entire dataset.

#### Example Commands

```bash
# Process the entire dataset
python prompt_injection_evaluator.py

# Process only the first 50 lines
python prompt_injection_evaluator.py --lines 50
```

## Input Dataset Format

The input CSV files should contain the following columns, separated by the `|` character:
- First column: The text to be evaluated
- Second column: The expected result (`true` or `false`)

Example:
```
"Hello, my name is John Doe"|true
"Hello, how are you?"|false
```

Note: The unified evaluator expects the `|` character as a separator, while the specialized evaluators use comma-separated format.

### Included Datasets

The project includes two pre-prepared datasets:

1. **PII Dataset** (`pii_dataset.csv`):
   - Contains 1,500 samples with various types of personal information
   - Includes examples of names, addresses, phone numbers, emails, and other PII
   - Balanced distribution of positive and negative cases

2. **Prompt Injection Dataset** (`prompt_inject_dataset.csv`):
   - Contains 1,500 samples of potential prompt injection attempts
   - Covers various injection techniques and patterns
   - Includes both malicious and benign prompts for comparison

## Output

Each evaluator generates two types of output:

1. **Console Output**:
   - Evaluation metrics (accuracy, precision, recall, F1 score)
   - Confusion matrix
   - Latency statistics

2. **CSV File**:
   - Contains detailed results for each evaluated prompt
   - Columns: prompt, expected, detected, confidence, elapsed_time

## Architecture

Both evaluators use a workflow-based architecture with the following components:

1. **LoadDatasetNode**: Loads and parses the input dataset
2. **ScanPromptsNode**: Processes prompts in batches using the CalypsoAI API
3. **SaveResultsNode**: Saves detailed results to a CSV file
4. **EvaluateAccuracyNode**: Calculates accuracy metrics
5. **DisplayResultsNode**: Formats and displays evaluation results
6. **LatencyStatsNode**: Calculates and displays latency statistics

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

[Specify your license here]

## Acknowledgments

- CalypsoAI for providing the scanning API
- PocketFlow framework for the workflow architecture 
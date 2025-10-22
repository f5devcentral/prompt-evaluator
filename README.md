# Prompt Evaluator

A comprehensive tool for evaluating AI-powered scanners in detecting various types of content using CalypsoAI API and AWS Bedrock Guardrail.

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment variables:**
   Create a `.env` file with your API credentials:
   ```
   CALYPSOAI_URL=https://calypsoai.app
   CALYPSOAI_TOKEN=your_api_token_here
   GUARDRAIL_ID=your_guardrail_id
   GUARDRAIL_VERSION=1
   ```

3. **Run evaluation:**
   ```bash
   python prompt_evaluator.py --input datasets/prompt_inject_dataset.csv
   ```

## Features

- **Flexible Evaluation**: Works with any CSV dataset
- **Batch Processing**: Efficiently process large datasets
- **Multiple Scanners**: CalypsoAI and AWS Bedrock Guardrail support
- **Comprehensive Metrics**: Accuracy, precision, recall, F1 score, latency stats
- **False Positives/Negatives Export**: Automatic export for troubleshooting
- **Browser Extension**: Chrome extension for real-time evaluation
- **Dataset Management**: Download from Hugging Face, convert existing datasets

## Documentation

- **[Installation Guide](docs/installation.md)** - Detailed setup instructions
- **[Usage Guide](docs/usage.md)** - Complete usage examples and options
- **[Dataset Management](docs/datasets.md)** - Working with datasets and Hugging Face
- **[Troubleshooting](docs/troubleshooting.md)** - Common issues and solutions
- **[Contributing](docs/contributing.md)** - How to contribute to the project

## Available Evaluators

| Evaluator | Description | Use Case |
|-----------|-------------|----------|
| `prompt_evaluator.py` | Standard CalypsoAI evaluation | General purpose evaluation |
| `prompt_evaluator_prompts.py` | Advanced CalypsoAI with LLM responses | Detailed analysis with full responses |
| `guardrail_evaluator.py` | AWS Bedrock Guardrail evaluation | AWS ecosystem integration |
| `evaluate_existing_results.py` | Calculate metrics from existing results | Re-analyze without re-scanning |

## Sample Datasets

The project includes several sample datasets in the `datasets/` folder:
- `promptinject-codesagar_malicious_llm_prompts_v4_test.csv` - Prompt injection examples
- `pii_dataset.csv` - Personally identifiable information examples
- `fin_advice_dataset.csv` - Financial advice prompts
- `eu-ai-act-prompts.csv` - EU AI Act compliance prompts

## Browser Extension

A Chrome extension is available in the `prompt-evaluator-extension/` folder for real-time prompt evaluation on popular AI platforms.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please see our [Contributing Guide](docs/contributing.md) for details.
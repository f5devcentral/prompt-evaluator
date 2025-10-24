# Installation Guide

## Prerequisites

- Python 3.6+
- CalypsoAI API access and credentials

## Installation Steps

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd <repository-directory>
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables:**
   Create a `.env` file in the project root with the following content:
   ```
   CALYPSOAI_URL=https://calypsoai.app
   CALYPSOAI_TOKEN=your_api_token_here
   ```

## Platform Configuration

### CalypsoAI Platform Configuration

Before running the evaluator, ensure you have configured the appropriate scanners in your CalypsoAI platform:

- Enable only the scanners relevant to your use case
- Consider running evaluations in isolation by enabling specific scanner sets
- This helps ensure accurate results and prevents cross-scanner interference

You can configure your scanners through the CalypsoAI platform's web interface under the Scanner Settings section.


## Verification

To verify your installation, run:

```bash
python validate_setup.py
```

This will check that all dependencies are installed and your environment variables are configured correctly.

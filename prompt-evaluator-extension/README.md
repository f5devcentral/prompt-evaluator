# Prompt Evaluator Chrome Extension

A Chrome extension for evaluating prompts using the CalypsoAI API to detect potential injection attacks.

## Features

- Evaluate prompts for potential injection attacks
- Works on popular AI platforms (OpenAI, Anthropic, Google, etc.)
- Simple and intuitive interface
- Secure API key storage

## Installation

### From Chrome Web Store (Coming Soon)

1. Visit the Chrome Web Store
2. Search for "Prompt Evaluator"
3. Click "Add to Chrome"

### Manual Installation (Developer Mode)

1. Download or clone this repository
2. Open Chrome and navigate to `chrome://extensions/`
3. Enable "Developer mode" in the top-right corner
4. Click "Load unpacked" and select the `prompt-evaluator-extension` folder
5. The extension should now be installed and visible in your Chrome toolbar

## Usage

1. Click the Prompt Evaluator icon in your Chrome toolbar
2. Go to the "Settings" tab and enter your CalypsoAI API key
3. Go to the "Evaluate" tab and enter a prompt to evaluate
4. Click "Evaluate Prompt" to see the results
5. The extension will show whether the prompt is safe or vulnerable to injection attacks

## API Key

You need a CalypsoAI API key to use this extension. You can obtain one by:

1. Visiting the [CalypsoAI website](https://calypsoai.com)
2. Creating an account
3. Generating an API key in your account settings

## Development

### Project Structure

- `manifest.json` - Extension configuration
- `popup.html` - Extension popup UI
- `popup.js` - Popup functionality
- `content.js` - Content script that runs on web pages
- `background.js` - Background script for extension functionality
- `src/agents/` - Contains the agent classes
  - `BaseAgent.js` - Base agent class with common functionality
  - `BatchAgent.js` - Agent for processing items in batches
  - `CalypsoAgent.js` - Agent for interacting with the CalypsoAI API

### Building from Source

1. Clone the repository
2. Install dependencies:
   ```bash
   npm install
   ```
3. Load the extension in Chrome as described in the Installation section

## License

MIT 
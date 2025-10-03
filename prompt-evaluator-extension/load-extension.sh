#!/bin/bash

# Get the absolute path of the extension directory
EXTENSION_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "====================================================="
echo "CalypsoAI Prompt Evaluator - Chrome Extension Loader"
echo "====================================================="
echo ""
echo "This script will help you load the CalypsoAI Prompt Evaluator extension in Chrome."
echo ""
echo "Extension directory: $EXTENSION_DIR"
echo ""
echo "Instructions:"
echo "1. Open Chrome"
echo "2. Go to chrome://extensions/"
echo "3. Enable 'Developer mode' (toggle in the top-right corner)"
echo "4. Click 'Load unpacked'"
echo "5. Select the following directory:"
echo "   $EXTENSION_DIR"
echo ""
echo "Note: You will need to set your CalypsoAI API key in the extension settings before use."
echo ""

# Try to open the Chrome extensions page based on OS
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    open -a "Google Chrome" chrome://extensions/
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    google-chrome chrome://extensions/
elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    # Windows
    start chrome chrome://extensions/
else
    echo "Could not automatically open Chrome. Please open chrome://extensions/ manually."
fi

echo ""
echo "After loading the extension, you can click the extension icon in your Chrome toolbar to use it."
echo ""
echo "Note: You will need to set your CalypsoAI API key in the extension settings before using it."
echo "" 
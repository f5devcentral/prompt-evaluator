#!/bin/bash

# Get the absolute path of the extension directory
EXTENSION_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PACKAGE_DIR="$EXTENSION_DIR/package"

echo "Prompt Evaluator Extension Packager"
echo "=================================="
echo ""
echo "This script will package the extension for testing."
echo ""
echo "Extension directory: $EXTENSION_DIR"
echo "Package directory: $PACKAGE_DIR"
echo ""

# Create package directory if it doesn't exist
mkdir -p "$PACKAGE_DIR"

# Copy necessary files to package directory
echo "Copying files to package directory..."
cp -r "$EXTENSION_DIR/manifest.json" "$PACKAGE_DIR/"
cp -r "$EXTENSION_DIR/popup.html" "$PACKAGE_DIR/"
cp -r "$EXTENSION_DIR/popup.js" "$PACKAGE_DIR/"
cp -r "$EXTENSION_DIR/content.js" "$PACKAGE_DIR/"
cp -r "$EXTENSION_DIR/background.js" "$PACKAGE_DIR/"
cp -r "$EXTENSION_DIR/icons" "$PACKAGE_DIR/"
cp -r "$EXTENSION_DIR/src" "$PACKAGE_DIR/"

# Create a zip file
echo "Creating zip file..."
cd "$EXTENSION_DIR"
zip -r "prompt-evaluator-extension.zip" "package"

echo ""
echo "Package created: $EXTENSION_DIR/prompt-evaluator-extension.zip"
echo ""
echo "To load the extension in Chrome:"
echo "1. Open Chrome and navigate to chrome://extensions/"
echo "2. Enable 'Developer mode' in the top-right corner"
echo "3. Click 'Load unpacked' and select the 'package' directory"
echo "   or drag and drop the zip file onto the extensions page"
echo "" 
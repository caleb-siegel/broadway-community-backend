#!/bin/bash

set -e  # Exit on error
set -x  # Print commands as they're executed

echo "Starting ChromeDriver installation..."

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
echo "Script directory: $SCRIPT_DIR"

# Download and install ChromeDriver
echo "Installing ChromeDriver..."
CHROME_VERSION="121"  # Use a specific version that matches Vercel's Chrome
CHROMEDRIVER_VERSION=$(curl -sS "https://chromedriver.storage.googleapis.com/LATEST_RELEASE_$CHROME_VERSION")
echo "Installing ChromeDriver version: $CHROMEDRIVER_VERSION"

wget -q -O /tmp/chromedriver.zip "https://chromedriver.storage.googleapis.com/$CHROMEDRIVER_VERSION/chromedriver_linux64.zip"
unzip -o /tmp/chromedriver.zip -d "$SCRIPT_DIR"
chmod +x "$SCRIPT_DIR/chromedriver"

echo "ChromeDriver installation completed. Verifying installation..."
ls -la "$SCRIPT_DIR/chromedriver"
"$SCRIPT_DIR/chromedriver" --version

# Check Chrome installation
echo "Checking Chrome installation..."
for chrome_path in "/opt/google/chrome/chrome" "/usr/bin/google-chrome" "/usr/bin/google-chrome-stable"; do
    if [ -f "$chrome_path" ]; then
        echo "Chrome found at: $chrome_path"
        "$chrome_path" --version
        break
    fi
done

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

echo "Installation completed successfully!" 
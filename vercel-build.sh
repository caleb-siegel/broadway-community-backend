#!/bin/bash

set -e  # Exit on error
set -x  # Print commands as they're executed

echo "Starting Chrome installation..."

# Create necessary directories
mkdir -p /var/task

# Download and install ChromeDriver
echo "Installing ChromeDriver..."
CHROME_VERSION="121"  # Use a specific version that matches Vercel's Chrome
CHROMEDRIVER_VERSION=$(curl -sS "https://chromedriver.storage.googleapis.com/LATEST_RELEASE_$CHROME_VERSION")
echo "Installing ChromeDriver version: $CHROMEDRIVER_VERSION"

wget -q -O /tmp/chromedriver.zip "https://chromedriver.storage.googleapis.com/$CHROMEDRIVER_VERSION/chromedriver_linux64.zip"
unzip -o /tmp/chromedriver.zip -d /var/task/
chmod +x /var/task/chromedriver

echo "ChromeDriver installation completed. Verifying installation..."
ls -la /var/task/chromedriver
/var/task/chromedriver --version

# Install Python dependencies
pip install -r requirements.txt

echo "Installation completed successfully!" 
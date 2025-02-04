#!/bin/bash

set -e  # Exit on error
set -x  # Print commands as they're executed

echo "Starting ChromeDriver installation..."

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
echo "Script directory: $SCRIPT_DIR"

# Install Chrome
echo "Installing Chrome..."
apt-get update
apt-get install -y wget gnupg2
wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add -
echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google.list
apt-get update
apt-get install -y google-chrome-stable

# Create directory for Chrome
mkdir -p /var/chrome
ln -s /usr/bin/google-chrome-stable /var/chrome/chrome

# Install ChromeDriver
echo "Installing ChromeDriver..."
CHROME_VERSION=$(google-chrome --version | cut -d " " -f3 | cut -d "." -f1)
CHROMEDRIVER_VERSION=$(curl -s "https://chromedriver.storage.googleapis.com/LATEST_RELEASE_${CHROME_VERSION}")
wget -q -O /tmp/chromedriver.zip "https://chromedriver.storage.googleapis.com/${CHROMEDRIVER_VERSION}/chromedriver_linux64.zip"
unzip -o /tmp/chromedriver.zip -d /var/chrome/
chmod +x /var/chrome/chromedriver

# Verify installations
echo "Verifying installations..."
/var/chrome/chrome --version
/var/chrome/chromedriver --version

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

echo "Installation completed successfully!" 
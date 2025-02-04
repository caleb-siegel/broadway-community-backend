#!/bin/bash

set -e  # Exit on error
set -x  # Print commands as they're executed

echo "Starting Chrome installation..."

# Create necessary directories
mkdir -p /opt/google/chrome
mkdir -p /usr/local/bin

# Install required dependencies
apt-get update
apt-get install -y wget unzip gnupg2

# Install Chrome
echo "Downloading Chrome..."
wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add -
echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google.list
apt-get update
apt-get install -y google-chrome-stable

# Create symlinks to ensure Chrome is findable
ln -sf /usr/bin/google-chrome-stable /usr/bin/google-chrome
ln -sf /usr/bin/google-chrome-stable /opt/google/chrome/chrome

echo "Chrome installation completed. Verifying installation..."
ls -la /usr/bin/google-chrome*
ls -la /opt/google/chrome/
google-chrome --version

# Install ChromeDriver
echo "Installing ChromeDriver..."
CHROME_VERSION=$(google-chrome --version | cut -d " " -f3 | cut -d "." -f1)
echo "Detected Chrome version: $CHROME_VERSION"

CHROMEDRIVER_VERSION=$(curl -sS "https://chromedriver.storage.googleapis.com/LATEST_RELEASE_$CHROME_VERSION")
echo "Installing ChromeDriver version: $CHROMEDRIVER_VERSION"

wget -q -O /tmp/chromedriver.zip "https://chromedriver.storage.googleapis.com/$CHROMEDRIVER_VERSION/chromedriver_linux64.zip"
unzip -o /tmp/chromedriver.zip -d /usr/local/bin/
chmod +x /usr/local/bin/chromedriver

echo "ChromeDriver installation completed. Verifying installation..."
ls -la /usr/local/bin/chromedriver
chromedriver --version

# Set environment variables
echo "Setting environment variables..."
export CHROME_BIN=/usr/bin/google-chrome-stable
export CHROMEDRIVER_PATH=/usr/local/bin/chromedriver

# Print final system state
echo "Final system state:"
echo "Chrome locations:"
which google-chrome
which google-chrome-stable
ls -la /opt/google/chrome/
echo "ChromeDriver location:"
which chromedriver

echo "Installation completed successfully!" 
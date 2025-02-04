#!/bin/bash

set -e  # Exit on error
set -x  # Print commands as they're executed

echo "Starting Chrome installation..."

# Install required dependencies
apt-get update
apt-get install -y wget unzip

# Install Chrome
echo "Downloading Chrome..."
wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add -
sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list'
apt-get update
apt-get install -y google-chrome-stable

echo "Chrome installation completed. Verifying installation..."
which google-chrome
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
which chromedriver
chromedriver --version

# Set environment variables
echo "Setting environment variables..."
export CHROME_BIN=/usr/bin/google-chrome
export CHROMEDRIVER_PATH=/usr/local/bin/chromedriver

echo "Installation completed successfully!" 
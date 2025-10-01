#!/bin/bash
# Install Chrome
apt-get update && apt-get install -y wget gnupg unzip
wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add -
echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list
apt-get update && apt-get install -y google-chrome-stable

# Download chromedriver matching Chrome version
CHROME_VERSION=$(google-chrome --version | cut -d " " -f3 | cut -d "." -f1)
DRIVER_VERSION=$(curl -s "https://chromedriver.storage.googleapis.com/LATEST_RELEASE_$CHROME_VERSION")
wget -q "https://chromedriver.storage.googleapis.com/${DRIVER_VERSION}/chromedriver_linux64.zip"
unzip chromedriver_linux64.zip -d /usr/local/bin/
rm chromedriver_linux64.zip

# Start your app
python app.py

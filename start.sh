# #!/bin/bash
# # Install Chrome
# apt-get update && apt-get install -y wget gnupg unzip
# wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add -
# echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list
# apt-get update && apt-get install -y google-chrome-stable

# # Download chromedriver matching Chrome version
# CHROME_VERSION=$(google-chrome --version | cut -d " " -f3 | cut -d "." -f1)
# DRIVER_VERSION=$(curl -s "https://chromedriver.storage.googleapis.com/LATEST_RELEASE_$CHROME_VERSION")
# wget -q "https://chromedriver.storage.googleapis.com/${DRIVER_VERSION}/chromedriver_linux64.zip"
# unzip chromedriver_linux64.zip -d /usr/local/bin/
# rm chromedriver_linux64.zip

# # Start your app
# python app.py


#!/bin/bash

# Exit on any error
set -e

echo "================================"
echo "GE Ltd Tender Scraper Starting"
echo "================================"

# Verify Chrome installation
echo "Checking Chrome installation..."
if command -v google-chrome &> /dev/null; then
    CHROME_VERSION=$(google-chrome --version)
    echo "✓ Chrome installed: $CHROME_VERSION"
else
    echo "✗ Chrome not found!"
    exit 1
fi

# Verify ChromeDriver installation
echo "Checking ChromeDriver installation..."
if command -v chromedriver &> /dev/null; then
    CHROMEDRIVER_VERSION=$(chromedriver --version)
    echo "✓ ChromeDriver installed: $CHROMEDRIVER_VERSION"
else
    echo "✗ ChromeDriver not found!"
    exit 1
fi

# Check Python version
echo "Checking Python version..."
PYTHON_VERSION=$(python --version)
echo "✓ Python: $PYTHON_VERSION"

# Verify NLTK data
echo "Verifying NLTK data..."
python -c "import nltk; nltk.data.find('tokenizers/punkt'); nltk.data.find('corpora/stopwords')" && \
    echo "✓ NLTK data available" || \
    (echo "Downloading NLTK data..." && python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords')")

# Set default port if not provided
PORT=${PORT:-8080}
echo "Starting application on port $PORT..."

# Run the application
exec python app.py

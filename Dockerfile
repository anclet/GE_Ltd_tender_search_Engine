# Use Python 3.11 slim base
FROM python:3.11-slim

# Prevent interactive prompts during apt install
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies including curl (required for ChromeDriver version check)
RUN apt-get update && apt-get install -y \
    curl wget gnupg ca-certificates unzip \
    libx11-xcb1 libxcomposite1 libxcursor1 libxdamage1 libxi6 libxtst6 \
    libnss3 libgbm1 libxss1 libasound2 libatk1.0-0 libatk-bridge2.0-0 \
    libcups2 libdrm2 libxrandr2 libpangocairo-1.0-0 libxkbcommon0 \
    fonts-liberation lsb-release xdg-utils \
    && rm -rf /var/lib/apt/lists/*

# Install Google Chrome
RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /usr/share/keyrings/google-chrome-keyring.gpg \
    && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google-chrome-keyring.gpg] http://dl.google.com/linux/chrome/deb/ stable main" | tee /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# Install latest ChromeDriver using curl (now available)
RUN CHROMEDRIVER_VERSION=$(curl -sS https://chromedriver.storage.googleapis.com/LATEST_RELEASE) \
    && echo "Installing ChromeDriver: $CHROMEDRIVER_VERSION" \
    && wget -q --no-check-certificate -O /tmp/chromedriver.zip https://chromedriver.storage.googleapis.com/$CHROMEDRIVER_VERSION/chromedriver_linux64.zip \
    && unzip /tmp/chromedriver.zip -d /tmp \
    && mv /tmp/chromedriver /usr/local/bin/ \
    && chmod +x /usr/local/bin/chromedriver \
    && rm /tmp/chromedriver.zip

# Set up app
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .
RUN python -c "import nltk; nltk.download('punkt', quiet=True); nltk.download('stopwords', quiet=True)"

# Expose port (for clarity; Render uses PORT env var)
EXPOSE 8080

# Run app
CMD ["python", "app.py"]
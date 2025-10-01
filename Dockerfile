FROM python:3.11-slim

# Install dependencies
RUN apt-get update && apt-get install -y \
    wget gnupg unzip curl xvfb \
    && rm -rf /var/lib/apt/lists/*

# Copy files
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Expose port (Gradio usually runs on 7860, Render expects $PORT)
ENV PORT=7860

CMD ["./start.sh"]

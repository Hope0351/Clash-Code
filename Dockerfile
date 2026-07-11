FROM python:3.12-slim

WORKDIR /app

# Install system dependencies for unstructured
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    libxml2-dev \
    libxslt1-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash appuser && \
    chown -R appuser:appuser /app
USER appuser

# Run the application on port 8080
EXPOSE 8080
ENTRYPOINT ["streamlit", "run", "app.py", \
    "--theme.base=dark", \
    "--theme.primaryColor=#77dd77", \
    "--server.port=8080", \
    "--server.enableCORS=false", \
    "--server.enableWebsocketCompression=false", \
    "--server.address=0.0.0.0", \
    "--server.headless=true"]
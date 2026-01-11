# Use official Python slim image for smaller size
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    STREAMLIT_SERVER_PORT=8080 \
    STREAMLIT_THEME_BASE=dark \
    STREAMLIT_THEME_PRIMARY_COLOR=#77dd77 \
    STREAMLIT_SERVER_ENABLE_CORS=false \
    STREAMLIT_SERVER_ENABLE_WEBSOCKET_COMPRESSION=false \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gnupg \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user
RUN useradd --create-home --shell /bin/bash appuser && \
    chown -R appuser:appuser /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY --chown=appuser:appuser . .

# Switch to non-root user
USER appuser

# Create directory for Streamlit config
RUN mkdir -p /home/appuser/.streamlit && \
    echo "[theme]\n\
    base=\"dark\"\n\
    primaryColor=\"#77dd77\"\n\
    \n\
    [server]\n\
    port = 8080\n\
    enableCORS = false\n\
    enableWebsocketCompression = false\n\
    address = \"0.0.0.0\"\n\
    \n\
    [browser]\n\
    gatherUsageStats = false\n" > /home/appuser/.streamlit/config.toml

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/_stcore/health || exit 1

# Expose port
EXPOSE 8080

# Run the application
ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8080", "--server.address=0.0.0.0"]

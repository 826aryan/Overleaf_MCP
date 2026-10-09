# Use the official Microsoft Playwright image with Python 3.12 pre-installed with Chromium and all OS dependencies
FROM mcr.microsoft.com/playwright/python:v1.49.0-noble

WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    OVERLEAF_HEADLESS=true \
    MCP_HOST=0.0.0.0 \
    MCP_PORT=8000 \
    MCP_TRANSPORT=sse

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install chromium browsers for playwright inside container
RUN playwright install chromium

# Copy application files
COPY . .

# Expose port
EXPOSE 8000

# Start MCP server with SSE transport
CMD ["python3", "main.py", "--transport", "sse", "--host", "0.0.0.0", "--port", "8000"]

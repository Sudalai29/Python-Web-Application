# -------- Stage 1: Build Stage --------
FROM python:3.12-slim AS build

# Set work directory
WORKDIR /app

# Install build dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        gcc \
        curl \
        && rm -rf /var/lib/apt/lists/*

# Upgrade pip
RUN python -m pip install --upgrade pip

# Copy requirements first (for caching)
COPY requirements.txt .

# Install Python dependencies
RUN python -m pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# -------- Stage 2: Production Stage --------
FROM python:3.12-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends libpq5 curl && \
    rm -rf /var/lib/apt/lists/*

# Ensure pip-installed scripts are on PATH
ENV PATH="/usr/local/bin:$PATH"

# Copy installed Python packages from build stage
COPY --from=build /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=build /app /app

# Expose Flask port
EXPOSE 5000

# Environment variables (can override with docker run -e)
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_RUN_PORT=5000

# Run the Flask app
CMD ["python", "-m", "flask", "run"]

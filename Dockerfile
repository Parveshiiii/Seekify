FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY . .

# Install dependencies and the package
RUN pip install --no-cache-dir .

# Default command matches the CLI entry point
ENTRYPOINT ["seekify"]
CMD ["--help"]

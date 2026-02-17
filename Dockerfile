FROM python:3.12-slim

WORKDIR /app

# Install dependencies first (layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source and install package
COPY src/ ./src/
COPY pyproject.toml .
RUN pip install --no-cache-dir .

# Run as non-root user
RUN useradd --create-home --shell /bin/bash appuser
USER appuser

# Container mode for dtPyAppFramework
ENV CONTAINER_MODE=true

ENTRYPOINT ["python", "-m", "dtjiramcpserver"]

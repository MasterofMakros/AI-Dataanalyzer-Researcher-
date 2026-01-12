
FROM python:3.11-slim-bookworm

WORKDIR /app

# Install system dependencies
# - build-essential for compiling some python libs
# - git for cloning repositories
# - libgl1 for OpenCV (replacement for libgl1-mesa-glx)
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
# Using CPU-only PyTorch to save space
RUN pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu

# Install Core Libraries
RUN pip install --no-cache-dir \
    docling \
    gliner \
    rustworkx \
    lancedb \
    sentence-transformers \
    fastapi \
    uvicorn \
    python-multipart \
    pydantic

# Copy Application Code
COPY . /app

# Expose API Port
EXPOSE 8000

# Run API
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

FROM python:3.11-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends exiftool \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY metadata_service.py ./metadata_service.py

ENV EXIFTOOL_BIN=exiftool
ENV EXIFTOOL_TIMEOUT=30

EXPOSE 8000

CMD ["uvicorn", "metadata_service:app", "--host", "0.0.0.0", "--port", "8000"]

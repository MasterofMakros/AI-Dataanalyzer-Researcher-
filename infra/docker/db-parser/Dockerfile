# DB Parser Service
FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    mdbtools \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY db_parser.py /app/db_parser.py
COPY app.py /app/app.py

WORKDIR /app
EXPOSE 8010

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8010"]

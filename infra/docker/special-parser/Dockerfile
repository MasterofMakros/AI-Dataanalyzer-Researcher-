FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY special_parser_service.py .
COPY special_parser_core.py .

EXPOSE 8015

CMD ["uvicorn", "special_parser_service:app", "--host", "0.0.0.0", "--port", "8015"]

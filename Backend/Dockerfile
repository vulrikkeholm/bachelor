FROM python:3-alpine

WORKDIR /Backend

COPY . .

RUN pip install --no-cache-dir -r requirements.txt

CMD ["sh", "-c", "uvicorn main:socket_app, --host 0.0.0.0, --port ${PORT:-8000}"]

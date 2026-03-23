FROM python:3-alpine

WORKDIR /Backend

COPY . .

ENV PYTHONDONTWRITEBYTECODE = 1

RUN pip install --no-cache-dir -r requirements.txt

CMD [ "uvicorn","main:app", "--reload"]


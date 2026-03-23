FROM python:3-alpine

WORKDIR /Backend

COPY . .

RUN pip install --no-cache-dir -r requirements.txt

CMD [ "uvicorn","main:app", "--reload"]


FROM python:alpine

WORKDIR /Backend

COPY . .

RUN pip instal --no-cache-dir -r requirements.txt

CMD [ "uvicorn","main:app", "--reload"]


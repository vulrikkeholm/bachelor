FROM python:3-alpine

WORKDIR /Backend

COPY . .

ENV DATABASE_URL="postgresql://postgres:kIrUOnFFulezbePpszmFGnMpYiPQSdlB@centerbeam.proxy.rlwy.net:49068/railway"

ENV JWT_SECRET_KEY="78d15d862465c5363a30406a8e163dbaabb8a78f330f448542bb99896016ff9f86cb7d97c95df8c1b9490a3c9b2fb3e578b69e0b88af0884d2f06670bd143894"

ENV JWT_ALGORITHM="HS265"

RUN pip install --no-cache-dir -r requirements.txt

CMD [ "uvicorn","main:app", "--host", "0.0.0.0"]


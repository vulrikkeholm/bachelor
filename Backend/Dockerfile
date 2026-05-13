FROM python:3-alpine

ARG USERNAME=backenduser
ARG USER_UID=1000
ARG USER_GID=$USER_UID

# Create the user
RUN addgroup -g $USER_GID $USERNAME \
    && adduser -u $USER_UID -G $USERNAME -s /bin/sh -D $USERNAME 

WORKDIR /Backend

COPY . .

RUN pip install --no-cache-dir -r requirements.txt

USER $USERNAME

CMD [ "uvicorn","main:socket_app", "--host", "0.0.0.0"]

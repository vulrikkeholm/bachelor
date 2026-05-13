FROM python:3-alpine

ARG USERNAME=backenduser
ARG USER_UID=1000
ARG USER_GID=$USER_UID

# Create the user
RUN addgroup --gid $USER_GID $USERNAME \
    && adduser --uid $USER_UID --gid $USER_GID -m $USERNAME 

WORKDIR /Backend

COPY . .

RUN pip install --no-cache-dir -r requirements.txt

USER $USERNAME

CMD [ "uvicorn","main:socket_app", "--host", "0.0.0.0"]

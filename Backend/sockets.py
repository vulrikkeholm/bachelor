import socketio

#Creating socketio server
sio_server = socketio.AsyncServer(
    async_mode='asgi', #FastAPI is an ASGI application
    cors_allowed_origins=[
        "http://localhost:5173",
        "https://frontend.smaas.dk",
    ] 
)

@sio_server.event
async def connect(sid, environ, auth):
    print(f"{sid}: connected")
    await sio_server.emit('join', {'sid': sid})

@sio_server.event
async def chat(sid, message):
    msg = {
        "sid": sid, 
        "message": message["text"]
    }
    await sio_server.emit('chat', msg) #chat is the message type, so the frontend knows what message to display

@sio_server.event
async def disconnect(sid):
    print(f"{sid}: disconnected")
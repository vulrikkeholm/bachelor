import socketio
#Creating socketio server
sio_server = socketio.AsyncServer(
    async_mode='asgi', #FastAPI is an ASGI application
    #cors_allowed_origins=[
     #   "http://localhost:5173",
     #   "https://frontend.smaas.dk",
    ],
    #socketio_path = "sockets"
)
@sio_server.event
async def connect(sid, environ, auth):
    #Måske noget user id skal tilføjes, noget sammenhæng med login
    print(f"{sid}: connected")
    await sio_server.emit('join', {'sid': sid})

@sio_server.event
async def joinRoom(sid, room):
    await sio_server.enter_room(sid, room)
    print(f"{sid} joined room {room}")

@sio_server.event
async def chat(sid, data):
    room = data["room"]
    if not room:
        print(f"No room specified")
        return

    msg = {
        "sid": sid, 
        "text": data["text"],
        "room": room
    }
    await sio_server.emit('chat', msg, room=room) #chat is the message type, so the frontend knows what message to display

@sio_server.event
async def disconnect(sid):
    print(f"{sid}: disconnected")

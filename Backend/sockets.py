import socketio

#Creating socketio server
sio_server = socketio.AsyncServer(
    async_mode='asgi', #FastAPI is an ASGI application
    cors_allowed_origins=[] #List of origins that the socket server should allow (den skal være tom, fordi FastAPI står for det)
)

#sio_app = socketio.ASGIApp(
 #   socketio_server = sio_server,
  #  socketio_path = 'sockets' #Which path it will be running in (the endpoint)
#)

@sio_server.event
async def connect(sid, environ, auth):
    print(f"{sid}: connected")
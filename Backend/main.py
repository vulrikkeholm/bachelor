from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from db.base import create_db_and_tables
from endpoints import user, auth, mess, keys
#from socket_server import app_sio  # Socket.IO ASGI app
from sockets  import sio_server
import socketio
from db.session import get_db
from models.user_model import User
from models.keys_model import Keys
from sqlmodel import Session, select
from endpoints.public_keys import router as public_keys_router

app = FastAPI()
#FastAPI app gets mounted to sockets (or other way around?), so that all the traffic FastAPI gets is routed through socketio
#app.mount('/', app=sio_app) #Want it mounted at the root
# Mount Socket.IO under /ws
#app.mount("/ws", app_sio)
origins = [
    "http://localhost:5173",
    "https://frontend.smaas.dk",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.include_router(user.router, prefix="/users")
app.include_router(auth.router, prefix="/auth")
app.include_router(mess.router, prefix="/messages")
app.include_router(keys.router, prefix="/aes-keys")
app.include_router(public_keys_router, prefix="/keys")

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

sio_server.cors_allowed_origins = origins

# Wrap FastAPI inside Socket.IO
socket_app = socketio.ASGIApp(
    socketio_server=sio_server,
    other_asgi_app=app,       
    socketio_path="sockets" 
)

#app.mount("/ws", socket_app)
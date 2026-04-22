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
fastapi_app = FastAPI()
#FastAPI app gets mounted to sockets (or other way around?), so that all the traffic FastAPI gets is routed through socketio
#app.mount('/', app=sio_app) #Want it mounted at the root
# Mount Socket.IO under /ws
#app.mount("/ws", app_sio)
origins = [
    "http://localhost:5173",
    "https://frontend.smaas.dk",
]

fastapi_app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

fastapi_app.include_router(user.router, prefix="/users")
fastapi_app.include_router(auth.router, prefix="/auth")
fastapi_app.include_router(mess.router, prefix="/messages")
fastapi_app.include_router(keys.router, prefix="/aes-keys")
fastapi_app.include_router(public_keys_router, prefix="/keys")

@fastapi_app.on_event("startup")
def on_startup():
    create_db_and_tables()

# Wrap FastAPI inside Socket.IO
spcket_app = socketio.ASGIApp(
    socketio_server=sio_server,
    socketio_path="sockets"
)

fastapi_app.mount("/ws", socket_app)


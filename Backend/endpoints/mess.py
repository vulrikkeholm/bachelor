from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from models import MessageCreate

router = APIRouter()

messages = []
'''
def message_send(sender: int, receiver: int, message: str, db: Session):
    try:
        while True:
            #Send (encrypted) message
            message = input('message> ').strip()
            encrypted_msg = fernet.encrypt(message.encode())
            sock.send(encrypted_msg)
            print('...')

            # wait response
            response = sock.recv(1024)
            response_decrypted = fernet.decrypt(response)
            print(f'server> {response_decrypted.decode()}')
    except KeyboardInterrupt:
        print('Bye.')
        sock.close()
'''

@router.post("/messages")
def send_message(data: MessageCreate):
    msg = {
        "sender": data.sender,
        "receiver": data.receiver,
        "message": data.message
    }
    
    messages.append(msg)

    return {"status": "sent"} 


#@router.get("/messages")
#def get_messages()
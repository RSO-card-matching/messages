# pylint: disable=no-name-in-module

from datetime import datetime, timedelta
from typing import Optional, List
from os import getenv

from fastapi import Depends, FastAPI, Form, HTTPException, Path, status
from fastapi.security import OAuth2PasswordBearer
from fastapi.middleware.cors import CORSMiddleware
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from . import models, database


SECRET_KEY = getenv("OAUTH_SIGN_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

if (SECRET_KEY == None):
    print("Please define OAuth signing key!")
    exit(-1)

# fastAPI dependecy magic
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

if (getenv("OAUTH_TOKEN_PROVIDER") == None):
    print("Please provide token provider URL!")
    exit(-1)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl = getenv("OAUTH_TOKEN_PROVIDER") + "/tokens")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex = r"https:\/\/.*cardmatching.ovh.*",
    allow_credentials = True,
    allow_methods = ["*"],
    allow_headers = ["*"],
)



async def get_current_user_from_token(token: str = Depends(oauth2_scheme)) -> int:
    credentials_exception = HTTPException(
        status_code = status.HTTP_401_UNAUTHORIZED,
        detail = "Could not validate credentials",
        headers = {"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms = [ALGORITHM])
        uid: Optional[int] = int(payload.get("sub"))
        if uid is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    return uid



@app.get("/v1/messages", response_model = List[models.Message])
async def return_all_messages(sender_id: Optional[int] = None,
        receiver_id: Optional[int] = None,
        read_status: Optional[bool] = None,
        current_user: int = Depends(get_current_user_from_token),
        db: Session = Depends(get_db)):
    return database.get_all_messages(db, sender_id, receiver_id, read_status)


@app.get("/v1/messages/{msg_id}", response_model = models.Message)
async def return_specific_message(current_user: int = Depends(get_current_user_from_token),
    msg_id: int = Path(...),
    db: Session = Depends(get_db)):
    ret = database.get_message_by_id(db, msg_id)
    if (ret == None):
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail = "Message with given ID not found",
        )
    return ret


@app.post("/v1/messages", response_model = models.NewMessageID)
async def send_message(message: models.MessageNew,
        current_user: int = Depends(get_current_user_from_token),
        db: Session = Depends(get_db)):
    new_id = database.insert_new_message(db, current_user, message)
    return models.NewMessageID(id = new_id)


@app.get("/v1/messages/{msg_id}/read", response_model = bool)
async def return_message_read_status(current_user: int = Depends(get_current_user_from_token),
    msg_id: int = Path(...),
    db: Session = Depends(get_db)):
    ret = database.get_message_by_id(db, msg_id)
    if (ret == None):
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail = "Message with given ID not found",
        )
    return ret.read_status


@app.post("/v1/messages/{msg_id}/read", response_model = None)
async def mark_message_as_read(current_user: int = Depends(get_current_user_from_token),
        msg_id = Path(...),
        db: Session = Depends(get_db)):
    message = database.get_message_by_id(db, msg_id)
    if (message == None):
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail = "Message with given ID not found",
        )
    if message.receiver_id != current_user:
        raise HTTPException(
            status_code = status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail = "Cannot mark someone else's message as read",
        )
    database.mark_message_as_read(db, message.id)


@app.post("/v1/messages/{msg_id}/unread", response_model = None)
async def mark_message_as_unread(current_user: int = Depends(get_current_user_from_token),
        msg_id = Path(...),
        db: Session = Depends(get_db)):
    message = database.get_message_by_id(db, msg_id)
    if (message == None):
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail = "Message with given ID not found",
        )
    if message.receiver_id != current_user:
        raise HTTPException(
            status_code = status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail = "Cannot mark someone else's message as unread",
        )
    database.mark_message_as_unread(db, message.id)


@app.delete("/v1/messages/{msg_id}", response_model = None)
async def remove_sample(msg_id: int = Path(...),
        current_user: int = Depends(get_current_user_from_token),
        db: Session = Depends(get_db)):
    try:
        database.delete_message(db, msg_id) # TODO: čekiranje, če je pravi user?
    except database.DBException:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail = "Sample with given ID not found"
        )



@app.get("/health/live", response_model = str)
async def liveness_check():
    return "OK"


@app.get("/health/ready", response_model = str)
async def readiness_check():
    return "OK"  # TODO: čekiranje baze or sth?

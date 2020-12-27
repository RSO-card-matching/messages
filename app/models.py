# pylint: disable=no-name-in-module

from typing import Optional
from datetime import datetime

from pydantic import BaseModel
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Boolean, Column, Integer, String, DateTime


Base = declarative_base()


class Message(BaseModel):
    id: int
    sender_id: int
    receiver_id: int
    time: datetime
    content: str
    read_status: bool


class MessageNew(BaseModel):
    receiver_id: int
    content: str

class NewMessageID(BaseModel):
    id: int


class MessageModel(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key = True, index = True)
    sender_id = Column(Integer, index = True)
    receiver_id = Column(Integer, index = True)
    time = Column(DateTime, index = True)
    content = Column(String)
    read_status = Column(Boolean, index = True)

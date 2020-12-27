from typing import Optional, List
from os import getenv

from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker, Session

from . import models


db_ip = getenv("DATABASE_IP")
if db_ip:
    SQLALCHEMY_DATABASE_URL = db_ip
else:
    SQLALCHEMY_DATABASE_URL = "sqlite:///./sql_app.db"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def initBase(db: Session):
    engine = db.get_bind()
    try:
        models.MessageModel.__table__.drop(engine)
    except:
        pass
    models.MessageModel.__table__.create(engine)
    db.commit()
    db.close()



class DBException(Exception):
    pass



def get_message_by_id(db: Session, sid: int) -> Optional[models.Message]:
    msg = db.query(models.MessageModel).filter(models.MessageModel.id == sid).first()
    return models.Message(**msg.__dict__) if msg else None


def get_all_messages(db: Session, sid: Optional[int], rid: Optional[int],
        read: Optional[bool]) -> List[models.Message]:
    q = db.query(models.MessageModel)
    if sid != None:
        q = q.filter(models.MessageModel.sender_id == sid)
    if rid != None:
        q = q.filter(models.MessageModel.receiver_id == rid)
    if read != None:
        q = q.filter(models.MessageModel.read_status == read)
    return [models.Message(**message.__dict__) for message in q.all()]


def insert_new_message(db: Session, uid: int, new_message: models.MessageNew) -> int:
    new_id = db.query(func.max(models.MessageModel.id)).first()[0] + 1
    message_model = models.MessageModel(
        id = new_id,
        sender_id = uid,
        receiver_id = new_message.receiver_id,
        time = func.now(),
        content = new_message.content,
        read_status = False
    )
    db.add(message_model)
    db.commit()
    return new_id


def mark_message_as_read(db: Session, sid: int) -> None:
    message = db.query(models.MessageModel)
    message = message.filter(models.MessageModel.id == sid)
    message = message.first()
    if message == None:
        raise DBException
    message.read_status = True
    db.commit()


def mark_message_as_unread(db: Session, mid: int) -> None:
    message = db.query(models.MessageModel).filter(models.MessageModel.id == mid).first()
    if message == None:
        raise DBException
    message.read_status = False
    db.commit()


def delete_message(db: Session, mid: int) -> None:
    sample_model = db.query(models.MessageModel).filter(models.MessageModel.id == mid)
    if sample_model.first() == None:
        raise DBException
    sample_model.delete()
    db.commit()

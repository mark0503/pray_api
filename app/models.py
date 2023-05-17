from datetime import datetime
import enum

from sqlalchemy.orm import Session
from sqlalchemy import create_engine, Enum, Column, Integer, String, ForeignKey, ARRAY
from sqlalchemy.ext.declarative import declarative_base

from app.config import DATABASE_URL

Base = declarative_base()


def connect_db():
    engine = create_engine(DATABASE_URL, connect_args=[])
    session = Session(bind=engine.connect())
    return session


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String)
    email = Column(String)
    password = Column(String)
    first_name = Column(String)
    last_name = Column(String)
    created_at = Column(String, default=datetime.utcnow())


class PrayEnum(enum.Enum):
    SIMPLE = 1,
    SPECIAL = 2,
    FORTY = 3,
    YEARLY = 4,


class Pray(Base):
    __tablename__ = 'pray'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    live_names = Column(ARRAY(String))
    rip_names = Column(ARRAY(String))
    type_pray = Column(Enum(PrayEnum))
    created_at = Column(String, default=datetime.utcnow())
    status_payment = Column(String, default='Не оплачено')


class AuthToken(Base):
    __tablename__ = 'auth_token'

    id = Column(Integer, primary_key=True)
    token = Column(String)
    user_id = Column(Integer, ForeignKey('users.id'))
    created_at = Column(String, default=datetime.utcnow())


class Payments(Base):
    __tablename__ = 'payments'

    id = Column(Integer, primary_key=True)
    ex_id = Column(String)
    url_pay = Column(String)
    user_id = Column(Integer, ForeignKey('users.id'))
    pray = Column(Integer, ForeignKey('pray.id'))
    status_payment = Column(String, default='Не оплачено')

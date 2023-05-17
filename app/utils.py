import hashlib
from app.config import SECRET_KEY
import uuid
from datetime import datetime, timedelta
from typing import Optional

import requests
from fastapi import APIRouter, Body, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
import databases
from sqlalchemy.orm import Session
from starlette import status
from typing import Any
from jose import JWTError, jwt

from qiwi.qiwi import QiwiApi
from .forms import UserLoginForm, PrayCreateForm
from .models import connect_db, User, AuthToken, Pray, Payments
import os
from dotenv import load_dotenv, find_dotenv


def get_password_hash(password: str) -> str:
    return hashlib.sha256(f"{SECRET_KEY}{password}".encode('utf-8')).hexdigest()


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm="HS256")
    return encoded_jwt


async def get_current_user(
        token_str: str = Depends(OAuth2PasswordBearer(tokenUrl="token")), database=Depends(connect_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token_str, SECRET_KEY, algorithms=["HS256"])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = database.query(AuthToken).filter(AuthToken.token == token_str).one_or_none()
    except JWTError:
        raise credentials_exception
    user = database.query(User).filter(User.id == token_data.user_id).one_or_none()
    if user is None:
        raise credentials_exception
    return user

import uuid
from datetime import datetime, timedelta
from typing import Optional

import requests
from fastapi import APIRouter, Body, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import databases
from sqlalchemy.orm import Session
from starlette import status
from typing import Any, List
from jose import JWTError, jwt
from starlette.responses import RedirectResponse

from .forms import UserLoginForm, UserCreateForm, PrayCreateForm
from .models import connect_db, User, AuthToken, Pray, Payments
from .utils import get_password_hash
import os
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())


router = APIRouter()
ACCESS_TOKEN_EXPIRE_MINUTES = 30
ALGORITHM = "HS256"
SECRET_KEY = os.environ.get("SECRET_KEY")
public_key = os.environ.get('public_key')
api_access_token = os.environ.get('api_access_token')
header = {
    'Accept': 'application/json',
    'authorization': 'Bearer ' + api_access_token,
    'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.82 Safari/537.36'
}
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


@router.post("/signup")
def login_for_access_token(form_data: UserLoginForm = Depends(), database=Depends(connect_db)):
    user = database.query(User).filter(User.username == form_data.username).one_or_none()
    if user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username",
            headers={"WWW-Authenticate": "Bearer"},
        )
    else:
        new_user = User(
            username=form_data.username
        )
        database.add(new_user)
        database.commit()
    user = database.query(User).filter(User.username == form_data.username).one_or_none()
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": form_data.username}, expires_delta=access_token_expires
    )
    token = AuthToken(
     token=access_token,
     user_id=user.id
    )
    database.add(token)
    database.commit()

    return {"access_token": access_token, "token_type": "bearer"}


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token_str: str = Depends(oauth2_scheme), database=Depends(connect_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token_str, SECRET_KEY, algorithms=[ALGORITHM])
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


@router.get('/user', name='user:get')
def get_user(user: AuthToken = Depends(get_current_user), database=Depends(connect_db)):
    return {'id': user.id, 'email': user.email}


@router.post('/pray', name='pray:post')
def post_pray(pray: PrayCreateForm = Body(..., embed=True), user: AuthToken = Depends(get_current_user),
              database=Depends(connect_db)):
    new_pray = Pray(
        user_id=user.id,
        live_names=pray.live_names,
        rip_names=pray.rip_names,
        type_pray=pray.typing
    )
    count_names = len(pray.live_names) + len(pray.rip_names)
    if pray.typing == "SIMPLE":
        amount = count_names * 2
    elif pray.typing == "SPECIAL":
        amount = count_names * 20
    elif pray.typing == "FORTY":
        amount = count_names * 800
    elif pray.typing == "YEARLY":
        amount = count_names * 2000
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Typing not found"
        )
    data = {
        "amount": {
            "currency": "RUB",
            "value": f"{amount}.00"
        },
        "expirationDateTime": "2023-12-10T09:02:00+03:00"
    }
    ex_id = uuid.uuid4()
    response = requests.put(f'https://api.qiwi.com/partner/bill/v1/bills/{ex_id}', json=data,
                            headers=header).json()
    url = response['payUrl']

    database.add(new_pray)
    database.commit()
    new_payments = Payments(
        ex_id=ex_id,
        url_pay=url,
        user_id=user.id,
        pray=new_pray.id
    )
    database.add(new_payments)
    database.commit()
    return {'id': new_pray.id, 'pray': new_pray.type_pray, 'url': url}


@router.get('/user/pray/pay/{id}')
def get_pray(user: AuthToken = Depends(get_current_user),
             id: int = Any,  database=Depends(connect_db)):
    payment = database.query(Payments).filter(id == Payments.pray).one_or_none()
    if not payment or payment.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Pray not found"
        )
    return {'pray': payment.url_pay}


@router.get('/user/pray/{id}')
def get_pray(user: AuthToken = Depends(get_current_user),
             id: int = Any,  database=Depends(connect_db)):
    pray = database.query(Pray).filter(id == Pray.id).one_or_none()
    if not pray or pray.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Pray not found"
        )
    return {'pray_id': pray.id, 'pray_type': pray.type_pray, 'names': pray.names}


@router.delete('/user/pray/{id}')
def delete_pray(user: AuthToken = Depends(get_current_user),
                id: int = Any,  database=Depends(connect_db)):
    pray = database.query(Pray).filter(id == Pray.id).one_or_none()
    if not pray or pray.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Pray not found"
        )
    database.delete(pray)
    database.commit()
    return {'pray_id': pray.id, 'status': 'delete'}


@router.get('/get_full_prays_paid/{type_pray}')
def get_full_prays_paid(user: AuthToken = Depends(get_current_user),
                          type_pray: str = Any, database=Depends(connect_db)):

    if type_pray.upper() not in ['SIMPLE', 'SPECIAL', 'FORTY', 'YEARLY']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Type_pray not found"
        )
    pray = database.query(Pray).filter(Pray.type_pray == type_pray, Pray.status_payment == 'Оплачено').all()

    if not pray:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="names not found"
        )
    ful_life = []
    for name in pray:
        for i in name.live_names:
            ful_life.append(i)
    ful_rip = []
    for name in pray:
        for y in name.rip_names:
            ful_rip.append(y)
    return {'pray_type': type_pray, 'live_names': ful_life, 'rip_names': ful_rip}


@router.get('/get_full_prays_paid/')
def get_full_prays_health(user: AuthToken = Depends(get_current_user),
                          database=Depends(connect_db)):
    pray_simple = database.query(Pray).filter(Pray.type_pray == "SIMPLE" and Pray.status_payment == 'Оплачено')
    pray_special = database.query(Pray).filter(Pray.type_pray == "SPECIAL" and Pray.status_payment == 'Оплачено')
    pray_forty = database.query(Pray).filter(Pray.type_pray == "FORTY" and Pray.status_payment == 'Оплачено')
    pray_yearly = database.query(Pray).filter(Pray.type_pray == "YEARLY" and Pray.status_payment == 'Оплачено')

    ful_life_simple = []
    ful_rip_simple = []
    for name in pray_simple:
        for i in name.live_names:
            ful_life_simple.append(i)
        for y in name.rip_names:
            ful_rip_simple.append(y)

    ful_life_special = []
    ful_rip_special = []
    for name in pray_special:
        for i in name.live_names:
            ful_life_special.append(i)
        for y in name.rip_names:
            ful_rip_special.append(y)

    ful_life_forty = []
    ful_rip_forty = []
    for name in pray_forty:
        for i in name.live_names:
            ful_life_forty.append(i)
        for y in name.rip_names:
            ful_rip_forty.append(y)

    ful_life_yearly = []
    ful_rip_yearly = []
    for name in pray_yearly:
        for i in name.live_names:
            ful_life_yearly.append(i)
        for y in name.rip_names:
            ful_rip_yearly.append(y)

    return {'pray_type': [
        {'pray_type': 'Простая', 'data': [{'names_life': ful_life_simple}, {'names_rip': ful_rip_simple}]},
        {'pray_type': 'Заказная', 'data': [{'names_life': ful_life_special}, {'names_rip': ful_rip_special}]},
        {'pray_type': 'Сорокоуст', 'data': [{'names_life': ful_life_forty}, {'names_rip': ful_rip_forty}]},
        {'pray_type': 'Годовое', 'data': [{'names_life': ful_life_yearly}, {'names_rip': ful_rip_yearly}]}]}


@router.get('/check/status/{id}')
def check_status_for_one_pray(user: AuthToken = Depends(get_current_user),
                              id: int = Any,  database=Depends(connect_db)):
    pray = database.query(Pray).filter(id == Pray.id).one_or_none()
    payment = database.query(Payments).filter(pray.id == Payments.pray).one_or_none()
    if not payment or pray.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Pray not found"
        )
    response = requests.get(f'https://api.qiwi.com/partner/bill/v1/bills/{payment.ex_id}', headers=header).json()
    if response['status']['value'] == 'PAID':
        payment = database.query(Payments).filter(Payments.ex_id == payment.ex_id).one_or_none()
        if payment:
            pray = database.query(Pray).filter(Pray.id == payment.pray).one_or_none()
            if pray:
                payment.status_payment = 'Оплачено'
                pray.status_payment = 'Оплачено'
                database.commit()

    return {'pray_id': pray, 'types': pray.status_payment}


def check_status_pray():
    db: Session = connect_db()
    pray_dead = db.query(Payments).filter(Payments.status_payment == 'Не оплачено').all()
    for pau in pray_dead:
        response = requests.get(f'https://api.qiwi.com/partner/bill/v1/bills/{pau.ex_id}', headers=header).json()

        if not response.get('status'):
            continue
        if response['status']['value'] == 'PAID':
            payment = db.query(Payments).filter(Payments.ex_id == pau.ex_id).one_or_none()
            if payment:
                pray = db.query(Pray).filter(Pray.id == payment.pray).one_or_none()
                if pray:
                    payment.status_payment = 'Оплачено'
                    pray.status_payment = 'Оплачено'
                    db.commit()
            else:
                continue

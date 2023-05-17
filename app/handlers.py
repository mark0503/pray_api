import uuid
from datetime import timedelta

from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy.orm import Session
from starlette import status
from typing import Any

from qiwi.qiwi import QiwiApi
from forms import UserLoginForm, PrayCreateForm
from models import connect_db, User, AuthToken, Pray, Payments
from utils import create_access_token, get_current_user


router = APIRouter()


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
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": form_data.username}, expires_delta=access_token_expires
    )
    token = AuthToken(
        token=access_token,
        user_id=user.id
    )
    database.add(token)
    database.commit()

    return {"access_token": access_token, "token_type": "bearer", "success": True}


@router.get('/user', name='user:get')
def get_user(user: AuthToken = Depends(get_current_user)):
    return {'id': user.id, 'email': user.email, "success": True}


@router.post('/pray', name='pray:post')
def post_pray(pray: PrayCreateForm = Body(..., embed=True), user: AuthToken = Depends(get_current_user),
              database=Depends(connect_db)):
    new_pray = Pray(
        user_id=user.id,
        live_names=pray.live_names,
        rip_names=pray.rip_names,
        type_pray=pray.typing
    )
    pray_rate = {
            "SIMPLE": 2,
            "SPECIAL": 20,
            "FORTY": 800,
            "YEARLY": 2000
        }
    count_names = len(pray.live_names) + len(pray.rip_names)
    if pray_rate.get(pray.typing):
        amount = count_names * pray_rate[pray.typing]
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Typing not found"
        )
    ex_id = uuid.uuid4().__str__()
    create_payment = QiwiApi().create_payment(pay_id=ex_id, amount=amount)
    if not create_payment:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Payment do ney create"
        )
    pay_url = create_payment['payUrl']

    database.add(new_pray)
    database.commit()
    new_payments = Payments(
        ex_id=ex_id,
        url_pay=pay_url,
        user_id=user.id,
        pray=new_pray.id
    )
    database.add(new_payments)
    database.commit()
    return {'id': new_pray.id, 'pray': new_pray.type_pray, 'url': pay_url, "success": True}


@router.get('/user/pray/pay/{id}')
def get_pray(user: AuthToken = Depends(get_current_user),
             id: int = Any, database=Depends(connect_db)):
    payment = database.query(Payments).filter(id == Payments.pray).one_or_none()
    if not payment or payment.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Pray not found"
        )
    return {'pray_url': payment.url_pay, "success": True}


@router.get('/user/pray/{id}')
def get_pray(user: AuthToken = Depends(get_current_user),
             id: int = Any, database=Depends(connect_db)):
    pray = database.query(Pray).filter(id == Pray.id).one_or_none()
    if not pray or pray.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Pray not found"
        )
    return {'pray_id': pray.id, 'pray_type': pray.type_pray, 'names': pray.names, "success": True}


@router.delete('/user/pray/{id}')
def delete_pray(user: AuthToken = Depends(get_current_user),
                id: int = Any, database=Depends(connect_db)):
    pray = database.query(Pray).filter(id == Pray.id).one_or_none()
    if not pray or pray.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Pray not found"
        )
    database.delete(pray)
    database.commit()
    return {'pray_id': pray.id, 'status': True}


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
    return {'pray_type': type_pray, 'live_names': pray.live_names, 'rip_names': pray.rip_names}


@router.get('/get_full_prays_paid/')
def get_full_prays_health(user: AuthToken = Depends(get_current_user),
                          database=Depends(connect_db)):
    res = {'pray_types': []}
    pray_simple = database.query(Pray).filter(Pray.type_pray == "SIMPLE" and Pray.status_payment == 'Оплачено')
    pray_special = database.query(Pray).filter(Pray.type_pray == "SPECIAL" and Pray.status_payment == 'Оплачено')
    pray_forty = database.query(Pray).filter(Pray.type_pray == "FORTY" and Pray.status_payment == 'Оплачено')
    pray_yearly = database.query(Pray).filter(Pray.type_pray == "YEARLY" and Pray.status_payment == 'Оплачено')

    pray_types = [
        {
            'name': 'Простая',
            'names_life': pray_simple.live_names,
            'names_rip': pray_simple.live_names,
        },
        {
            'name': 'Заказная',
            'names_life': pray_special.live_names,
            'names_rip': pray_special.live_names,
        },
        {
            'name': 'Сорокоуст',
            'names_life': pray_forty.live_names,
            'names_rip': pray_forty.live_names,
        },
        {
            'name': 'Годовое',
            'names_life': pray_yearly.live_names,
            'names_rip': pray_yearly.live_names,
        }
    ]

    for pray_type in pray_types:
        res['pray_types'].append(
            {
                'pray_type': pray_type['name'],
                'data': [
                    {
                        'names_life': pray_type['names_life']
                    },
                    {
                        'names_rip': pray_type['names_rip']
                    }
                ]
            }
        )

    return res


@router.get('/check/status/{id}')
def check_status_for_one_pray(user: AuthToken = Depends(get_current_user),
                              id: int = Any, database=Depends(connect_db)):
    pray = database.query(Pray).filter(id == Pray.id).one_or_none()
    payment = database.query(Payments).filter(pray.id == Payments.pray).one_or_none()
    if not payment or pray.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Pray not found"
        )
    pay_status = QiwiApi().pay_status(payment.ex_id)
    if not pay_status:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Pray not found in qiwi system"
        )
    if pay_status == 'PAID':
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

        pay_status = QiwiApi().pay_status(pau.ex_id)
        if not pay_status:
            continue
        if pay_status == 'PAID':
            payment = db.query(Payments).filter(Payments.ex_id == pau.ex_id).one_or_none()
            if payment:
                pray = db.query(Pray).filter(Pray.id == payment.pray).one_or_none()
                if pray:
                    payment.status_payment = 'Оплачено'
                    pray.status_payment = 'Оплачено'
                    db.commit()
            else:
                continue

from pydantic import BaseModel
from typing import Optional


class UserLoginForm(BaseModel):
    username: str


class UserCreateForm(BaseModel):
    username: str
    email: str
    password: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class PrayCreateForm(BaseModel):
    live_names: list
    rip_names: list
    typing: str

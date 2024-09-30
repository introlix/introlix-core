from pydantic import BaseModel
from typing import List
from datetime import date

# signup model
class UserSignup(BaseModel):
    name: str
    email: str
    password: str
    dob: date
    interestList: List[str]

# login model
class UserLogin(BaseModel):
    email: str
    password: str

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date
from datetime import datetime

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

# feed model
class FeedModel(BaseModel):
    id: str = Field(..., alias="_id")
    title: str
    desc: str
    url: str
    image_url: str
    tags: list
    vote: int
    created_at: Optional[datetime]

class DiscussionModel(BaseModel):
    id: str = Field(..., alias="_id")
    title: str
    url: str
    tags: list
    vote: int
    created_at: Optional[datetime]
    answer_count: int
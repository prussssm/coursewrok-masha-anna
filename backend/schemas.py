from pydantic import BaseModel

class UserCreate(BaseModel):
    first_name: str
    last_name: str
    email: str
    phone: str
    password: str

class UserLogin(BaseModel):
    first_name: str
    last_name: str
    password: str

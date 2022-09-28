from pydantic import BaseModel

class EdupageCredentials(BaseModel):
    username: str
    password: str
    subdomain: str

class UsernameAndPassword(BaseModel):
    username: str
    password: str

class Message(BaseModel):
    recipients: list[int]
    body: str
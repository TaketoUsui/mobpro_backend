from fastapi import FastAPI

from pydantic import BaseModel

class Message(BaseModel):
    user: str
    message: str
class RoomInfo(BaseModel):
    youtube: str
    title: str
    user: str

app = FastAPI()

@app.get("/")
async def read_root():
    return {"Hello": "World"}

@app.post("/make-room")
async def make_room(info: RoomInfo):
    return {
        "room": "qWjlNO"
    }

@app.post("/messages/{room}")
async def message(room: str, content: Message):
    return {
        "room": room,
        "user": content.user,
        "message": content.message
    }

@app.get("/messages/{room}")
async def get_messages(room: str):
    return {
        "room": room,
        "messages": [
            {"user": "pigeon", "message": "hello"},
            {"user": "giraffe", "message": "nice code"},
            {"user": "penguin", "message": "hi"},
            {"user": "shark", "message": "日本人いませんかー？"},
        ]
    }
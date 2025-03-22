from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from fastapi import Depends, FastAPI, HTTPException, Query

import my_db as db

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Message(BaseModel):
    user: str
    message: str
class RoomInfo(BaseModel):
    youtubeId: str
    title: str
    user: str
    atcoderContest: str

# @app.on_event("startup")
# def on_startup():
#     db.create_db_and_tables()

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
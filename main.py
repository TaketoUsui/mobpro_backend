from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from fastapi import Depends, HTTPException, Query

import my_db as db

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class MakeMessage(BaseModel):
    user: str
    message: str
class MakeRoom(BaseModel):
    title: str
    user: int
    atcoderContest: str
    youtubeId: str
class MakeUser(BaseModel):
    name: str
    password: str

@app.on_event("startup")
def on_startup():
    db.create_db_and_tables()

@app.post("/users/make")
async def make_user(data: MakeUser, session: db.SessionDep):
    new_user = db.User(name=data.name, password=data.password)
    session.add(new_user)
    session.commit()
    session.refresh(new_user)
    return {
        "id": new_user.id,
        "name": new_user.name
    }

@app.get("/users/{user_id}")
async def get_user(user_id: int, session: db.SessionDep):
    user = session.get(db.User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {
        "id": user.id,
        "name": user.name
    }

@app.get("/users")
async def get_users(session: db.SessionDep):
    users = session.exec(db.select(db.User)).all()
    return [
        {
            "id": user.id,
            "name": user.name
        }
        for user in users
    ]

@app.post("/rooms/make")
async def make_room(data: MakeRoom, session: db.SessionDep):
    if not session.get(db.User, data.user):
        raise HTTPException(status_code=404, detail="User not found")
    new_room = db.Room(
        title=data.title,
        user=data.user,
        atcoder_contest=data.atcoderContest,
        youtube_id=data.youtubeId
    )
    session.add(new_room)
    session.commit()
    session.refresh(new_room)
    return {
        "id": new_room.id,
        "title": new_room.title
    }

@app.get("/rooms/{room_id}")
async def get_room(room_id: int, session: db.SessionDep):
    room = session.get(db.Room, room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    return {
        "id": room.id,
        "title": room.title,
        "user": session.get(db.User, room.user).name,
        "atcoderContest": room.atcoder_contest,
        "youtubeId": room.youtube_id
    }

@app.get("/rooms")
async def get_rooms(session: db.SessionDep):
    rooms = session.exec(db.select(db.Room)).all()
    return [
        {
            "id": room.id,
            "title": room.title,
            "user": session.get(db.User, room.user).name
        }
        for room in rooms
    ]

@app.post("/messages/{room}")
async def message(room: str, data: MakeMessage):
    return {
        "room": room,
        "user": data.user.name,
        "message": data.message
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
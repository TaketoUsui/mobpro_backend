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
    youtubeId: str
    title: str
    user: str
    atcoderContest: str
class MakeUser(BaseModel):
    name: str
    password: str

@app.on_event("startup")
def on_startup():
    db.create_db_and_tables()

@app.get("/")
async def read_root():
    return {"Hello": "World"}

@app.post("/make-room")
async def make_room(data: MakeRoom):
    return {
        "room": "qWjlNO"
    }

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
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from fastapi import Depends, FastAPI, HTTPException, Query

from . import my_db as db

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# @app.on_event("startup")
# def on_startup():
#     db.create_db_and_tables()

# @app.post("/heroes/")
# def create_hero(hero: db.Hero, session: db.SessionDep) -> db.Hero:
#     session.add(hero)
#     session.commit()
#     session.refresh(hero)
#     return hero

# @app.get("/heroes/")
# def read_heroes(
#     session: db.SessionDep,
#     offset: int = 0,
#     limit: db.Annotated[int, Query(le=100)] = 100,
# ) -> list[db.Hero]:
#     heroes = session.exec(db.select(db.Hero).offset(offset).limit(limit)).all()
#     return heroes

# @app.get("/heroes/{hero_id}")
# def read_hero(hero_id: int, session: db.SessionDep) -> db.Hero:
#     hero = session.get(db.Hero, hero_id)
#     if not hero:
#         raise HTTPException(status_code=404, detail="Hero not found")
#     return hero

# @app.delete("/heroes/{hero_id}")
# def delete_hero(hero_id: int, session: db.SessionDep):
#     hero = session.get(db.Hero, hero_id)
#     if not hero:
#         raise HTTPException(status_code=404, detail="Hero not found")
#     session.delete(hero)
#     session.commit()
#     return {"ok": True}

class Message(BaseModel):
    user: str
    message: str
class RoomInfo(BaseModel):
    youtubeId: str
    title: str
    user: str
    atcoderContest: str

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
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from fastapi import Depends, FastAPI, HTTPException, Query

from typing import Annotated

from fastapi import Depends
from sqlmodel import Field, Session, SQLModel, create_engine, select


class Hero(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    age: int | None = Field(default=None, index=True)
    secret_name: str

sqlite_file_name = "database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, connect_args=connect_args)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]

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

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

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
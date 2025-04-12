from typing import Annotated

from fastapi import Depends
from sqlmodel import Field, Session, SQLModel, create_engine, select

class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    password: str

class Room(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    title: str | None = None
    user: int | None = Field(default=None, foreign_key="user.id")
    atcoder_contest: str | None = None
    youtube_id: str | None = None

class Message(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user: str
    message: str
    room: int | None = Field(default=None, foreign_key="room.id")
    liked: int = Field(default=0)
    
class Like(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: int | None = Field(default=None, foreign_key="user.id")
    message_id: int | None = Field(default=None, foreign_key="message.id")
    
class Achievement(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: int | None = Field(default=None, foreign_key="user.id")
    login_days: int = 1 #登録した時点でログイン1日目になるため
    likes_given: int = 0
    likes_received: int = 0
    comments_made: int = 0
    rooms_created: int = 0
    streams_viewed: int = 0

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
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
class LoginUser(BaseModel):
    name: str
    password: str

@app.on_event("startup")
def on_startup():
    db.create_db_and_tables()

@app.get("/init-database")
def init_database():
    try:
        db.engine.connect()
        db.engine.execute("SELECT 1")
    except:
        db.create_db_and_tables()
    return {"ok": True}

@app.post("/users/make")
async def make_user(data: MakeUser, session: db.SessionDep):
    user = session.exec(db.select(db.User).filter(db.User.name == data.name)).first()
    if user:
        raise HTTPException(status_code=400, detail="User already exists")
    new_user = db.User(name=data.name, password=data.password)
    session.add(new_user)
    session.commit()
    session.refresh(new_user)
    
    #　実績テーブルの初期化
    new_achievement = db.Achievement(user_id=new_user.id)
    session.add(new_achievement)
    session.commit()
    
    return {
        "id": new_user.id,
        "name": new_user.name
    }

@app.get("/users/{user_id}")
async def get_user(user_id: int, session: db.SessionDep):
    user = session.get(db.User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    archievement = session.exec(db.select(db.Achievement).filter(db.Achievement.user_id == user_id)).first()
    output = {
        "id": user.id,
        "name": user.name,
    }
    if archievement:
        output["archievements"] = {
            # "login_days": archievement.login_days,
            "likes_given": archievement.likes_given,
            "likes_received": archievement.likes_received,
            "messages_made": archievement.messages_made,
            # "rooms_created": archievement.rooms_created,
            # "streams_viewed": archievement.streams_viewed,
        }
    else:
        output["archievements"] = {}
    return output

@app.post("/users/login")
async def login_user(data: LoginUser, session: db.SessionDep):
    user = session.exec(db.select(db.User).filter(db.User.name == data.name)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.password != data.password:
        raise HTTPException(status_code=401, detail="Invalid password")
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

@app.post("/messages/make/{room_id}")
async def make_message(room_id: int, data: MakeMessage, session: db.SessionDep):
    if not session.get(db.Room, room_id):
        raise HTTPException(status_code=404, detail="Room not found")
    new_message = db.Message(user=data.user, message=data.message, room=room_id)
    session.add(new_message)
    
    # メッセージ投稿者の実績（messages_made）を更新
    make_message_user = session.exec(db.select(db.User).where(db.User.name == data.user)).first()
    make_message_achievement = None
    if make_message_user:
        make_message_achievement = session.exec(
            db.select(db.Achievement).where(db.Achievement.user_id == make_message_user.id)
        ).first()
    if make_message_achievement:
        make_message_achievement.messages_made += 1

    session.commit()
    session.refresh(new_message)
    return {
        "id": new_message.id,
        "user": new_message.user,
        "message": new_message.message
    }

@app.get("/messages/{room_id}")
async def get_messages(room_id: int, user_id: int, session: db.SessionDep):
    messages = session.exec(db.select(db.Message).filter(db.Message.room == room_id)).all()
    return [
        {
            "user": message.user,
            "message": message.message,
            "message_id": message.id,
            "liked_cnt": message.liked,
            "liked_by_me": session.exec(db.select(db.Like).filter(db.Like.message_id == message.id, db.Like.user_id == user_id)).first() is not None
        }
        for message in messages
    ]

@app.post("/messages/like/{message_id}")
async def like_message(message_id: int, user_id: int, session: db.SessionDep):
    message = session.get(db.Message, message_id)
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    
    liker = session.get(db.User, user_id)
    if not liker:
        raise HTTPException(status_code=404, detail="User not found")
    
    # すでにいいねしているか確認
    existing_like = session.exec(db.select(db.Like).filter(db.Like.message_id == message_id, db.Like.user_id == user_id)).first()
    if existing_like:
        raise HTTPException(status_code=400, detail="Already liked")
    
    # いいね作成
    new_like = db.Like(user_id=user_id, message_id=message_id)
    message.liked += 1
    session.add(new_like)
    
    # いいねしたユーザーの実績（likes_given）を更新
    liker_achievement = session.exec(
        db.select(db.Achievement).where(db.Achievement.user_id == user_id)
    ).first()
    if liker_achievement:
        liker_achievement.likes_given += 1
        
    # メッセージの投稿者の実績（likes_received）を更新
    # ユーザー名から User を検索
    receiver_user = session.exec(db.select(db.User).where(db.User.name == message.user)).first()
    # ユーザーが存在する場合のみ Achievement を取得しいいね数を増やす
    receiver_achievement = None
    if receiver_user:
        receiver_achievement = session.exec(
            db.select(db.Achievement).where(db.Achievement.user_id == receiver_user.id)
        ).first()
    if receiver_achievement:
        receiver_achievement.likes_received += 1
    
    # DBの更新
    session.commit()
    session.refresh(message)
    session.refresh(new_like)
    return {
        "user_id": new_like.user_id,
        "message_id": new_like.message_id
    }

@app.post("/messages/unlike/{message_id}")
async def unlike_message(message_id: int, user_id: int, session: db.SessionDep):
    message = session.get(db.Message, message_id)
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    
    like = session.exec(db.select(db.Like).filter(db.Like.message_id == message_id, db.Like.user_id == user_id)).first()
    if not like:
        raise HTTPException(status_code=404, detail="Like not found")
    
    # いいねの削除
    session.delete(like)
    message.liked -= 1
    
    # いいねしたユーザーの実績（likes_given）を更新
    liker_achievement = session.exec(
        db.select(db.Achievement).where(db.Achievement.user_id == user_id)
    ).first()
    if liker_achievement:
        liker_achievement.likes_given -= 1
        
    # メッセージの投稿者の実績（likes_received）を更新
    # ユーザー名から User を検索
    receiver_user = session.exec(db.select(db.User).where(db.User.name == message.user)).first()
    # ユーザーが存在する場合のみ Achievement を取得しいいね数を減らす
    receiver_achievement = None
    if receiver_user:
        receiver_achievement = session.exec(
            db.select(db.Achievement).where(db.Achievement.user_id == receiver_user.id)
        ).first()
    if receiver_achievement:
        receiver_achievement.likes_received -= 1
    
    # DBの更新
    session.commit()
    session.refresh(message)
    return HTTPException(status_code=200, detail="Unliked successfully")
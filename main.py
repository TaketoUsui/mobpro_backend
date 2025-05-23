from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from fastapi import Depends, HTTPException, Query
from datetime import datetime, timezone

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
    session.refresh(new_achievement)
    
    return {
        "id": new_user.id,
        "name": new_user.name
    }

@app.get("/users/{user_id}")
async def get_user(user_id: int, session: db.SessionDep):
    user = session.get(db.User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    achievement = session.exec(db.select(db.Achievement).filter(db.Achievement.user_id == user_id)).first()
    output = {
        "id": user.id,
        "name": user.name,
    }
    if achievement:
        output["achievements"] = {
            "login_days": achievement.login_days,
            "likes_given": achievement.likes_given,
            "likes_received": achievement.likes_received,
            "messages_made": achievement.messages_made,
            "rooms_created": achievement.rooms_created,
            # "streams_viewed": achievement.streams_viewed,
        }
    else:
        output["achievements"] = {}
    return output

@app.post("/users/login")
async def login_user(data: LoginUser, session: db.SessionDep):
    user = session.exec(db.select(db.User).filter(db.User.name == data.name)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.password != data.password:
        raise HTTPException(status_code=401, detail="Invalid password")
    
    # ログインユーザーの実績（login_days）の更新
    login_achievement = None
    login_achievement = session.exec(
        db.select(db.Achievement).where(db.Achievement.user_id == user.id)
    ).first()
    last_login_date = login_achievement.last_login_date if login_achievement and login_achievement.last_login_date else "no data"
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    if login_achievement:
        # その日初めてのログインであればlogin_daysを増やす
        if last_login_date != today:
            login_achievement.login_days += 1
            login_achievement.last_login_date = today
            session.add(login_achievement)
            
    session.commit()
    if login_achievement:
        session.refresh(login_achievement)
    return {
        "id": user.id,
        "name": user.name,
        "last_login_date": last_login_date,
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
    
    # ルーム作成者の実績（rooms_created）を更新
    make_room_achievement = None
    make_room_achievement = session.exec(
        db.select(db.Achievement).where(db.Achievement.user_id == data.user)
    ).first()
    if make_room_achievement:
        make_room_achievement.rooms_created += 1
        session.add(make_room_achievement)
    
    session.commit()
    session.refresh(new_room)
    if make_room_achievement:
        session.refresh(make_room_achievement)
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
        session.add(make_message_achievement)

    session.commit()
    session.refresh(new_message)
    if make_message_achievement:
        session.refresh(make_message_achievement)
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
    session.add(message)
    session.add(new_like)
    
    # いいねしたユーザーの実績（likes_given）を更新
    liker_achievement = session.exec(
        db.select(db.Achievement).where(db.Achievement.user_id == user_id)
    ).first()
    if liker_achievement:
        liker_achievement.likes_given += 1
        session.add(liker_achievement)
        
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
        session.add(receiver_achievement)
    
    # DBの更新
    session.commit()
    session.refresh(message)
    session.refresh(new_like)
    if liker_achievement:
        session.refresh(liker_achievement)
    if receiver_achievement:
        session.refresh(receiver_achievement)
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
    session.add(message)
    
    # いいねしたユーザーの実績（likes_given）を更新
    liker_achievement = session.exec(
        db.select(db.Achievement).where(db.Achievement.user_id == user_id)
    ).first()
    if liker_achievement:
        liker_achievement.likes_given -= 1
        session.add(liker_achievement)
        
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
        session.add(receiver_achievement)
    
    # DBの更新
    session.commit()
    session.refresh(message)
    if liker_achievement:
        session.refresh(liker_achievement)
    if receiver_achievement:
        session.refresh(receiver_achievement)
    return HTTPException(status_code=200, detail="Unliked successfully")

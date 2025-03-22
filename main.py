from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
import uvicorn

import models
import schemas
import crud
from database import engine, get_db

# データベースのテーブルを作成
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="メッセージアプリAPI")

# CORSミドルウェアの設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 本番環境では特定のオリジンに制限すべき
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ユーザー関連のエンドポイント
@app.post("/users/", response_model=schemas.User, status_code=status.HTTP_201_CREATED)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="すでに登録されているメールアドレスです")
    return crud.create_user(db=db, user=user)

@app.get("/users/", response_model=List[schemas.User])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    users = crud.get_users(db, skip=skip, limit=limit)
    return users

@app.get("/users/{user_id}", response_model=schemas.User)
def read_user(user_id: int, db: Session = Depends(get_db)):
    db_user = crud.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="ユーザーが見つかりません")
    return db_user

# メッセージ関連のエンドポイント
@app.post("/users/{user_id}/messages/", response_model=schemas.Message)
def create_message_for_user(
    user_id: int, message: schemas.MessageCreate, db: Session = Depends(get_db)
):
    return crud.create_user_message(db=db, message=message, user_id=user_id)

@app.get("/messages/", response_model=List[schemas.Message])
def read_messages(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    messages = crud.get_messages(db, skip=skip, limit=limit)
    return messages

@app.get("/conversations/{sender_id}/{receiver_id}", response_model=List[schemas.Message])
def get_conversation(sender_id: int, receiver_id: int, db: Session = Depends(get_db)):
    messages = crud.get_conversation(db, sender_id=sender_id, receiver_id=receiver_id)
    return messages

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
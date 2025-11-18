from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
import uvicorn

import models
from models import User
import schemas
from database import *

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Mobil Api", version="0.1.0")


@app.post("/add_user", response_model=schemas.UserResponse)
def create_user(user: schemas.CreateUser, db: Session = Depends(get_db)):
    new_user = User(
        login=user.login,
        password=user.password,
        email=user.email
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@app.post("/come_in", response_model=schemas.UserResponse)
def come_in(user: schemas.UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.login == user.login).first()
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найдет"
        )

    if db_user.password != user.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="неверный пароль"
        )

    return db_user


if __name__ == "__main__":
    uvicorn.run("main:app", host="192.168.0.16", port=8000, reload=True)


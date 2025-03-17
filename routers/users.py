from fastapi import APIRouter, Depends, HTTPException
from schemas import UserCreate
from sqlalchemy.orm import Session
import crud
from utils import get_db

router = APIRouter()

@router.get("/users/", tags=["users"])
def read_users(db: Session = Depends(get_db), skip: int = 0, limit: int = 100):
    users = crud.get_users(db, skip=skip, limit=limit)
    return users

@router.get("/users/{user_name}", tags=["users"])
def read_user_by_name(user_name: str, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_name(db, user_name=user_name)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


@router.post("/users/", tags=["users"]) 
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    return crud.create_user(db=db, user=user)

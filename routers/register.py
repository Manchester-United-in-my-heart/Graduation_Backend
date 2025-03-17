from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import crud
import schemas
import utils

router = APIRouter()

@router.post("/register/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(utils.get_db)):
    db_user = crud.get_user_by_name(db, username=user.username)
    if db_user: 
        raise HTTPException(status_code=400, detail="User already registered")
    hashed_password = utils.get_password_hash(user.password)
    return crud.create_user(db=db, user=schemas.User(username=user.username, email=user.email, role="user", password=hashed_password))

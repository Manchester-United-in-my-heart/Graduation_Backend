from fastapi import APIRouter, Depends, HTTPException, Header
from fastapi.security import OAuth2PasswordRequestForm
from typing import Annotated
from schemas import UserLogin 
from sqlalchemy.orm import Session
import crud
import models
from utils import verify_password, create_access_token, get_db, verify_token

router = APIRouter()

@router.post("/token", tags=["login"])
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Session = Depends(get_db)
):
    user = UserLogin(username=form_data.username, password=form_data.password)
    db_user = crud.get_user_by_name(db, username=user.username)
    if not db_user:
        raise HTTPException(status_code=400, detail="Incorrect username")
    if not verify_password(user.password, db_user.password):
        raise HTTPException(status_code=400, detail="Incorrect password")
    access_token = create_access_token(data={"sub": db_user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/users/me", tags=["login"])
async def get_current_user_by_token(
    authorization: Annotated [str|None, Header()] = None,
    db: Session = Depends(get_db)
):
    try: 
        token_removed_bearer = authorization.split(" ")[1]
        payload = verify_token(token_removed_bearer)
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=400, detail="Invalid token")
        user = crud.get_user_by_name(db, username)
        if user is None:
            raise HTTPException(status_code=400, detail="User not found")
        return user
    except Exception as e:
        raise HTTPException(status_code=400, detail=e)
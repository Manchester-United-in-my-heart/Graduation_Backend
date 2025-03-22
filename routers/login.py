from fastapi import APIRouter, Depends, HTTPException, Header, Body
from fastapi.security import OAuth2PasswordRequestForm
from typing import Annotated
from schemas import UserLogin 
from sqlalchemy.orm import Session
import crud
import models
from utils import verify_password, create_access_token, get_db, verify_token
from otp_utils import verify_otp
import json

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
    
    if db_user.role.value == "admin":
        temp_access_token = create_access_token(
            data={"sub": db_user.username, "temp": True},
            time_in_min=5
        )
        return {
            "redirect": '/admin/otp',
            "access_token": temp_access_token,
            "token_type": "bearer"
        }
    access_token = create_access_token(data={"sub": db_user.username, "temp": False})
    return { "redirect": "/" ,"access_token": access_token, "token_type": "bearer"}

@router.get("/users/me", tags=["login"])
async def get_current_user_by_token(
    authorization: Annotated [str|None, Header()] = None,
    db: Session = Depends(get_db)
):
    try: 
        token_removed_bearer = authorization.split(" ")[1]
        payload = verify_token(token_removed_bearer)
        username: str = payload.get("sub")
        temp = payload.get("temp")
        if temp:
            raise HTTPException(status_code=400, detail="Invalid token")
        if username is None:
            raise HTTPException(status_code=400, detail="Invalid token")
        user = crud.get_user_by_name(db, username)
        if user is None:
            raise HTTPException(status_code=400, detail="User not found")
        return user
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid token")

async def get_current_user_by_token_pass_temp(
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
        raise HTTPException(status_code=400, detail="Invalid token")

@router.get("/get_admin", tags=["login"])
async def get_admin(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user_by_token)
):
    if current_user.role != "admin":
        return {
            'is_admin': False
        }
    return {
        'is_admin': True
    }
    
@router.post("/admin_login", tags=["login"])
async def admin_login(
    otp: str = Body(...),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user_by_token_pass_temp)
):

    if current_user.role.value != "admin":
        raise HTTPException(status_code=400, detail="You are not authorized to access this page")
    
    otp_number = json.loads(otp).get("otp")
    
    if not verify_otp(otp_number):
        raise HTTPException(status_code=400, detail="Invalid OTP")
    
    access_token = create_access_token(data={"sub": current_user.username, "temp": False})
    return { "status_code": 200 ,"redirect": "/admin" ,"access_token": access_token, "token_type": "bearer"}

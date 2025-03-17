from pydantic import BaseModel
from typing import List, Union


class Token(BaseModel):
    access_token: str
    token_type: str
    
class TokenData(BaseModel):
    username: Union[str, None] = None

class UserBase(BaseModel):
    username: str
    email: Union[str, None]
    
class UserCreate(BaseModel):
    username: str
    password: str
    email: Union[str, None]

class UserLogin(BaseModel):
    username: str
    password: str

class User(UserBase):
    username: str
    email: Union[str, None]
    password: str
    role: str
    class Config:
        orm_mode = True

class ProjectBase(BaseModel):
    name: str
    description: str
    is_public: bool
    pdf_download_link: str
    epub_download_link: str
    is_allow_to_train: bool

class ProjectCreate(ProjectBase):
    pass
    
class Project(ProjectBase):
    username: str
    id: int
    date_created: str
    
    class Config:
        orm_mode = True

class PageBase(BaseModel):
    project_id: int
    page_number: int
    image_link: str

class PageCreate(PageBase):
    pass
    
class Page(PageBase):
    id: int
    
    class Config:
        orm_mode = True
        
class ElementBase(BaseModel):
    page_id: int
    element_type: str
    x: float
    y: float
    width: float
    height: float
    prediction: str

class ElementCreate(ElementBase):
    pass
    
class Element(ElementBase):
    id: int
    
    class Config:
        orm_mode = True
        
    

from sqlalchemy import Column, Integer, String, Float, Enum, ForeignKey, Boolean, DateTime, Text
# from database import Base
from sqlalchemy.ext.declarative import declarative_base
import datetime
import enum

Base = declarative_base()

class RoleEnum(enum.Enum):
    admin = "admin"
    user = "user"

class ElementTypeEnum(enum.Enum):
    caption = 0
    footnote = 1
    formula = 2
    listitem = 3
    pagefooter = 4
    pageheader = 5
    picture = 6
    sectionheader = 7
    table = 8
    text = 9
    title = 10

class User(Base):
    __tablename__ = "users"
    
    username = Column(String(12), primary_key=True, index=True)
    password = Column(String(200), nullable=False)
    email = Column(String(50), nullable=True)
    role = Column(Enum(RoleEnum), nullable=False)
    
class Project(Base):
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False)
    description = Column(String(200), nullable=True)
    username = Column(String(12), ForeignKey("users.username"), nullable=False, index=True)
    is_public = Column(Boolean, default=False, nullable=False)
    date_created = Column(DateTime, default=datetime.datetime.utcnow)
    pdf_download_link = Column(String(500), nullable=True)
    epub_download_link = Column(String(500), nullable=True)
    cover_image = Column(Text, nullable=True)
    is_allow_to_train = Column(Boolean, default=False, nullable=False)
    
    
class Page(Base):
    __tablename__ = "pages"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    page_number = Column(Integer, nullable=False)
    image_link = Column(String(500), nullable=False)
    is_used_to_train = Column(Boolean, default=False, nullable=False)

class Element(Base):
    __tablename__ = "elements"
    
    id = Column(Integer, primary_key=True, index=True)
    page_id = Column(Integer, ForeignKey("pages.id"), index=True)
    element_type = Column(Enum(ElementTypeEnum), nullable=False)
    x = Column(Float, nullable=False)
    y = Column(Float, nullable=False)
    width = Column(Float, nullable=False)
    height = Column(Float, nullable=False)
    prediction = Column(String(500), nullable=True)
    actual = Column(String(500), nullable=True)
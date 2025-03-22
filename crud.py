from sqlalchemy.orm import Session
import models, schemas
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import datetime

def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).offset(skip).limit(limit).all()

def get_user_by_name(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()

def create_user(db: Session, user: schemas.User):
    db_user = models.User(username=user.username, email=user.email, role=user.role, password=user.password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_projects(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Project).offset(skip).limit(limit).all()

def get_projects_by_username(db: Session, username: str):
    return db.query(models.Project).filter(models.Project.username == username).all()

def get_project_by_id(db: Session, project_id: int):
    return db.query(models.Project).filter(models.Project.id == project_id).first()

def create_project(db: Session, username: str, project: schemas.ProjectCreate, cover_image: str):
    db_project = models.Project(name=project.name, description=project.description, username=username, is_public=project.is_public, pdf_download_link=project.pdf_download_link, epub_download_link=project.epub_download_link, cover_image=cover_image, is_allow_to_train=project.is_allow_to_train)
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project
    
def get_pages(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Page).offset(skip).limit(limit).all()

def get_pages_by_project_id(db: Session, project_id: int):
    return db.query(models.Page).filter(models.Page.project_id == project_id).all()

def get_all_pages_in_the_same_project(db: Session, project_id: int, page_id: int):
    return db.query(models.Page).filter(models.Page.project_id == project_id, models.Page.id != page_id).all()

def get_page_by_id(db: Session, project_id: int, page_id: int):
    return db.query(models.Page).filter(models.Page.project_id == project_id, models.Page.id == page_id).first()

def create_page(db: Session, page: schemas.PageCreate):
    db_page = models.Page(project_id=page.project_id, page_number=page.page_number, image_link=page.image_link)
    db.add(db_page)
    db.commit()
    db.refresh(db_page)
    return db_page

def get_elements(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Element).offset(skip).limit(limit).all()

def get_element_by_id(db: Session, element_id: int):
    return db.query(models.Element).filter(models.Element.id == element_id).first()

def create_element(db: Session, element: schemas.ElementCreate):
    db_element = models.Element(page_id=element.page_id, element_type=element.element_type, x=element.x, y=element.y, width=element.width, height=element.height, prediction=element.prediction)
    db.add(db_element)
    db.commit()
    db.refresh(db_element)
    return db_element

def get_elements_by_page_id(db: Session, page_id: int):
    return db.query(models.Element).filter(models.Element.page_id == page_id).all()

def get_elements_by_page_id_and_element_type(db: Session, page_id: int, element_type: str):
    return db.query(models.Element).filter(models.Element.page_id == page_id, models.Element.element_type == element_type).all()

def get_all_pages_in_project_allow_to_train(db: Session):
    projects_allow_to_train = db.query(models.Project).filter(models.Project.is_allow_to_train == True).all()
    return_data = []
    for project in projects_allow_to_train:
        pages_is_not_trained_yet = db.query(models.Page).filter(models.Page.project_id == project.id, models.Page.is_used_to_train == False).all()
        for page in pages_is_not_trained_yet:
            page_data = {}
            page_data["image_file"] = page.image_link
            page_data["page_id"] = page.id
            file_name_without_extension = page.image_link.split(".")[0]
            page_data["label_file"] = f"{file_name_without_extension}.txt"
            return_data.append(page_data)
            page.is_used_to_train = True
            db.commit()
    return return_data

def count_number_of_newly_created_users(db: Session):
    # last 24 hours
    last_24_hours = db.query(models.User).filter(models.User.date_created >= datetime.datetime.now() - datetime.timedelta(days=1)).count()
    last_48_hours = db.query(models.User).filter(models.User.date_created >= datetime.datetime.now() - datetime.timedelta(days=2)).count()
    last_72_hours = db.query(models.User).filter(models.User.date_created >= datetime.datetime.now() - datetime.timedelta(days=3)).count()
    last_96_hours = db.query(models.User).filter(models.User.date_created >= datetime.datetime.now() - datetime.timedelta(days=4)).count()
    last_120_hours = db.query(models.User).filter(models.User.date_created >= datetime.datetime.now() - datetime.timedelta(days=5)).count()
    data_by_days = [
        last_24_hours,
        last_48_hours - last_24_hours,
        last_72_hours - last_48_hours,
        last_96_hours - last_72_hours,
        last_120_hours - last_96_hours
    ]
    
    # last 7 days
    last_7_days = db.query(models.User).filter(models.User.date_created >= datetime.datetime.now() - datetime.timedelta(days=7)).count()
    last_14_days = db.query(models.User).filter(models.User.date_created >= datetime.datetime.now() - datetime.timedelta(days=14)).count()
    last_21_days = db.query(models.User).filter(models.User.date_created >= datetime.datetime.now() - datetime.timedelta(days=21)).count()
    last_28_days = db.query(models.User).filter(models.User.date_created >= datetime.datetime.now() - datetime.timedelta(days=28)).count()
    last_35_days = db.query(models.User).filter(models.User.date_created >= datetime.datetime.now() - datetime.timedelta(days=35)).count()
    data_by_weeks = [
        last_7_days,
        last_14_days - last_7_days,
        last_21_days - last_14_days,
        last_28_days - last_21_days,
        last_35_days - last_28_days
    ]
    # last 30 days
    last_30_days = db.query(models.User).filter(models.User.date_created >= datetime.datetime.now() - datetime.timedelta(days=30)).count()
    last_60_days = db.query(models.User).filter(models.User.date_created >= datetime.datetime.now() - datetime.timedelta(days=60)).count()
    last_90_days = db.query(models.User).filter(models.User.date_created >= datetime.datetime.now() - datetime.timedelta(days=90)).count()
    last_120_days = db.query(models.User).filter(models.User.date_created >= datetime.datetime.now() - datetime.timedelta(days=120)).count()
    last_150_days = db.query(models.User).filter(models.User.date_created >= datetime.datetime.now() - datetime.timedelta(days=150)).count()
    data_by_months = [
        last_30_days,
        last_60_days - last_30_days,
        last_90_days - last_60_days,
        last_120_days - last_90_days,
        last_150_days - last_120_days
    ]
    return {
        "data_by_days": data_by_days,
        "data_by_weeks": data_by_weeks,
        "data_by_months": data_by_months
    }

def count_number_of_newly_created_projects(db: Session):
    # last 24 hours
    last_24_hours = db.query(models.Project).filter(models.Project.date_created >= datetime.datetime.now() - datetime.timedelta(days=1)).count()
    last_48_hours = db.query(models.Project).filter(models.Project.date_created >= datetime.datetime.now() - datetime.timedelta(days=2)).count()
    last_72_hours = db.query(models.Project).filter(models.Project.date_created >= datetime.datetime.now() - datetime.timedelta(days=3)).count()
    last_96_hours = db.query(models.Project).filter(models.Project.date_created >= datetime.datetime.now() - datetime.timedelta(days=4)).count()
    last_120_hours = db.query(models.Project).filter(models.Project.date_created >= datetime.datetime.now() - datetime.timedelta(days=5)).count()
    data_by_days = [
        last_24_hours,
        last_48_hours - last_24_hours,
        last_72_hours - last_48_hours,
        last_96_hours - last_72_hours,
        last_120_hours - last_96_hours
    ]
    
    # last 7 days
    last_7_days = db.query(models.Project).filter(models.Project.date_created >= datetime.datetime.now() - datetime.timedelta(days=7)).count()
    last_14_days = db.query(models.Project).filter(models.Project.date_created >= datetime.datetime.now() - datetime.timedelta(days=14)).count()
    last_21_days = db.query(models.Project).filter(models.Project.date_created >= datetime.datetime.now() - datetime.timedelta(days=21)).count()
    last_28_days = db.query(models.Project).filter(models.Project.date_created >= datetime.datetime.now() - datetime.timedelta(days=28)).count()
    last_35_days = db.query(models.Project).filter(models.Project.date_created >= datetime.datetime.now() - datetime.timedelta(days=35)).count()
    data_by_weeks = [
        last_7_days,
        last_14_days - last_7_days,
        last_21_days - last_14_days,
        last_28_days - last_21_days,
        last_35_days - last_28_days
    ]
    # last 30 days
    last_30_days = db.query(models.Project).filter(models.Project.date_created >= datetime.datetime.now() - datetime.timedelta(days=30)).count()
    last_60_days = db.query(models.Project).filter(models.Project.date_created >= datetime.datetime.now() - datetime.timedelta(days=60)).count()
    last_90_days = db.query(models.Project).filter(models.Project.date_created >= datetime.datetime.now() - datetime.timedelta(days=90)).count()
    last_120_days = db.query(models.Project).filter(models.Project.date_created >= datetime.datetime.now() - datetime.timedelta(days=120)).count()
    last_150_days = db.query(models.Project).filter(models.Project.date_created >= datetime.datetime.now() - datetime.timedelta(days=150)).count()
    data_by_months = [
        last_30_days,
        last_60_days - last_30_days,
        last_90_days - last_60_days,
        last_120_days - last_90_days,
        last_150_days - last_120_days
    ]
    return {
        "data_by_days": data_by_days,
        "data_by_weeks": data_by_weeks,
        "data_by_months": data_by_months
    }
    
def count_number_of_newly_created_pages(db: Session):
    # last 24 hours
    last_24_hours = db.query(models.Page).filter(models.Page.date_created >= datetime.datetime.now() - datetime.timedelta(days=1)).count()
    last_48_hours = db.query(models.Page).filter(models.Page.date_created >= datetime.datetime.now() - datetime.timedelta(days=2)).count()
    last_72_hours = db.query(models.Page).filter(models.Page.date_created >= datetime.datetime.now() - datetime.timedelta(days=3)).count()
    last_96_hours = db.query(models.Page).filter(models.Page.date_created >= datetime.datetime.now() - datetime.timedelta(days=4)).count()
    last_120_hours = db.query(models.Page).filter(models.Page.date_created >= datetime.datetime.now() - datetime.timedelta(days=5)).count()
    data_by_days = [
        last_24_hours,
        last_48_hours - last_24_hours,
        last_72_hours - last_48_hours,
        last_96_hours - last_72_hours,
        last_120_hours - last_96_hours
    ]
    
    # last 7 days
    last_7_days = db.query(models.Page).filter(models.Page.date_created >= datetime.datetime.now() - datetime.timedelta(days=7)).count()
    last_14_days = db.query(models.Page).filter(models.Page.date_created >= datetime.datetime.now() - datetime.timedelta(days=14)).count()
    last_21_days = db.query(models.Page).filter(models.Page.date_created >= datetime.datetime.now() - datetime.timedelta(days=21)).count()
    last_28_days = db.query(models.Page).filter(models.Page.date_created >= datetime.datetime.now() - datetime.timedelta(days=28)).count()
    last_35_days = db.query(models.Page).filter(models.Page.date_created >= datetime.datetime.now() - datetime.timedelta(days=35)).count()
    data_by_weeks = [
        last_7_days,
        last_14_days - last_7_days,
        last_21_days - last_14_days,
        last_28_days - last_21_days,
        last_35_days - last_28_days
    ]
    # last 30 days
    last_30_days = db.query(models.Page).filter(models.Page.date_created >= datetime.datetime.now() - datetime.timedelta(days=30)).count()
    last_60_days = db.query(models.Page).filter(models.Page.date_created >= datetime.datetime.now() - datetime.timedelta(days=60)).count()
    last_90_days = db.query(models.Page).filter(models.Page.date_created >= datetime.datetime.now() - datetime.timedelta(days=90)).count()
    last_120_days = db.query(models.Page).filter(models.Page.date_created >= datetime.datetime.now() - datetime.timedelta(days=120)).count()
    last_150_days = db.query(models.Page).filter(models.Page.date_created >= datetime.datetime.now() - datetime.timedelta(days=150)).count()
    data_by_months = [
        last_30_days,
        last_60_days - last_30_days,
        last_90_days - last_60_days,
        last_120_days - last_90_days,
        last_150_days - last_120_days
    ]
    return {
        "data_by_days": data_by_days,
        "data_by_weeks": data_by_weeks,
        "data_by_months": data_by_months
    }
        
async def get_all_pages_in_project_allow_to_train_async(db: AsyncSession):
    projects_allow_to_train = await db.execute(select(models.Project).filter(models.Project.is_allow_to_train == True))
    return_data = []
    for project in projects_allow_to_train.scalars():
        pages_is_not_trained_yet = await db.execute(select(models.Page).filter(models.Page.project_id == project.id, models.Page.is_used_to_train == False))
        for page in pages_is_not_trained_yet.scalars():
            page_data = {}
            page_data["image_file"] = page.image_link
            page_data["page_id"] = page.id
            file_name_without_extension = page.image_link.split(".")[0]
            page_data["label_file"] = f"{file_name_without_extension}.txt"
            return_data.append(page_data)
    return return_data
            
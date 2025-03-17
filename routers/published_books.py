from fastapi import APIRouter, Depends
import s3_utils
from utils import get_db
import os
from dotenv import load_dotenv, dotenv_values 
from sqlalchemy.orm import Session
import crud

load_dotenv()

router = APIRouter()

@router.get("/", tags=["published_books"])
async def get_published_books(db: Session = Depends(get_db)):
    projects = crud.get_projects(db)
    published_books_bucket_name = os.getenv("PUBLISHED_BUCKET_NAME")
    return_data = []
    for project in projects:
        is_public = project.is_public
        if is_public:
            epub_file_name = project.name + ".epub"
            is_published_yet = s3_utils.check_if_file_exists(published_books_bucket_name, epub_file_name)
            if is_published_yet:
                return_data.append({
                    "project_id": project.id,
                    "project_name": project.name,
                })
    return {
        "published_books": return_data
    }
    
@router.get("/{project_id}", tags=["published_books"])
async def get_published_book(project_id: int, db: Session = Depends(get_db)):
    project = crud.get_project_by_id(db, project_id)
    if project is None:
        return {
            "detail": "Project not found"
        }
    published_books_bucket_name = os.getenv("PUBLISHED_BUCKET_NAME")
    epub_file_name = project.name + ".epub"
    is_published_yet = s3_utils.check_if_file_exists(published_books_bucket_name, epub_file_name)
    if is_published_yet:
        return {
            "project_id": project.id,
            "project_name": project.name,
            "epub_download_link": s3_utils.get_s3_url(published_books_bucket_name, epub_file_name),
            "project_description": project.description,
            "project_belongs_to": project.username
        }
    return {
        "detail": "Project is not published yet"
    }
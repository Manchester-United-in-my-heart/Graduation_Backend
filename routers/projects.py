from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from typing import Annotated
from pydantic import BaseModel
from schemas import ProjectBase, User, PageCreate
from sqlalchemy.orm import Session
import crud
from utils import get_db, get_current_user, cut_image_and_return_image_and_label_file_name
from .pages import router as pages_router
import os
import shutil
import s3_utils
from dotenv import load_dotenv, dotenv_values 
from paddle_utils import get_prediction_from_image
import cv2
import numpy as np
import json
import math
import base64
import subprocess

load_dotenv() 

class ProjectCreateSchema(BaseModel):
    name: str
    description: str
    is_public: bool
    is_allow_to_train: bool


router = APIRouter()

@router.get("/", tags=["projects"])
# a function that returns all projects belonging to the user coming with the session
async def get_current_user_project(
    db: Session = Depends(get_db), 
    current_user = Depends(get_current_user)
):
    return crud.get_projects_by_username(db, username=current_user.username)

@router.get("/{project_id}", tags=["projects"])
# a function that returns a specific project belonging to the user coming with the session
def get_current_user_project_by_id(project_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    db_project = crud.get_project_by_id(db, project_id=project_id)
    db_pages = crud.get_pages_by_project_id(db, project_id=project_id)
    if db_project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return {
        "project": db_project,
        "pages": db_pages
    }

@router.post("/", tags=["projects"])
# a function that creates a project for the user coming with the session
async def create_project(name : str = Form(...), description : str = Form(...), is_public : bool = Form(...), is_allow_to_train : bool = Form(...),
                         cover_image: UploadFile = File(...),
                         db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    image_content = await cover_image.read()
    image_in_base64 = base64.b64encode(image_content).decode('utf-8')
    
    project = ProjectBase(name=name, description=description, is_public=is_public, is_allow_to_train=is_allow_to_train, pdf_download_link="", epub_download_link="")

    return crud.create_project(db=db, username=current_user.username, project=project, cover_image=image_in_base64)

@router.post("/{project_id}/upload_images", tags=["projects"])
async def upload_images(project_id: int, allow_to_train: bool = False, db: Session = Depends(get_db) , files: list[UploadFile] = File(...)):
    number_of_project_images = len(crud.get_pages_by_project_id(db, project_id))
    project_name = crud.get_project_by_id(db, project_id).name
    
    file_names = []
    file_contents = []
    
    image_bucket_name = os.getenv("IMAGES_BUCKET_NAME")
    element_bucket_name = os.getenv("ELEMENTS_BUCKET_NAME")
    for file in files:
        contents = file.file.read()
        np_array = np.frombuffer(contents, np.uint8)
        image_in_bgr = cv2.imdecode(np_array, cv2.IMREAD_COLOR)
        image_in_rgb = cv2.cvtColor(image_in_bgr, cv2.COLOR_BGR2RGB)
        text_in_image = await get_prediction_from_image(image_in_rgb)
        file_contents.append(text_in_image)
        file_name = f"{project_name}_{number_of_project_images}.png"
        file_name_without_extension = file_name.split(".")[0]
        with open(f"{file_name_without_extension}.txt", "w") as f:
            f.write(json.dumps(text_in_image))
        with open(f"{file_name_without_extension}_shortened.txt", "w") as f:
                for section in text_in_image:
                    for line in section['lines']:
                        for word in line['words']:
                            f.write(f"0 {word['position']['x']} {word['position']['y']} {word['position']['x'] + word['position']['w']} {word['position']['y'] + word['position']['h']} {word['texts']}\n")
        cv2.imwrite(file_name, image_in_bgr)
        if allow_to_train:
            s3_utils.upload_file(open(file_name, "rb"), element_bucket_name, file_name)
            s3_utils.upload_file(open(f"{file_name_without_extension}.txt", "rb"), element_bucket_name, f"{file_name_without_extension}.txt")
            s3_utils.upload_file(open(f"{file_name_without_extension}_shortened.txt", "rb"), element_bucket_name, f"{file_name_without_extension}_shortened.txt")
            print("Uploaded image and label to train bucket")
        s3_utils.upload_file(open(file_name, "rb"), image_bucket_name, file_name)
        s3_utils.upload_file(open(f"{file_name_without_extension}.txt", "rb"), image_bucket_name, f"{file_name_without_extension}.txt")
        s3_utils.upload_file(open(f"{file_name_without_extension}_shortened.txt", "rb"), image_bucket_name, f"{file_name_without_extension}_shortened.txt")
        os.remove(f"{file_name_without_extension}.txt")
        os.remove(f"{file_name_without_extension}_shortened.txt")
        os.remove(file_name)
        file_names.append(file_name)
        print("Uploaded image and label to image bucket")
        page = PageCreate(project_id=project_id, page_number=number_of_project_images, image_link=file_name)
        crud.create_page(db=db, page=page)
        number_of_project_images += 1

    return {"filenames": file_names, "filecontents": file_contents}

@router.get("/{project_id}/request_epub_file", tags=["projects"])
async def request_epub_file(project_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    project = crud.get_project_by_id(db, project_id)
    image_links = crud.get_pages_by_project_id(db, project_id)
    image_bucket_name = os.getenv("IMAGES_BUCKET_NAME")
    images_and_raw_contents = []
    for element in image_links:
        image_link = element.image_link
        file_name_without_extension = image_link.split(".")[0]
        image_file_name = image_link
        raw_content_file_name = f"{file_name_without_extension}.txt"
        
        image = s3_utils.download_file(image_bucket_name, image_file_name)
        raw_content = s3_utils.download_file(image_bucket_name, raw_content_file_name)
        
        cv2_image = cv2.imread(image_file_name)
        data_in_raw_content_file = ""
        with open(raw_content_file_name, "r") as file:
            data_in_raw_content_file = file.read()
        raw_content = json.loads(data_in_raw_content_file)
        images_and_raw_contents.append({
            # "image": cv2.cvtColor(cv2_image, cv2.COLOR_BGR2RGB),
            "image": cv2_image,
            "raw_content": raw_content
        })

        os.remove(image_file_name)
        os.remove(raw_content_file_name)
    
    html_content = ""
    
    html_content_in_array = []
    
    current_section_content = {}
    
    for i in range(len(images_and_raw_contents)):
        do_have_next_page = True if i != len(images_and_raw_contents) - 1 else False
        do_have_previous_page = True if i != 0 else False
        
        for element in images_and_raw_contents[i]['raw_content']:
            if element['label'] == "SectionHeader":
                if current_section_content:
                    html_content_in_array.append(current_section_content.copy())
                current_section_content.clear()
                element_text = ""
                for line in element['lines']:
                    for word in line['words']:
                        element_text += f"{word['texts']} "
                html_content += f"<h1>{element_text}</h1>"
                current_section_content['title'] = element_text
                current_section_content['data'] = ""
            elif element['label'] == "Picture":
                x = math.floor(element['bbox'][0])
                y = math.floor(element['bbox'][1])
                w = math.ceil(element['bbox'][2] - x)
                h = math.ceil(element['bbox'][3] - y)

                cropped_image = images_and_raw_contents[i]['image'][y:y+h, x:x+w]
                _, buffer = cv2.imencode(".png", cropped_image)
                image_array = np.array(buffer)
                base64_image = base64.b64encode(image_array).decode('utf-8')
                html_content += f"<img src='data:image/png;base64,{base64_image}' alt='image'/>"
                if 'data' not in current_section_content:
                    current_section_content['data'] = ""
                current_section_content['data'] += f"<img src='data:image/png;base64,{base64_image}' alt='image'/>"
                
            else:
                element_text = ""
                for line in element['lines']:
                    for word in line['words']:
                        element_text += f"{word['texts']} "
                html_content += f"<p>{element_text}</p>"
                if 'data' not in current_section_content:
                    current_section_content['data'] = ""
                
                # check if the first char in element_text is a captial letter. If it is, then it is a new paragraph, else it is a continuation of the previous paragraph
                if current_section_content['data'] and element_text[0].isupper():
                    current_section_content['data'] += f"<p>{element_text}</p>"
                else:
                    last_closing_p_index = current_section_content['data'].rfind("</p>")
                    if last_closing_p_index != -1:
                        current_section_content["data"] = current_section_content['data'][:last_closing_p_index] + current_section_content['data'][last_closing_p_index+4:]
                    current_section_content['data'] += f" {element_text}</p>"
                    
    html_content_in_array.append(current_section_content)
    
    # write the html content array to a file using json.dumps
    with open("html_content.json", "w") as file:
        file.write(json.dumps(html_content_in_array))
    
    # Path to your JavaScript file
    js_file_path = 'test.mjs'

    # Command to run the JavaScript file using Node.js
    command = f'node {js_file_path}'

    # Execute the command and wait for it to complete
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # Get the output and error (if any)
    stdout, stderr = process.communicate()

    # Decode the output and error from bytes to string
    stdout = stdout.decode('utf-8')
    stderr = stderr.decode('utf-8')

    # Print the output and error
    print("Output:\n", stdout)
    print("Error:\n", stderr)

    os.remove("html_content.json")
    
    published_bucket_name = os.getenv("PUBLISHED_BUCKET_NAME")

    s3_utils.upload_file(open("my-first-ebook.epub", "rb"), published_bucket_name, object_name=project.name + ".epub")
    
    download_link = s3_utils.get_s3_url(published_bucket_name, project.name + ".epub")
    
    return {
        "download_link": download_link
    }


router.include_router(pages_router, prefix="/{project_id}/pages", tags=["pages"])

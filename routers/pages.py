from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Body
from schemas import PageBase
from sqlalchemy.orm import Session
import crud
from utils import get_db, get_current_user
import s3_utils
import os
import json
import ast

router = APIRouter()

@router.get("/", tags=["pages"])
def get_pages(project_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    return crud.get_pages(db, project_id=project_id, user_name=current_user.user_name)

@router.get("/{page_id}", tags=["pages"])
def get_page_by_id(project_id: int, page_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    db_page = crud.get_page_by_id(db, project_id=project_id, page_id=page_id)
    pages_in_the_same_project = crud.get_all_pages_in_the_same_project(db, project_id, page_id)
    pages_in_the_same_project.append({
        "id": db_page.id,
        "page_number": db_page.page_number,
        "image_link": db_page.image_link
    })
    db_page.other_pages = pages_in_the_same_project
    images_bucket_name = os.getenv("IMAGES_BUCKET_NAME")
    # get the download link of the page from s3
    download_link = s3_utils.get_s3_url(images_bucket_name, db_page.image_link)

    # download the raw result file (not shortened) from s3
    file_name_without_extension = db_page.image_link.split(".")[0]
    raw_result_file_name = file_name_without_extension + ".txt"
    s3_utils.download_file(images_bucket_name, raw_result_file_name)
    string_result = ""
    with open(raw_result_file_name, "r") as file:
        string_result = file.read()
    db_page.raw_result = json.loads(string_result)
    os.remove(raw_result_file_name)
    db_page.image_link = download_link

    if db_page is None:
        raise HTTPException(status_code=404, detail="Page not found")
    return db_page
    
@router.post("/{page_id}/update", tags=["pages"])
async def update_page_content(project_id: int, page_id: int, body = Body(...) , db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    images_bucket_name = os.getenv("IMAGES_BUCKET_NAME")
    raw_body = body
    decoded_body = body.decode("UTF-8")
    data = ast.literal_eval(decoded_body)
    updated_text = data.get("updatedText")
    db_page = crud.get_page_by_id(db, project_id=project_id, page_id=page_id)
    image_file_name = db_page.image_link
    file_name_without_extension = image_file_name.split(".")[0]
    raw_result_file_name = file_name_without_extension + ".txt"
    
    # download the raw result file and shortened result file from s3
    s3_utils.download_file(images_bucket_name, raw_result_file_name)
    string_raw_result = ""
    with open(raw_result_file_name, "r") as file:
        string_raw_result = file.read()
    raw_result = json.loads(string_raw_result)

    line_iterator = 0
    
    for line in updated_text['lines']:
        line_iterator += 1
        if len(line['boxes']) == 0:
            lines_in_raw_result = []
            for paragraph in raw_result:
                for line in paragraph['lines']:
                    lines_in_raw_result.append(line)
            lines_in_raw_result[line_iterator -1 ]['words'] = []
            continue
        paragraph_index = line['boxes'][0]['inParagraph']
        line_index = line['boxes'][0]['inLine']
        
        # find the most-top-left and the most-bottom-right point of the line among boxes
        min_x = 10000
        min_y = 10000
        max_x = 0
        max_y = 0
        
        for box in line['boxes']:
            if box['x'] < min_x:
                min_x = box['x']
            if box['y'] < min_y:
                min_y = box['y']
            if box['x'] + box['width'] > max_x:
                max_x = box['x'] + box['width']
            if box['y'] + box['height'] > max_y:
                max_y = box['y'] + box['height']
        
        # compare them with the position of current line and update if neccessary
        current_min_x = line['position']['x']
        current_min_y = line['position']['y'] 
        current_max_x = line['position']['x'] + line['position']['w'] 
        current_max_y = line['position']['y'] + line['position']['h']

        if min_x < current_min_x:
            current_min_x = min_x
        if min_y < current_min_y:
            current_min_y = min_y
        if max_x > current_max_x:
            current_max_x = max_x
        if max_y > current_max_y:
            current_max_y = max_y
        
        line['position']['x'] = current_min_x
        line['position']['y'] = current_min_y
        line['position']['w'] = current_max_x - current_min_x
        line['position']['h'] = current_max_y - current_min_y

        words = []
        
        for box in line['boxes']:
            texts = {}
            texts['texts'] = box['word']
            position = {}
            position['x'] = box['x']
            position['y'] = box['y']
            position['w'] = box['width']
            position['h'] = box['height']
            texts['position'] = position
            words.append(texts)
        
        words.sort(key=lambda x: x['position']['x'])
        
        raw_result[paragraph_index]['lines'][line_index]['words'] = words
        raw_result[paragraph_index]['lines'][line_index]['position'] = line['position']
    
    print("just a text")
    
    # write the updated raw result to the file
    with open(raw_result_file_name, "w") as file:
        file.write(json.dumps(raw_result))
    
    # upload the updated raw result to s3
    s3_utils.upload_file(open(raw_result_file_name, "rb"), images_bucket_name, raw_result_file_name)
    
    os.remove(raw_result_file_name)
    return {
        "message": "Updated successfully"
    }
    
@router.post("/upload", tags=["pages"])
def upload_pages(project_id: int, page: PageBase, db: Session = Depends(get_db), current_user = Depends(get_current_user), files: list[UploadFile] = File(...)):
    return {"filenames": [file.filename for file in files]}
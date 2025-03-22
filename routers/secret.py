from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from utils import get_db, get_current_user
import crud
import s3_utils
import time
import os
from dotenv import load_dotenv
import requests
import json
from otp_utils import get_otp_auth_string, get_qr_code, verify_otp

load_dotenv()
 
router = APIRouter()

@router.get("/secret/")
async def get_secret(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    if current_user.role.value != "admin":
        return {
            "detail": "You are not authorized to see this message"
        }
    END_POINT = "http://localhost:8001/"
    response = requests.get(END_POINT)
    return {
        "message": response.json()
    }

@router.get("/train")
async def start_training(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    if current_user.role.value != "admin":
        return {
            "detail": "You are not authorized to start training"
        }
    
    data_to_train = crud.get_all_pages_in_project_allow_to_train(db)
    instances = s3_utils.get_all_ec2_instances()
    bucket_name = os.getenv("IMAGES_BUCKET_NAME")
    images_and_labels = []
    command_list = [
        'sudo touch /home/ubuntu/data_to_train.txt',
        'sudo chmod 777 /home/ubuntu/data_to_train.txt'
    ]
    for data in data_to_train:
        image_downloadable_url = s3_utils.get_s3_url(
            bucket = bucket_name,
            object_name = data['image_file']
        )
        label = s3_utils.get_s3_url(
            bucket = bucket_name,
            object_name = data['label_file']
        )
        
        command = f"echo \"{image_downloadable_url}\" \"{label}\"  >> /home/ubuntu/data_to_train.txt",
        command_list.append(command[0])
        
        images_and_labels.append({
            "image": image_downloadable_url,
            "label": label
        })
    
    date = time.strftime("%Y-%m-%d-%H-%M-%S")

    command_list.append('sudo docker container start 2d2c')
    command_list.append('sudo docker cp /home/ubuntu/data_to_train.txt 2d2c:/home/data_to_train.txt')
    command_list.append('sudo rm /home/ubuntu/data_to_train.txt')
    command_list.append('sudo docker exec 2d2c /bin/bash -c "python3 prepare_data.py"')
    command_list.append('sudo docker exec 2d2c /bin/bash -c "python3 edit_yml_config.py --epoch_num=5"')
    command_list.append('sudo docker exec 2d2c /bin/bash -c "cd /home/PaddleOCR && python3 tools/train.py -c configs/rec/PP-OCRv3/en_PP-OCRv3_rec.yml"')
    command_list.append('sudo docker exec 2d2c /bin/bash -c "rm -rf /home/PaddleOCR/train_data/train/"')
    command_list.append('sudo docker exec 2d2c /bin/bash -c "rm -rf /home/PaddleOCR/train_data/train_label.txt"')
    command_list.append('sudo docker exec 2d2c /bin/bash -c "export FLAGS_enable_pir_api=0"')
    command_list.append(f'sudo docker exec 2d2c /bin/bash -c "cd /home/PaddleOCR && python3 tools/export_model.py -c configs/rec/PP-OCRv3/en_PP-OCRv3_rec.yml -o Global.pretrained_model=output/v3_en_mobile/latest Global.save_inference_dir=./inference/rec_{date}/"')
    command_list.append(f'sudo docker cp 2d2c:/home/PaddleOCR/inference/rec_{date} ./rec_{date}')
    command_list.append(f'sudo aws s3 cp ./rec_{date} s3://graduation-trained-models/rec_{date} --recursive')
    command_list.append(f'sudo aws s3 cp ./rec_{date} s3://graduation-trained-models/latest --recursive')
    command_list.append(f'sudo rm -rf ./rec_{date}')

    # write the commands to a file named "training_commands.json" as a JSON object
    with open("training_commands.json", "w") as file:
        file.write(
            json.dumps(
                command_list
            )
        )
        
    # upload the file to the S3 bucket
    s3_utils.upload_file(
        bucket=os.getenv("IMAGES_BUCKET_NAME"),
        object_name="training_commands.json",
        data=open("training_commands.json", "rb") 
    )

    # remove the file from the local machine
    os.remove("training_commands.json")
    
    return {
        "data": command_list
    }

@router.get("/secret/replace_model")
async def replace_model(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    if current_user.role.value != "admin":
        return {
            "detail": "You are not authorized to replace the model"
        }
        
    # create a new folder named "recognition_model_latest" in the local machine if not exists
    if not os.path.exists("recognition_model_latest"):
        os.makedirs("recognition_model_latest")
        
    # download the latest model from the S3 bucket
    s3_utils.download_file_from_a_nested_folder(
        bucket=os.getenv("TRAINED_MODELS_BUCKET_NAME"),
        key="latest/inference.pdiparams",
        file_name="inference.pdiparams"
    )
    s3_utils.download_file_from_a_nested_folder(
        bucket=os.getenv("TRAINED_MODELS_BUCKET_NAME"),
        key="latest/inference.pdiparams.info",
        file_name="inference.pdiparams.info"
    )
    s3_utils.download_file_from_a_nested_folder(
        bucket=os.getenv("TRAINED_MODELS_BUCKET_NAME"),
        key="latest/inference.pdmodel",
        file_name="inference.pdmodel"
    )
    s3_utils.download_file_from_a_nested_folder(
        bucket=os.getenv("TRAINED_MODELS_BUCKET_NAME"),
        key="latest/inference.yml",
        file_name="inference.yml"
    )

    # move the downloaded files to the folder "recognition_model_latest"
    os.rename("inference.pdiparams", "recognition_model_latest/inference.pdiparams")
    os.rename("inference.pdiparams.info", "recognition_model_latest/inference.pdiparams.info")
    os.rename("inference.pdmodel", "recognition_model_latest/inference.pdmodel")
    os.rename("inference.yml", "recognition_model_latest/inference.yml")

    # move the folder "recognition_model_latest" to ./../archive
    os.rename("recognition_model_latest", "./../archive/recognition_model_latest")

    return {
        "message": "Model has been replaced"
    }

@router.get("/secret/dashboard_data")
async def get_dashboard_data(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    if current_user.role.value != "admin":
        return {
            "detail": "You are not authorized to see the dashboard data"
        }
    return {
        "message": "Nothing"
    }
    

@router.get("/get_dashboard_data")
async def test(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    if current_user.role.value != "admin":
        return {
            "detail": "You are not authorized to see this message"
        }

    users_data = crud.count_number_of_newly_created_users(db)
    projects_data = crud.count_number_of_newly_created_projects(db)
    pages_data = crud.count_number_of_newly_created_pages(db)
    published_data = s3_utils.count_number_of_updated_published_books(os.getenv("PUBLISHED_BUCKET_NAME"))
    return {
        "users": users_data,
        "projects": projects_data,
        "pages": pages_data,
        "published_books": published_data
    }
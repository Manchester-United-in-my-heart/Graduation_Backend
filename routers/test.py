import boto3
import cv2
import os
import numpy as np

from dotenv import load_dotenv, dotenv_values 
load_dotenv() 
bucket_name = os.getenv("IMAGES_BUCKET_NAME")

def get_image_from_s3(bucket_name: str, file_name: str):
    s3 = boto3.client('s3')
    
    response = s3.get_object(Bucket=bucket_name, Key=file_name)
    image_data = response['Body'].read()
    
    image = np.frombuffer(image_data, np.uint8)
    
    return cv2.imdecode(image, cv2.IMREAD_COLOR)

def show_image(image):
    cv2.imshow('image', image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

image = get_image_from_s3(bucket_name, "Think and Grow Rich_0.png")
show_image(image)
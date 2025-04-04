from PIL import Image
from surya.layout import LayoutPredictor
import cv2
from surya.detection import DetectionPredictor
from ultralytics import YOLO
from paddleocr import PaddleOCR, draw_ocr
import math
import numpy as np
from matplotlib import pyplot as plt
import base64
import asyncio
from threading import Lock
from s3_utils import download_file_from_a_nested_folder
import os
from dotenv import load_dotenv
import shutil

load_dotenv()

layout_predictor = LayoutPredictor()
det_predictor = DetectionPredictor()
model = YOLO('./best (1).pt')

ocr_model = None
model_lock = Lock()
def remove_folder(folder_path):
    """
    Removes a folder and its contents.

    Args:
        folder_path (str): The path to the folder to remove.
    """
    try:
        shutil.rmtree(folder_path)  # Use shutil.rmtree for non-empty folders
        print(f"Folder '{folder_path}' removed successfully.")
    except FileNotFoundError:
        print(f"Folder '{folder_path}' not found.")
    except OSError as e:
        print(f"Error removing folder '{folder_path}': {e}")

async def load_ocr_model(model_path):
    global ocr_model
    try:
      with model_lock:
        if ocr_model is None:
            ocr_model = PaddleOCR(rec_model_dir=model_path, rec_char_dict_path='./archive/vi_dict.txt', use_angle_cls=False, use_gpu=False, ocr_version="PP-OCRv3")
        print("OCR model loaded successfully.")
    except Exception as e:
        print(f"Error loading OCR model: {e}")
  
async def reload_model():
    global ocr_model
    try:
        with model_lock:
          print("Downloading Weights...")
          # Download the weights from S3
           
          print("Reloading OCR model...")
          ocr_model = None
          # remove the old model in ./archive/recognition_model_latest
          remove_folder('./archive/recognition_model_latest')
          os.makedirs('./archive/recognition_model_latest', exist_ok=True)
          # download the new model to ./archive/recognition_model_latest
          download_file_from_a_nested_folder(bucket=os.getenv("TRAINED_MODELS_BUCKET_NAME"),file_name="inference.pdiparams", key="latest/inference.pdiparams")
          download_file_from_a_nested_folder(bucket=os.getenv("TRAINED_MODELS_BUCKET_NAME"),file_name="inference.pdmodel", key="latest/inference.pdmodel")
          download_file_from_a_nested_folder(bucket=os.getenv("TRAINED_MODELS_BUCKET_NAME"),file_name="inference.pdiparams.info", key="latest/inference.pdiparams.info")
          download_file_from_a_nested_folder(bucket=os.getenv("TRAINED_MODELS_BUCKET_NAME"),file_name="inference.yml", key="latest/inference.yml")
          
          # move the new model to ./archive/recognition_model_latest
          os.rename('./inference.pdiparams', './archive/recognition_model_latest/inference.pdiparams')
          os.rename('./inference.pdmodel', './archive/recognition_model_latest/inference.pdmodel')
          os.rename('./inference.pdiparams.info', './archive/recognition_model_latest/inference.pdiparams.info')
          os.rename('./inference.yml', './archive/recognition_model_latest/inference.yml')
          # load the new model
          new_model = PaddleOCR(rec_model_dir='./archive/recognition_model_latest', rec_char_dict_path='./archive/vi_dict.txt', use_angle_cls=False, use_gpu=False, ocr_version="PP-OCRv3")
          ocr_model = new_model
          print("OCR model reloaded successfully.")
    except Exception as e:
        print(f"Error reloading OCR model: {e}")
  
async def get_ocr_model():
  while ocr_model is None:
    await asyncio.sleep(0.1)
  return ocr_model

async def get_prediction_from_image_specified_model(current_model,image_in_rgb):
  image = Image.fromarray(image_in_rgb)
  layout_predictions = layout_predictor([image])
  final = ""
  return_data = []
  img = image_in_rgb
  for ele in layout_predictions[0].bboxes:
    element_infor = {}
    element_infor['label'] = ele.label
    element_infor['position'] = ele.position
    element_infor['bbox'] = ele.bbox
    element_infor['top_k'] = ele.top_k
    element_infor['lines'] = []
    x1, y1, x2, y2 = ele.bbox
    x, y, w, h = math.floor(x1), max(math.floor(y1) - 2, 0), math.ceil(x2 - x1), math.floor(y2 - y1) + 4
    cropped_img = img[y:y+h, x:x+w]
    # print(ele.label, ele.position)
    if (ele.label == "Picture"):
      _, buffer = cv2.imencode('.png', cv2.cvtColor(cropped_img, cv2.COLOR_RGB2BGR)) 
      base64_str = base64.b64encode(buffer).decode('utf-8')
      element_infor['base64'] = base64_str
      return_data.append(element_infor)
    else:
      paragraphs = det_predictor([Image.fromarray(cropped_img)])
      for paragraph in paragraphs:
        for line in paragraph.bboxes:
          line_infor = {}
          line_infor['words'] = []
          x1_line, y1_line, x2_line, y2_line = line.bbox
          x_line, y_line, w_line, h_line = math.floor(x1_line), max(math.floor(y1_line) - 2, 0), math.ceil(x2_line - x1_line), math.ceil(y2_line - y1_line) + 4
          line = cropped_img[y_line:y_line+h_line, x_line:x_line+w_line]
          x_line_absolute = x + x_line
          y_line_absolute = y + y_line
          w_line_absolute = w_line
          h_line_absolute = h_line
          line_infor['position'] = {
            'x': x_line_absolute,
            'y': y_line_absolute,
            'w': w_line_absolute,
            'h': h_line_absolute
          }
          # print(f"Absolute Coordinate of line: x: {x_line_absolute}, y: {y_line_absolute}, w: {w_line_absolute}, h: {h_line_absolute}")
          result = model.predict(source = line, save = False, save_txt = False)
          cors = np.copy(result[0].boxes.xyxy)
          sorted_indices = np.argsort(cors[:, 0])
          sorted_cors = cors[sorted_indices]
          for cor in sorted_cors:
            word_infor = {}
            x1_word, y1_word, x2_word, y2_word = cor
            x_word, y_word, w_word, h_word = max(math.floor(x1_word) -1, 0), math.floor(y1_word), math.floor(x2_word - x1_word) + 2, math.ceil(y2_word - y1_word)
            x_word_absolute = x_line_absolute + x_word
            y_word_absolute = y_line_absolute + y_word
            w_word_absolute = w_word
            h_word_absolute = h_word
            word_infor['position'] = {
              'x': x_word_absolute,
              'y': y_word_absolute,
              'w': w_word_absolute,
              'h': h_word_absolute
            }
            # print(f"Absolute Coordinate of word: x: {x_word_absolute}, y: {y_word_absolute}, w: {w_word_absolute}, h: {h_word_absolute}")
            word = line[y_word:y_word+h_word, x_word:x_word+w_word]
            predicted_word = current_model.ocr(word, det = False)
            print(predicted_word[0][0][0])
            word_infor['texts'] = predicted_word[0][0][0]
            final += predicted_word[0][0][0] + " "
            line_infor['words'].append(word_infor)
          element_infor['lines'].append(line_infor)
          final += "\n"
        final += "\n"
        return_data.append(element_infor)
  print(final)
  return return_data 
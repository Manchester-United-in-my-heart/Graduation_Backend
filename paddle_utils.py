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

layout_predictor = LayoutPredictor()
det_predictor = DetectionPredictor()
model = YOLO('./best (1).pt')
# ocr = PaddleOCR(rec_model_dir='./archive/rec_added_vietnamese_char', rec_char_dict_path='./archive/vi_dict.txt', use_angle_cls=False, use_gpu=False, ocr_version="PP-OCRv3")
# Updated at 2025-03-13 23:02
# ocr = PaddleOCR(rec_model_dir='./archive/rec_2025_03_13_22_52', rec_char_dict_path='./archive/vi_dict.txt', use_angle_cls=False, use_gpu=False, ocr_version="PP-OCRv3")

# Updated at 2025-03-16 21:31
ocr = PaddleOCR(rec_model_dir='./archive/recognition_model_latest', rec_char_dict_path='./archive/vi_dict.txt', use_angle_cls=False, use_gpu=False, ocr_version="PP-OCRv3")

async def get_prediction_from_image(image_in_rgb):
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
            predicted_word = ocr.ocr(word, det = False)
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
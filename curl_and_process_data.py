import os
import json
import cv2
import random

import requests

# Function to download a file from a URL
def download_file(url, save_path):
    try:
        # Send an HTTP GET request to the file URL
        response = requests.get(url, stream=True)
        response.raise_for_status()  # Check if the request was successful

        # Write the content to the file
        with open(save_path, 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
        
        print(f"File downloaded and saved to {save_path}")
    except Exception as e:
        print(f"An error occurred: {e}")

TRAIN_IMAGE_PATH = "./dataset/train/"
TEST_IMAGE_PATH = "./dataset/test/"
TRAIN_LABEL_PATH = "./dataset/train_label.txt"
TEST_LABEL_PATH = "./dataset/test_label.txt"

# Create the directories if they don't exist
os.makedirs(TRAIN_IMAGE_PATH, exist_ok=True)
os.makedirs(TEST_IMAGE_PATH, exist_ok=True)

num_of_test_images = 0
image_iterator = 0
# count how many lines in test_label_path
try:
    with open(TEST_LABEL_PATH, "r") as file:
        test_label_lines = file.readlines()
        num_of_test_images = len(test_label_lines)
except:
    pass

FILE_OF_DOWNLOADABLE_LINKS = './data_to_train.txt'
TRAIN_TEST_RATIO = 0.8

try:
    with open(FILE_OF_DOWNLOADABLE_LINKS, "r") as file:
        for line in file:
            line = line.strip()
            image_url, label_url = line.split()
            download_file(image_url, "image.png")
            download_file(label_url, "raw_label.txt")

            raw_label = ""
            with open("raw_label.txt", "r") as single_label_file:
                raw_label = single_label_file.read()
            
            label = json.loads(raw_label)
            image = cv2.imread("image.png")

            for element in label:
                for line in element['lines']:
                    for word in line['words']:
                        x = word['position']['x']
                        y = word['position']['y']
                        w = word['position']['w']
                        h = word['position']['h']
                        cropped_image = image[y:y+h, x:x+w]
                        # generate a random number between 0 and 1
                        random_number = random.random()
                        if random_number < TRAIN_TEST_RATIO:
                            cropped_image_file_name = f"image_{image_iterator}.png"
                            cv2.imwrite(f'{TRAIN_IMAGE_PATH}{cropped_image_file_name}', cropped_image)
                            with open(TRAIN_LABEL_PATH, "a") as summarized_label_file:
                                summarized_label_file.write(f"./{cropped_image_file_name}\t{word['texts']}\n")
                            image_iterator += 1
                        else:
                            cropped_image_file_name = f"image_{num_of_test_images}.png"
                            cv2.imwrite(f'{TEST_IMAGE_PATH}{cropped_image_file_name}', cropped_image)
                            with open(TEST_LABEL_PATH, "a") as summarized_label_file:
                                summarized_label_file.write(f"./{cropped_image_file_name}\t{word['texts']}\n")
                            num_of_test_images += 1
except Exception as e:
    print(f"An error occurred: {e}")

# try:
#     with open(file_path, "r") as file:
#         for line in file:
#             line = line.strip()
#             image_url, label_url = line.split()
#             download_file(image_url, "image.png")
#             download_file(label_url, "raw_label.txt")
            
#             raw_label = ""
#             with open("raw_label.txt", "r") as single_label_file:
#                 raw_label = single_label_file.read()
            
#             label = json.loads(raw_label)
#             image = cv2.imread("image.png")
        
#             with open("label.txt", "w") as summarized_label_file:
#                 for element in label:
#                     for line in element['lines']:
#                         for word in line['words']:
#                             x = word['position']['x']
#                             y = word['position']['y']
#                             w = word['position']['w']
#                             h = word['position']['h']
#                             cropped_image = image[y:y+h, x:x+w]
#                             cropped_image_file_name = f"image_{image_iterator}.png"
#                             cv2.imwrite(f'./dataset/train/{cropped_image_file_name}', cropped_image)
#                             summarized_label_file.write(f"/home/code/backend/dataset/train/{cropped_image_file_name}\t{word['texts']}\n")
#                             image_iterator += 1
#             os.remove("image.png")
#             os.remove("raw_label.txt")
# except Exception as e:
#     print(f"An error occurred: {e}")
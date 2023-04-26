# Requires Python 3.6 or higher due to f-strings

# Import libraries
import os
import csv
import cv2
import re
import platform
import pytesseract
import itertools
import sys
import imutils
import numpy as np
from tempfile import TemporaryDirectory
from pathlib import Path
from pdf2image import convert_from_path
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

if platform.system() == "Windows":
	# We may need to do some additional downloading and setup...
	# Windows needs a PyTesseract Download
	# https://github.com/UB-Mannheim/tesseract/wiki/Downloading-Tesseract-OCR-Engine

	pytesseract.pytesseract.tesseract_cmd = (
		r"C:\Program Files\Tesseract-OCR\tesseract.exe"
	)

	# Windows also needs poppler_exe
    # Download the file: https://github.com/oschwartz10612/poppler-windows/releases/
	path_to_poppler_exe = Path(r"C:\Program Files (x86)\poppler-23.01.0\Library\bin")
	
	# Put our output files in a sane place...
	out_directory = Path(r"./").expanduser()
else:
	out_directory = Path("./").expanduser()	

# Set the path to the folder containing the PDF files
pdf_folder_path = r"./"

# Set the path to the output CSV file
csv_file_path = r"NamesAndEmails.csv"
# Initialize an empty list to hold the extracted data
data = []

if os.path.isfile(csv_file_path):
    try:
        with open(csv_file_path, "a", newline="") as csv_file:
            # Write data to CSV file
            ...
    except PermissionError as e:
        print(f"Error: {e}. \n\t {csv_file_path} is open in a program. Please Close and run again. ")
        sys.exit()

# Loop through each PDF file in the folder
for filename in os.listdir(pdf_folder_path):
    try:
        if filename.endswith('.pdf'):
            print("Working on ",filename)
            # Store all the pages of the PDF in a variable
            image_file_list = []

            with TemporaryDirectory() as tempdir:
                # Create a temporary directory to hold our temporary images.

                """
                Part #1 : Converting PDF to images
                """

                if platform.system() == "Windows":
                    pdf_pages = convert_from_path(
                        filename, 300,first_page=1,last_page=1, poppler_path=path_to_poppler_exe )
                else:
                    pdf_pages = convert_from_path(filename, 350)

                    # Create a file name to store the image
                filenameImg = f"{tempdir}\page_test"

                # Calculate the dimensions of the upper half
                # width, height = pdf_pages[0].size
                # upper_half_box = (0, 0, width, height // 1)
                # pdf_pages[0] = pdf_pages[0].crop(upper_half_box)
                pdf_pages[0].save(filenameImg, "PNG")
                    # image_file_list.append(filenameImg)

                """
                Part #2 - Recognizing text from the images using OCR
                """
                img = cv2.imread(filenameImg)
                img = cv2.resize(img, None, fx=1.2, fy=1.2, interpolation=cv2.INTER_CUBIC)
                img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                kernel = np.ones((1, 1), np.uint8)
                img = cv2.dilate(img, kernel, iterations=1)
                img = cv2.erode(img, kernel, iterations=1)
                cv2.threshold(cv2.GaussianBlur(img, (5, 5), 0), 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]

                cv2.threshold(cv2.bilateralFilter(img, 5, 75, 75), 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]

                cv2.threshold(cv2.medianBlur(img, 3), 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]

                cv2.adaptiveThreshold(cv2.GaussianBlur(img, (5, 5), 0), 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 2)

                cv2.adaptiveThreshold(cv2.bilateralFilter(img, 9, 75, 75), 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 2)

                cv2.adaptiveThreshold(cv2.medianBlur(img, 3), 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 2)
                # Recognize the text as string in image using pytesserct
                # text = pytesseract.image_to_string(Image.open(filenameImg),config='--psm 6')
                text = pytesseract.image_to_string(img,config='--psm 4')
                text = re.sub(r'[^\w@.\n\s]', '', text)
            lines = text.split('\n') 
            # print(lines)
            found_name = False
            found_secondary_name = False
            found_email = False
            found_secondary_email = False
            email="No Email Found"
            secondary_email="No Email Found"
            secondary_name=""
            for text in lines:
                # print(text)
                # print()
                if found_email is False:
                    email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                    possible_email = text.split(' ')
                    # print(possible_email)
                    for word in possible_email:
                        # print("word::::",word)
                        if re.search(email_regex, word):
                            email = word
                            # print(email)
                            found_email=True
                            break
                    if found_email is True:
                        continue
                if found_email is False and found_secondary_email is False:
                    if re.match(r'email',text.lower()):
                        secondary_email = re.sub(r'email', '', text.lower())
                        # print("email :: ",text)
                        found_secondary_email=True
                text1 =text.lower()
                p1 = r"\b(?:nome)\w*\b"
                p2 = r"\b(?:cognome)\w*\b"
                # Replace all occurrences of the pattern with "nome python"
                text1 = re.sub(p1, "nome", text1)
                text1 = re.sub(p2, "cognome", text1)
                pattern = r"\b(nome|cognome|name)\b"
                text1 = re.sub(r'[^a-zA-Z0-9\s]+', ' ', text1)
                # print(text1)

                # print(text1)
                # Define regular expressions to match name and email
                # if ("nome" in text.lower() or "cognome" in text.lower())and found_name is False:
                if (re.search(pattern, text1))and found_name is False:
                    words = text1.split()
                    if "nome" in words and "cognome" in words:
                        # Find the index of "nome" and "cognome"
                        nome_index = words.index("nome")
                        cognome_index = words.index("cognome")
                        # print(nome_index,"---",cognome_index)
                        if(nome_index>cognome_index):
                            first_index = cognome_index
                            last_index = nome_index
                        else:
                            first_index = nome_index
                            last_index = cognome_index
                        # Remove words between "nome" and "cognome"
                        del words[first_index:last_index+1]

                        # Join the remaining words back into a string
                        name_str = " ".join(words)
                        found_name=True
                    elif "nome" in words:
                        for i in range(len(words)):
                            name = words[i+1:]
                            name_str = ' '.join(name)
                            # print("Name::",name_str)
                            found_name=True
                            break
                    elif "cognome" in words:
                        for i in range(len(words)):
                            name = words[i+1:]
                            name_str = ' '.join(name)
                            # print("Name::",name_str)
                            found_name=True
                            break   
                # if found_name is False and found_secondary_name is False:
                if found_secondary_name is False:
                    pattern_ignore = r'portfolio|professionale|email|e-mail|curriculum|vitae|informazioni|personali|formazione|academica|formato|europeo|operaia|europass|presentazione|nazionalita|italiana|indirizzo|occupazione'
                    if not re.search(pattern_ignore, text.lower()) and not text.isspace():
                        secondary_name = re.sub(r'(?<!\S)[^a-zA-Z\s]|(?<=\s)\S(?=\s)|(?<=\s)\S$', '', text)
                        found_secondary_name=True

            if found_name is False and found_secondary_name is True:
                name_str=secondary_name
                
            if found_name is True and name_str.isspace():
                name_str=secondary_name

            # Add the data to the list
            if found_email is False and found_secondary_email is True:
                email = secondary_email
            words = name_str.split()
            size = len(words)
            first_name=""
            last_name=""
            if size>0:
                first_name=words[0]
                if size>1:
                    last_name=words[1]
            data.append([first_name, last_name, email])
    # except FileNotFoundError:
    #     print(f"Error: {filename} not found")
    except Exception as e:
        print(f"Error: {filename} - {str(e)}")
        continue

# Write the data to the CSV file
if os.path.isfile(csv_file_path):
    # File already exists, so append data to it
    with open(csv_file_path, "a", newline="",encoding='utf-8') as csv_file:
        writer = csv.writer(csv_file)
        writer.writerows(data)
else:
    with open(csv_file_path, 'w', newline='',encoding='utf-8') as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(['First Name', 'Last Name', 'Email'])
        writer.writerows(data)

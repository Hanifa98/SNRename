import os
from pyzbar.pyzbar import decode
from PIL import Image, ImageEnhance, ImageOps
import pytesseract
import re
import logging

# Configure logging to track renaming process
logging.basicConfig(filename='rename_log.txt', level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s') 

def preprocess_image(image):
    """ Preprocess the image for OCR by converting it to grayscale and enhancing contrast. """
    # Convert to grayscale
    gray_image = ImageOps.grayscale(image)
    
    # Increase contrast
    enhancer = ImageEnhance.Contrast(gray_image)
    enhanced_image = enhancer.enhance(2.0)  # Increase contrast for better OCR results
    
    return enhanced_image

def extract_serial_number_from_zbar_data(data):
    """ Extract serial number (e.g., PF558S19) from ZBar decoded data like URLs. """
    # Use a regular expression to match serial number-like patterns in the data
    serial_match = re.search(r'([A-Z0-9]{8})', data)  # Match 8 alphanumeric characters (customize as needed)
    
    if serial_match:
        return serial_match.group(1)
    else:
        return None

def extract_code_with_zbar(image_path):
    """ Try to extract the QR or barcode from the image using ZBar. """
    try:
        # Open the image
        img = Image.open(image_path)
        
        # Use ZBar to detect and decode the barcode or QR code
        decoded_objects = decode(img)
        
        if decoded_objects:
            # Extract the first detected QR/barcode
            for obj in decoded_objects:
                barcode_data = obj.data.decode("utf-8")  # Decode bytes to string
                print(f"ZBar found QR/Barcode data: {barcode_data} in {image_path}")
                
                # Extract serial number from the QR/Barcode data
                serial_number = extract_serial_number_from_zbar_data(barcode_data)
                
                if serial_number:
                    print(f"Extracted Serial Number from QR/Barcode: {serial_number}")
                    return serial_number
                else:
                    print(f"Could not find a serial number in the QR/Barcode data from {image_path}.")
        
        # No barcode found
        print(f"No barcode/QR code found in {image_path} using ZBar.")
        logging.info(f"No barcode/QR code found in {image_path} using ZBar.")
        return None

    except Exception as e:
        logging.error(f"Error processing {image_path} with ZBar: {e}")
        return None

def extract_serial_number_with_tesseract(image_path):
    """ Fallback method to extract the serial number from the image using Tesseract OCR. """
    try:
        # Open the image
        img = Image.open(image_path)
        
        # Preprocess the image for better OCR performance
        processed_img = preprocess_image(img)
        
        # Use Tesseract to do OCR on the processed image
        text = pytesseract.image_to_string(processed_img)
        
        # Print the extracted text for debugging purposes
        print(f"Tesseract extracted text from {image_path}:\n{text}")
        
        # Use regex to find the serial number (S/N: XXXX or similar patterns)
        serial_number_match = re.search(r'S/N:\s*([A-Za-z0-9]+)', text)
        
        if serial_number_match:
            serial_number = serial_number_match.group(1)
            print(f"Tesseract found Serial Number: {serial_number} in {image_path}")
            return serial_number
        else:
            print(f"No serial number found in {image_path} using Tesseract.")
            logging.info(f"No serial number found in {image_path} using Tesseract.")
            return None

    except Exception as e:
        logging.error(f"Error processing {image_path} with Tesseract: {e}")
        return None

def rename_image(image_path, folder):
    """ Rename the image based on extracted serial number, using ZBar first, then Tesseract. """
    
    # Step 1: Try to extract serial number from QR/Barcode with ZBar
    serial_number = extract_code_with_zbar(image_path)
    
    if serial_number:
        print(f"ZBar successfully extracted serial number: {serial_number}")
        logging.info(f"ZBar successfully extracted serial number: {serial_number} from {image_path}")
    else:
        print(f"ZBar failed, falling back to Tesseract OCR for {image_path}")
        logging.info(f"ZBar failed, falling back to Tesseract OCR for {image_path}")
    
        # Step 2: If ZBar fails, fall back to Tesseract OCR
        serial_number = extract_serial_number_with_tesseract(image_path)
    
    # Step 3: If a valid serial number is found, rename the image
    if serial_number:
        new_filename = f"{serial_number}.jpg"
        new_file_path = os.path.join(folder, new_filename)
        
        try:
            os.rename(image_path, new_file_path)
            logging.info(f"Renamed '{image_path}' to '{new_file_path}'")
            print(f"Renamed '{image_path}' to '{new_file_path}'")
        except Exception as e:
            logging.error(f"Failed to rename {image_path}: {e}")
            print(f"Failed to rename {image_path}: {e}")
    else:
        logging.warning(f"No valid serial number found for {image_path}, skipping.")

# Folder where your images are stored
image_folder = r'C:\Users\maste\Desktop\TestSN'

# Iterate through each image in the folder
for filename in os.listdir(image_folder):
    if filename.endswith(".jpg") or filename.endswith(".png"):
        image_path = os.path.join(image_folder, filename)
        rename_image(image_path, image_folder)

print("Batch processing complete. Check rename_log.txt for details.")

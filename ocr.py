import easyocr
import cv2
import numpy as np
import re

def preprocess_image(image_path):
    # Membaca gambar
    img = cv2.imread(image_path)
    
    # Konversi ke grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Terapkan Gaussian Blur untuk mengurangi noise
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    
    # Terapkan thresholding adaptif
    thresh = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                  cv2.THRESH_BINARY_INV, 11, 2)
    
    return thresh

def read_kwh_meter(image_path):
    try:
        # Inisialisasi EasyOCR reader
        reader = easyocr.Reader(['en'], gpu=False)  # Gunakan 'en' untuk angka dan teks bahasa Inggris
        
        # Pra-pemrosesan gambar
        processed_image = preprocess_image(image_path)
        
        # Simpan gambar yang telah diproses untuk OCR
        temp_image_path = 'processed_kwh.png'
        cv2.imwrite(temp_image_path, processed_image)
        
        # Lakukan OCR
        results = reader.readtext(temp_image_path)
        
        # Ekstrak angka dari hasil OCR
        number_pattern = r'\d+[.,]?\d*'
        kwh_reading = None
        
        for (bbox, text, prob) in results:
            # Cari pola angka (bisa berupa integer atau desimal)
            match = re.search(number_pattern, text)
            if match:
                kwh_reading = match.group()
                # Konversi koma ke titik untuk format desimal
                kwh_reading = kwh_reading.replace(',', '.')
                try:
                    kwh_reading = float(kwh_reading)
                    break
                except ValueError:
                    continue
        
        if kwh_reading is not None:
            print(f"Stand kWh meter: {kwh_reading}")
            return kwh_reading
        else:
            print("Tidak dapat mendeteksi angka pada gambar.")
            return None
            
    except Exception as e:
        print(f"Terjadi kesalahan: {str(e)}")
        return None

if __name__ == "__main__":
    # Ganti dengan path ke gambar kWh meter Anda
    image_path = "kwh1.jpg"
    read_kwh_meter(image_path)
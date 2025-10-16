import os
import uuid
import shutil
import cv2
import numpy as np
import pandas as pd
import requests
import re
from flask import Flask, render_template, request, jsonify, send_from_directory
from ultralytics import YOLO
import pymysql # DIUBAH: Menggunakan library pymysql yang sudah terbukti bekerja
import pymysql.cursors # DIUBAH: Diperlukan untuk mengambil data sebagai dictionary

# ==============================================================================
# KONFIGURASI & INISIALISASI
# ==============================================================================

app = Flask(__name__)

os.makedirs("static/results", exist_ok=True)
os.makedirs("uploads", exist_ok=True)
app.config['UPLOAD_FOLDER'] = 'uploads'

# Konfigurasi DB tidak perlu diubah, karena sudah terbukti benar
DB_CONFIG = {
    'host': '127.0.0.1',
    'user': 'root',
    'password': '',
    'database': 'kwh_detection'
}

# ==============================================================================
# FUNGSI INISIALISASI DATABASE OTOMATIS (MENGGUNAKAN PyMySQL)
# ==============================================================================

def initialize_database():
    try:
        db_config_server = DB_CONFIG.copy()
        db_name = db_config_server.pop('database')
        
        print(f"🔧 Menghubungkan ke server MySQL di {db_config_server.get('host')} dengan PyMySQL...")
        conn_server = pymysql.connect(**db_config_server) # DIUBAH
        cursor_server = conn_server.cursor()
        
        print(f"🔧 Memeriksa keberadaan database '{db_name}'...")
        cursor_server.execute(f"CREATE DATABASE IF NOT EXISTS {db_name} CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci")
        print(f"✅ Database '{db_name}' sudah siap.")
        cursor_server.close()
        conn_server.close()

        conn_db = pymysql.connect(**DB_CONFIG) # DIUBAH
        cursor_db = conn_db.cursor()

        print(f"🔧 Memeriksa keberadaan tabel 'kwh_detection'...")
        create_table_query = """
        CREATE TABLE IF NOT EXISTS kwh_detection (
            BLTH VARCHAR(6) NOT NULL,
            IDPEL VARCHAR(20) NOT NULL,
            KET VARCHAR(50) DEFAULT NULL,
            SAHLWBP VARCHAR(20) DEFAULT NULL,
            SAI VARCHAR(20) DEFAULT NULL,
            STAND_VERIFIKASI VARCHAR(20) DEFAULT NULL,
            ANOTASI VARCHAR(255) DEFAULT NULL,
            VER VARCHAR(10) DEFAULT NULL,
            PRIMARY KEY (BLTH, IDPEL)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
        """
        cursor_db.execute(create_table_query)
        print("✅ Tabel 'kwh_detection' sudah siap.")
        
        cursor_db.close()
        conn_db.close()
        print("🎉 Inisialisasi database berhasil!")

    except Exception as e:
        print(f"❌ FATAL: Gagal melakukan inisialisasi database. Error: {e}")
        exit()

# ==============================================================================
# FUNGSI KONEKSI DATABASE & PEMUATAN MODEL
# ==============================================================================

def get_db_connection():
    try:
        conn = pymysql.connect(**DB_CONFIG) # DIUBAH
        return conn
    except Exception as e:
        print(f"❌ Gagal koneksi database: {e}")
        raise

try:
    print("Memuat model AI...")
    kwh_model = YOLO('model/kwh.pt')
    stand_model = YOLO('model/stand.pt')
    ocr_model = YOLO('model/ocr.pt')
    print("✅ Semua model AI berhasil dimuat.")
    MODELS_LOADED = True
except Exception as e:
    print(f"❌ Error saat memuat model AI: {e}")
    MODELS_LOADED = False

# ==============================================================================
# (SISA KODE DI BAWAH INI TIDAK PERLU DIUBAH, KECUALI view_database)
# FUNGSI INTI PEMROSESAN GAMBAR (LOGIKA AI)
# ==============================================================================

def process_single_image(image_path, save_to_results=False):
    if not MODELS_LOADED:
        return None, "Error: Model AI tidak berhasil dimuat.", None, None, None
    try:
        img = cv2.imread(image_path)
        if img is None: return None, "Gagal membaca file gambar.", None, None, None
    except Exception as e:
        return None, f"Error saat membaca gambar: {e}", None, None, None
    img_result = img.copy()
    kwh_results = kwh_model(img)
    kwh_status, max_kwh_conf, best_kwh_box = "bukan_kwh", 0, None
    if kwh_results and kwh_results[0].boxes:
        for box in kwh_results[0].boxes:
            if box.conf[0] > max_kwh_conf:
                max_kwh_conf = box.conf[0]
                kwh_status = kwh_model.names[int(box.cls[0].item())]
                best_kwh_box = box.xyxy[0]
    if best_kwh_box is not None:
        kx1, ky1, kx2, ky2 = map(int, best_kwh_box)
        label = f"{kwh_status} ({max_kwh_conf:.2f})"
        cv2.rectangle(img_result, (kx1, ky1), (kx2, ky2), (255, 0, 0), 2)
        cv2.putText(img_result, label, (kx1, ky1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
    ocr_text_result = f"Status: {kwh_status}"
    sai = ""
    if kwh_status != 'kwh_jelas':
        result_filename = f"{uuid.uuid4()}.jpg"
        result_folder = os.path.join("static", "results") if save_to_results else app.config['UPLOAD_FOLDER']
        result_path = os.path.join(result_folder, result_filename)
        cv2.imwrite(result_path, img_result)
        anotasi_link = "/" + result_path.replace("\\", "/")
        return result_path, ocr_text_result, kwh_status, sai, anotasi_link
    stand_results = stand_model(img)
    best_stand_box, max_stand_conf = None, 0
    if stand_results and stand_results[0].boxes:
        for box in stand_results[0].boxes:
            if box.conf[0] > max_stand_conf:
                max_stand_conf = box.conf[0]
                best_stand_box = box.xyxy[0]
    if best_stand_box is None:
        ocr_text_result = f"Status: {kwh_status} -> Gagal mendeteksi stand."
        result_filename = f"{uuid.uuid4()}.jpg"
        result_folder = os.path.join("static", "results") if save_to_results else app.config['UPLOAD_FOLDER']
        result_path = os.path.join(result_folder, result_filename)
        cv2.imwrite(result_path, img_result)
        anotasi_link = "/" + result_path.replace("\\", "/")
        return result_path, ocr_text_result, kwh_status, sai, anotasi_link
    sx1, sy1, sx2, sy2 = map(int, best_stand_box)
    cv2.rectangle(img_result, (sx1, sy1), (sx2, sy2), (0, 255, 0), 2)
    roi = img[sy1:sy2, sx1:sx2]
    ocr_results = ocr_model(roi)
    all_detections = []
    if ocr_results and ocr_results[0].boxes:
        for box in ocr_results[0].boxes:
            all_detections.append({'bbox': list(map(int, box.xyxy[0])), 'class_name': ocr_model.names[int(box.cls[0].item())], 'confidence': box.conf[0].item()})
    if not all_detections:
        ocr_text_result = f"Status: {kwh_status} -> Stand terdeteksi, angka tidak terbaca."
    else:
        top_5 = sorted(all_detections, key=lambda x: x['confidence'], reverse=True)[:5]
        sorted_by_pos = sorted(top_5, key=lambda x: x['bbox'][0])
        sai = "".join([det['class_name'] for det in sorted_by_pos])
        cv2.putText(img_result, sai, (sx1, sy1 - 15), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 255), 3)
        ocr_text_result = f"Status: {kwh_status} -> Angka: {sai}"
    result_filename = f"{uuid.uuid4()}.jpg"
    result_folder = os.path.join("static", "results") if save_to_results else app.config['UPLOAD_FOLDER']
    result_path = os.path.join(result_folder, result_filename)
    cv2.imwrite(result_path, img_result)
    anotasi_link = "/" + result_path.replace("\\", "/")
    return result_path, ocr_text_result, kwh_status, sai, anotasi_link

# ==============================================================================
# FUNGSI UPDATE DATABASE
# ==============================================================================

def update_database(blth, idpel, ket, sai, anotasi, existing_data=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        blth = str(blth).strip()
        idpel = str(idpel).strip()
        ket = str(ket).strip() if ket else ''
        sai = str(sai).strip() if sai else ''
        anotasi = str(anotasi).strip() if anotasi else ''
        sahlwbp = existing_data.get('SAHLWBP', '') if existing_data else ''
        stand_verifikasi = sai  # Default STAND_VERIFIKASI ke SAI saat proses awal
        cursor.execute("SELECT VER, STAND_VERIFIKASI FROM kwh_detection WHERE BLTH = %s AND IDPEL = %s", (blth, idpel))
        existing_record = cursor.fetchone()
        if existing_record:
            current_ver = existing_record[0] if existing_record[0] is not None else ''
            current_stand_ver = existing_record[1] if existing_record[1] is not None else stand_verifikasi
            cursor.execute("""
                UPDATE kwh_detection 
                SET KET = %s, SAI = %s, ANOTASI = %s, SAHLWBP = %s, VER = %s, STAND_VERIFIKASI = %s
                WHERE BLTH = %s AND IDPEL = %s
            """, (ket, sai, anotasi, sahlwbp, current_ver, current_stand_ver, blth, idpel))
            print(f"✅ Updated {idpel} BLTH {blth}. Status verifikasi '{current_ver}' DIPERTAHANKAN.")
        else:
            initial_ver = ''
            initial_stand_ver = stand_verifikasi
            cursor.execute("""
                INSERT INTO kwh_detection (BLTH, IDPEL, KET, SAHLWBP, SAI, STAND_VERIFIKASI, ANOTASI, VER)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (blth, idpel, ket, sahlwbp, sai, initial_stand_ver, anotasi, initial_ver))
            print(f"✅ Inserted {idpel} BLTH {blth} ke database.")
        conn.commit()
    except Exception as e:
        print(f"❌ Error DB untuk {idpel} BLTH {blth}: {e}")
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()

# ==============================================================================
# ROUTE / ENDPOINT APLIKASI WEB
# ==============================================================================

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/uploads/<path:filename>')
def serve_uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/api/process_upload', methods=['POST'])
def handle_process_upload():
    if 'images' not in request.files:
        return jsonify({'error': 'Tidak ada file gambar yang dikirim. Silakan pilih setidaknya satu file gambar.'}), 400
    files = request.files.getlist('images')
    results = []
    for file in files:
        if not file.filename:
            results.append({'filename': 'unknown', 'result_text': 'Gagal: Nama file tidak valid.', 'result_image_url': ''})
            continue
        temp_filename = f"{uuid.uuid4()}_{file.filename}"
        temp_path = os.path.join(app.config['UPLOAD_FOLDER'], temp_filename)
        try:
            file.save(temp_path)
            result_image_path, result_text, ket, sai, anotasi = process_single_image(temp_path, save_to_results=False)
            if result_image_path:
                result_image_url = f"/uploads/{os.path.basename(result_image_path)}"
                results.append({'filename': file.filename, 'result_text': result_text, 'result_image_url': result_image_url})
            else:
                results.append({'filename': file.filename, 'result_text': result_text or 'Gagal: Gambar tidak dapat diproses.', 'result_image_url': ''})
        except Exception as e:
            results.append({'filename': file.filename, 'result_text': f'Gagal memproses gambar: {str(e)}', 'result_image_url': ''})
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
    return jsonify(results)

@app.route('/api/download_and_process', methods=['POST'])
def handle_download_and_process():
    jsessionid = request.form.get('jsessionid')
    pool_acmt = request.form.get('poolacmt')
    blth_string = request.form.get('blth')
    excel_file = request.files.get('excel_file')
    if not all([excel_file, blth_string, jsessionid, pool_acmt]):
        return jsonify({'error': 'Semua field harus diisi lengkap'}), 400
    blth_list = [item for item in re.split(r'[\s,;]+', blth_string) if item]
    excel_temp_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{uuid.uuid4()}_temp.xlsx")
    excel_file.save(excel_temp_path)
    download_temp_dir = os.path.join(app.config['UPLOAD_FOLDER'], str(uuid.uuid4()))
    os.makedirs(download_temp_dir)
    results = []
    try:
        df = pd.read_excel(excel_temp_path, dtype={'IDPEL': str})
        if 'SAHLWBP' in df.columns:
            df['SAHLWBP'] = df['SAHLWBP'].fillna('').astype(str).str.split('.').str[0].str.replace(',', '').str.strip()
        columns = df.columns.tolist()
        session = requests.Session()
        session.headers.update({'User-Agent': 'Mozilla/5.0'})
        session.cookies.update({'JSESSIONID': jsessionid, 'Pool_ACMTJava': pool_acmt})
        path_foto_base = 'https://portalapp.iconpln.co.id/acmt/DisplayBlobServlet1?idpel='
        path_foto_blth = '&blth='
        for blth in blth_list:
            print(f"--- Memulai proses untuk BLTH: {blth} ---")
            for index, row in df.iterrows():
                idpel = str(row['IDPEL']).strip()
                existing_data = {col: str(row.get(col, '')).strip() for col in columns if col not in ['IDPEL', 'BLTH']}
                url = f"{path_foto_base}{idpel}{path_foto_blth}{blth}"
                try:
                    response = session.get(url, stream=True, timeout=15)
                    response.raise_for_status()
                    content_type = response.headers.get('Content-Type', '')
                    if 'text/html' in content_type:
                        raise requests.RequestException("Sesi login (JSESSIONID) kemungkinan kedaluwarsa.")
                    downloaded_img_path = os.path.join(download_temp_dir, f"{idpel}_{blth}.jpg")
                    with open(downloaded_img_path, 'wb') as f: f.write(response.content)
                    print(f"✅ Gambar untuk {idpel} BLTH {blth} berhasil di-download")
                    result_image_path, result_text, ket, sai, anotasi = process_single_image(downloaded_img_path, save_to_results=True)
                    print(f"✅ Gambar untuk {idpel} BLTH {blth} berhasil diproses: {result_text}")
                    if result_image_path:
                        result_image_url = f"/static/results/{os.path.basename(result_image_path)}"
                        results.append({'filename': f"{idpel}_{blth}.jpg", 'result_text': result_text, 'result_image_url': result_image_url})
                        update_database(blth, idpel, ket, sai, anotasi, existing_data)
                    else:
                        results.append({'filename': f"{idpel}_{blth}.jpg", 'result_text': result_text or 'Gagal memproses gambar.', 'result_image_url': ''})
                except requests.RequestException as e:
                    if "Sesi login" in str(e):
                        print("❌ Kesalahan Fatal: Sesi login (JSESSIONID) kedaluwarsa. Proses dihentikan.")
                        return jsonify({'error': 'Gagal: Sesi login (JSESSIONID) salah atau kedaluwarsa. Proses dihentikan.'}), 400
                    error_message = f"Gagal download: {e}"
                    if hasattr(e, 'response') and e.response is not None and e.response.status_code == 404:
                        error_message = "Gagal: Gambar untuk IDPEL atau BLTH ini tidak ditemukan di server."
                    print(f"❌ {error_message} untuk IDPEL {idpel} BLTH {blth}")
                    results.append({'filename': f"{idpel}_{blth}.jpg", 'result_text': error_message, 'result_image_url': '', 'is_error': True})
    except Exception as e:
        print(f"❌ Error utama di download_and_process: {e}")
        return jsonify({'error': f'Terjadi kesalahan saat memproses: {e}'}), 500
    finally:
        if os.path.exists(excel_temp_path): os.remove(excel_temp_path)
        if os.path.exists(download_temp_dir): shutil.rmtree(download_temp_dir)
        print("🧹 Membersihkan file sementara")
    return jsonify(results)

@app.route('/api/view_database', methods=['GET'])
def view_database():
    conn = None
    try:
        filter_type = request.args.get('filter', 'all')
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        query = "SELECT * FROM kwh_detection"
        if filter_type == 'unverified':
            query += " WHERE VER IS NULL OR VER = ''"
        elif filter_type == 'sesuai':
            query += " WHERE VER = 'sesuai'"
        elif filter_type == 'tidak':
            query += " WHERE VER = 'tidak'"
        query += " ORDER BY BLTH DESC, IDPEL"
        
        cursor.execute(query)
        rows = cursor.fetchall()
        print(f"📋 Mengambil {len(rows)} baris dari database")
        return jsonify(rows)
    except Exception as e:
        print(f"❌ Error saat query database: {e}")
        return jsonify({'error': f'Gagal mengambil data: {e}'}), 500
    finally:
        if conn:
            conn.close()

@app.route('/api/update_ver', methods=['POST'])
def update_ver():
    data = request.json
    blth = data.get('blth')
    idpel = data.get('idpel')
    ver = data.get('ver')
    ket = data.get('ket')
    stand_verifikasi = data.get('stand_verifikasi')
    if not blth or not idpel:
        return jsonify({'error': 'Data tidak lengkap'}), 400
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE kwh_detection SET VER = %s, KET = %s, STAND_VERIFIKASI = %s WHERE BLTH = %s AND IDPEL = %s", (ver, ket, stand_verifikasi, blth, idpel))
        conn.commit()
        print(f"✅ Updated VER untuk {idpel} BLTH {blth} ke {ver}")
        return jsonify({'success': True})
    except Exception as e:
        print(f"❌ Error update VER untuk {idpel} BLTH {blth}: {e}")
        return jsonify({'error': 'Gagal update'}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/update_all_ver', methods=['POST'])
def update_all_ver():
    data = request.json
    if not data or not isinstance(data, list):
        return jsonify({'error': 'Data tidak valid, harus berupa daftar'}), 400
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        for item in data:
            blth = item.get('blth')
            idpel = item.get('idpel')
            ver = item.get('ver')
            if not blth or not idpel or not ver:
                print(f"⚠️ Data tidak lengkap untuk {idpel} BLTH {blth}")
                continue
            cursor.execute("UPDATE kwh_detection SET VER = %s WHERE BLTH = %s AND IDPEL = %s", (ver, blth, idpel))
            print(f"✅ Updated VER untuk {idpel} BLTH {blth} ke {ver}")
        conn.commit()
        return jsonify({'success': True, 'message': 'Semua perubahan VER tersimpan'})
    except Exception as e:
        print(f"❌ Error saat update semua VER: {e}")
        return jsonify({'error': f'Gagal menyimpan perubahan: {e}'}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/api/cleanup_uploads', methods=['POST'])
def cleanup_uploads():
    try:
        upload_folder = app.config['UPLOAD_FOLDER']
        for filename in os.listdir(upload_folder):
            file_path = os.path.join(upload_folder, filename)
            if os.path.isfile(file_path):
                os.remove(file_path)
        print("🧹 Membersihkan folder uploads")
        return jsonify({'success': True})
    except Exception as e:
        print(f"❌ Error saat membersihkan folder uploads: {e}")
        return jsonify({'error': f'Gagal membersihkan folder: {e}'}), 500

# ==============================================================================
# MENJALANKAN APLIKASI
# ==============================================================================

# Panggil fungsi inisialisasi untuk memastikan DB dan tabel siap sebelum aplikasi berjalan
initialize_database()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
import os
import shutil
import zipfile
import random
from collections import defaultdict

def split_yolo_dataset_with_negatives(zip_path, output_dir, train_ratio=0.9):
    """
    Membagi dataset gambar dan label (termasuk gambar negatif dengan label kosong)
    dari file ZIP Label Studio (format YOLO) menjadi folder training dan validation.

    Args:
        zip_path (str): Path menuju file .zip Anda.
        output_dir (str): Folder tujuan untuk menyimpan hasil split.
        train_ratio (float): Perbandingan untuk data training (contoh: 0.9 untuk 90%).
    """
    
    # --- 1. Persiapan Folder ---
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    
    extract_dir = os.path.join(os.path.dirname(output_dir), "temp_extracted_data")
    if os.path.exists(extract_dir):
        shutil.rmtree(extract_dir)
    os.makedirs(extract_dir)

    train_images_dir = os.path.join(output_dir, 'train', 'images')
    train_labels_dir = os.path.join(output_dir, 'train', 'labels')
    val_images_dir = os.path.join(output_dir, 'validation', 'images')
    val_labels_dir = os.path.join(output_dir, 'validation', 'labels')

    for path in [train_images_dir, train_labels_dir, val_images_dir, val_labels_dir]:
        os.makedirs(path, exist_ok=True)
    print("📂 Folder output berhasil dibuat.")

    # --- 2. Ekstrak File ZIP ---
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
        print(f"✅ File '{os.path.basename(zip_path)}' berhasil diekstrak.")
    except (FileNotFoundError, zipfile.BadZipFile) as e:
        print(f"❌ Error: {e}")
        shutil.rmtree(extract_dir)
        return

    source_images_dir = os.path.join(extract_dir, 'images')
    source_labels_dir = os.path.join(extract_dir, 'labels')

    if not os.path.exists(source_images_dir) or not os.path.exists(source_labels_dir):
        print("❌ Error: Struktur folder 'images' atau 'labels' tidak ditemukan di dalam ZIP.")
        shutil.rmtree(extract_dir)
        return

    # --- 3. Mengkategorikan Gambar Positif dan Negatif ---
    print("\n🔄 Mengkategorikan gambar positif dan negatif...")
    
    all_image_files = [f for f in os.listdir(source_images_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    positive_basenames = []
    negative_basenames = []

    for img_file in all_image_files:
        basename = os.path.splitext(img_file)[0]
        label_path = os.path.join(source_labels_dir, basename + '.txt')
        
        # Cek apakah label ada dan tidak kosong
        if os.path.exists(label_path) and os.path.getsize(label_path) > 0:
            positive_basenames.append(basename)
        else:
            negative_basenames.append(basename)
    
    print(f"📊 Ditemukan {len(positive_basenames)} gambar positif dan {len(negative_basenames)} gambar negatif.")

    # --- 4. Memisahkan Data ---

    # Helper function untuk menyalin file
    def copy_files(basenames, dest_img_dir, dest_lbl_dir):
        for basename in basenames:
            # Cari ekstensi gambar yang mungkin
            for ext in ['.jpg', '.jpeg', '.png']:
                img_filename = basename + ext
                src_img_path = os.path.join(source_images_dir, img_filename)
                if os.path.exists(src_img_path):
                    shutil.copy(src_img_path, dest_img_dir)
                    
                    # Salin label jika ada (termasuk yang kosong)
                    src_lbl_path = os.path.join(source_labels_dir, basename + '.txt')
                    if os.path.exists(src_lbl_path):
                        shutil.copy(src_lbl_path, dest_lbl_dir)
                    else:
                        # Buat file label kosong jika tidak ada sama sekali
                        open(os.path.join(dest_lbl_dir, basename + '.txt'), 'w').close()
                    break

    # 4a. Proses Gambar Positif (Stratified Split)
    print("\n🔀 Memisahkan gambar positif per kelas...")
    images_by_class = defaultdict(list)
    for basename in positive_basenames:
        with open(os.path.join(source_labels_dir, basename + '.txt'), 'r') as f:
            classes_in_file = set(line.split()[0] for line in f if line.strip())
            for class_id in classes_in_file:
                images_by_class[class_id].append(basename)
    
    processed_files = set()
    for class_id, basenames in images_by_class.items():
        random.shuffle(basenames)
        split_index = int(len(basenames) * train_ratio)
        train_basenames = basenames[:split_index]
        val_basenames = basenames[split_index:]

        # Salin file yang belum pernah diproses sebelumnya
        copy_files([b for b in train_basenames if b not in processed_files], train_images_dir, train_labels_dir)
        copy_files([b for b in val_basenames if b not in processed_files], val_images_dir, val_labels_dir)
        
        processed_files.update(basenames)

    # 4b. Proses Gambar Negatif
    print("\n🔀 Memisahkan gambar negatif...")
    random.shuffle(negative_basenames)
    neg_split_index = int(len(negative_basenames) * train_ratio)
    train_neg_basenames = negative_basenames[:neg_split_index]
    val_neg_basenames = negative_basenames[neg_split_index:]

    copy_files(train_neg_basenames, train_images_dir, train_labels_dir)
    copy_files(val_neg_basenames, val_images_dir, val_labels_dir)
    print(f"  -> {len(train_neg_basenames)} negatif ke training, {len(val_neg_basenames)} negatif ke validation.")

    # --- 5. Membersihkan & Ringkasan ---
    shutil.rmtree(extract_dir)
    num_train = len(os.listdir(train_images_dir))
    num_val = len(os.listdir(val_images_dir))
    total = num_train + num_val
    
    print("\n🎉 Proses Selesai!")
    print("---------------------------------")
    print(f"Total Gambar    : {total}")
    print(f"Data Training   : {num_train} gambar ({num_train/total:.1%})")
    print(f"Data Validation : {num_val} gambar ({num_val/total:.1%})")
    print(f"Hasil disimpan di: '{os.path.abspath(output_dir)}'")
    print("---------------------------------")


# --- CARA PENGGUNAAN (TETAP SAMA) ---
if __name__ == '__main__':
    # 1. Ganti dengan path file ZIP Anda
    zip_file_path = "labeling_foto_kwh.zip" 

    # 2. Tentukan nama folder untuk menyimpan hasilnya
    output_folder = "dataset_split" 
    
    # 3. Jalankan fungsi
    split_yolo_dataset_with_negatives(zip_file_path, output_folder)
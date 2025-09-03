# WGS_CUDAmaplibrePY

## Deskripsi Proyek
WGS_CUDAmaplibrePY adalah simulator penerbangan dan visualisasi radar berbasis web yang menampilkan pergerakan pesawat secara real-time di atas peta. Aplikasi ini menggunakan CUDA untuk akselerasi simulasi di sisi backend dan MapLibre GL / Deck.gl di sisi frontend untuk rendering.

## Fitur
- **Visualisasi Real-time:** Menampilkan posisi pesawat di atas peta interaktif.
- **Simulasi Berbasis CUDA:** Simulasi pergerakan dan deteksi radar dipercepat menggunakan GPU, memungkinkan penanganan ribuan objek secara efisien.
- **Kontrol Interaktif:** Pengguna dapat memberikan perintah kepada pesawat secara individu atau dalam kelompok, seperti mengubah kecepatan, arah, dan ketinggian.
- **Visualisasi Radar:** Menampilkan jangkauan radar dan animasi pemindaian (sweep) untuk setiap stasiun radar.

## Alur Kerja Aplikasi
1. **Backend (FastAPI):**
   - Menjalankan server web menggunakan FastAPI.
   - Menyajikan halaman `index.html` sebagai antarmuka utama.
   - Membuka koneksi WebSocket (`/ws`) untuk mengirimkan data posisi pesawat ke frontend secara real-time.
   - Menerima perintah dari frontend (misalnya, mengubah kecepatan pesawat) melalui WebSocket.
   - Mengekspos endpoint `/radars` untuk menyediakan daftar lokasi radar ke frontend.

2. **Simulasi (CUDA/Numba):**
   - Inisialisasi posisi, kecepatan, dan status ribuan pesawat menggunakan NumPy.
   - Semua data simulasi ditransfer ke memori GPU.
   - Kernel CUDA yang ditulis menggunakan Numba dijalankan setiap frame untuk:
     - Memperbarui pergerakan setiap pesawat berdasarkan perintah yang diterima.
     - Mendeteksi pesawat mana yang berada dalam jangkauan stasiun radar.
   - Hasil simulasi (posisi baru) disalin kembali dari GPU ke CPU untuk dikirim ke frontend.

3. **Frontend (HTML/JavaScript):**
   - Memuat peta menggunakan MapLibre GL.
   - Menggunakan Deck.gl untuk merender lapisan (layer) data di atas peta, termasuk ikon pesawat dan poligon jangkauan radar.
   - Membuka koneksi WebSocket ke backend untuk menerima pembaruan posisi pesawat.
   - Saat data baru diterima, posisi ikon pesawat di peta diperbarui.
   - Menyediakan antarmuka untuk memilih pesawat dan mengirim perintah kontrol kembali ke backend.

## Dependensi
### Backend (Python)
- `fastapi`: Untuk server web.
- `uvicorn`: Sebagai ASGI server untuk FastAPI.
- `websockets`: Untuk komunikasi real-time.
- `numpy`: Untuk operasi numerik dan inisialisasi data.
- `numba`: Untuk kompilasi just-in-time (JIT) kernel CUDA.

**Prasyarat Backend:**
- **GPU NVIDIA** yang mendukung CUDA.
- **CUDA Toolkit** yang terinstal dan sesuai dengan driver NVIDIA Anda.

Untuk menginstal dependensi Python, jalankan:
```bash
pip install fastapi uvicorn websockets numpy numba
```

### Frontend (JavaScript)
Dependensi frontend diambil melalui CDN dan sudah termasuk di dalam `index.html`:
- **MapLibre GL JS:** Pustaka untuk rendering peta.
- **Deck.gl:** Pustaka untuk visualisasi data di atas peta.

## Cara Menjalankan Aplikasi
1. **Pastikan Prasyarat Terpenuhi:**
   - Python 3.x terinstal.
   - GPU NVIDIA dan CUDA Toolkit terinstal dengan benar.

2. **Instal Dependensi Python:**
   ```bash
   pip install -r requirements.txt
   ```
   *(Catatan: Anda perlu membuat file `requirements.txt` yang berisi daftar dependensi di atas).*

3. **Jalankan Server Backend:**
   ```bash
   uvicorn main:app --reload
   ```
   Server akan berjalan di `http://127.0.0.1:8000`.

4. **Buka Aplikasi di Browser:**
   Buka browser web Anda dan arahkan ke `http://127.0.0.1:8000`. Peta dengan simulasi pesawat akan ditampilkan.

## Rencana Pengembangan (Update Berikutnya)
- **Manajemen Skenario:** Kemampuan untuk menyimpan dan memuat skenario simulasi (posisi awal pesawat, lokasi radar, dll.).
- **Model Fisika yang Lebih Kompleks:** Menambahkan pengaruh cuaca (angin) atau model penerbangan yang lebih realistis.
- **Deteksi Tabrakan:** Menambahkan logika untuk mendeteksi potensi tabrakan antar pesawat.
- **Tampilan Data Telemetri:** Menampilkan informasi lebih detail untuk setiap pesawat yang dipilih (kecepatan, ketinggian, dll.) dalam panel khusus.
- **Optimalisasi Lanjutan:** Penelitian penggunaan memori bersama (shared memory) pada CUDA untuk meningkatkan performa.
- **Unit Tests:** Membuat unit test untuk memvalidasi logika simulasi.
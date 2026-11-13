# SCREENFLOW — Screening Management System

Aplikasi screening peserta berbasis QR Code dengan Flask, SQLite, Flask-Login, CSRF, SQLAlchemy, dan dashboard terpisah untuk Super Admin serta Mentor.

## Fitur

- Landing page publik dan QR scanner kamera belakang (html5-qrcode; kamera membutuhkan HTTPS saat online).
- Form screening tanpa akun peserta, token QR acak per mentor, dan validasi token aktif di backend.
- 10 akun mentor dibuat otomatis pada inisialisasi database.
- Isolasi data mentor diterapkan pada seluruh query detail, daftar, review, dan API polling.
- Pencegahan NIM ganda per periode melalui unique constraint database.
- Status Pending / Lolos / Tidak Lolos, catatan evaluasi, waktu keputusan, dan audit log.
- Dashboard admin, manajemen mentor, reset QR, aktivasi/nonaktifkan, periode screening, filter, pagination, dan export CSV UTF-8.
- Polling dashboard mentor setiap 7 detik.
- CSRF untuk form POST, password hashing Werkzeug, role authorization, cookie session aman pada production.

## Persyaratan

Python 3.10+ disarankan. Kamera browser memerlukan HTTPS (kecuali localhost). Tailwind CDN dan html5-qrcode CDN membutuhkan koneksi internet pada browser.

## Instalasi lokal

```bash
cd screenflow
python -m venv .venv
# Windows: .venv\\Scripts\\activate
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env`, terutama `SECRET_KEY` dengan nilai acak panjang. Jalankan:

```bash
python run.py
```

Database SQLite, periode awal, 1 Super Admin, dan 10 mentor dibuat otomatis saat pertama kali aplikasi dijalankan. Kredensial awal dibuat acak (kecuali admin password diatur melalui environment) dan ditulis satu kali ke `instance/initial_credentials.txt`. Simpan file tersebut secara aman, login, lalu ubah password. File kredensial masuk `.gitignore` dan tidak disajikan oleh web server.

Default username Super Admin adalah `admin`. Username mentor: `mentor01` sampai `mentor10`. Password acak ada di file kredensial awal. Jangan menghapus file tersebut sebelum kredensial disimpan.

## Environment

| Variable | Keterangan |
|---|---|
| `SECRET_KEY` | Wajib diganti untuk production |
| `DATABASE_URL` | Default SQLite di `instance/screenflow.db` |
| `PUBLIC_BASE_URL` | URL publik production, mis. `https://screening.example.com` |
| `SCREENFLOW_ADMIN_USERNAME` | Username admin bootstrap (default `admin`) |
| `SCREENFLOW_ADMIN_PASSWORD` | Password bootstrap opsional; jika kosong dibuat acak |
| `FLASK_ENV` | Set `production` untuk cookie Secure |

Atur `PUBLIC_BASE_URL` sebelum mengunduh QR untuk deployment agar URL QR menggunakan domain production. Tanpa variabel ini, URL QR dibentuk dari host request saat unduhan.

## URL penting

- `/` landing peserta
- `/scan` scanner QR
- `/s/<token>` formulir screening
- `/health` health check
- `/admin/login` dan `/admin/dashboard`
- `/mentor/login` dan `/mentor/dashboard`
- `/logout` (POST saja)

## Deployment PythonAnywhere (ringkas)

1. Upload folder project ke PythonAnywhere dan buat virtualenv Python yang sesuai.
2. Install dependency: `pip install -r requirements.txt`.
3. Buat file `.env` di root project dengan `SECRET_KEY` random, `PUBLIC_BASE_URL=https://username.pythonanywhere.com`, `FLASK_ENV=production`, dan `DATABASE_URL=sqlite:////home/username/screenflow/instance/screenflow.db` (sesuaikan path).
4. Jalankan `python run.py` sekali dari console untuk bootstrap database dan kredensial.
5. Pada tab Web, buat konfigurasi WSGI dengan isi inti berikut:

```python
import sys
project = '/home/username/screenflow'
if project not in sys.path:
    sys.path.insert(0, project)
from app import create_app
application = create_app()
```

6. Set working directory ke project, virtualenv ke virtualenv yang benar, lalu reload web app.
7. HTTPS aktif di domain hosting. Kamera scanner memerlukan HTTPS.
8. Pastikan folder `instance/` writable oleh user aplikasi. Jangan expose `instance/` melalui static mapping.

## Backup SQLite

Hentikan sementara penulisan atau gunakan SQLite backup API. Cara sederhana saat aplikasi tidak sedang menulis:

```bash
cp instance/screenflow.db instance/screenflow-backup-$(date +%F).db
```

Simpan backup di lokasi privat terenkripsi. Uji pemulihan secara berkala.

## Pengujian

```bash
pytest -q
```

## Catatan operasional / batasan implementasi

- CSV disediakan; XLSX/PDF belum diaktifkan.
- Status review dibatasi ke mentor pemilik peserta; admin bersifat read-only untuk keputusan guna menjaga aturan pemilik proses.
- Akun mentor diarsipkan dengan menonaktifkan akun. Penghapusan fisik sengaja tidak disediakan agar relasi peserta dan audit tetap utuh.
- Pengelolaan tanggal mulai/akhir periode tersedia pada skema, sedangkan UI saat ini mengaktifkan periode melalui status aktif.
- Untuk production, gunakan reverse proxy/hosting HTTPS, secret key kuat, backup rutin, dan jangan commit `.env` atau file kredensial awal.

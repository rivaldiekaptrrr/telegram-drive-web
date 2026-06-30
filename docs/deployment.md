# Panduan Deployment (Docker, CI/CD & Coolify)

Dokumen ini menjelaskan struktur deployment aplikasi Telegram Drive Web menggunakan teknologi kontainerisasi (Docker) dan integrasi Continuous Integration / Continuous Deployment (CI/CD) dengan **Coolify**.

---

## 🏗 Arsitektur Deployment

Aplikasi ini menggunakan pendekatan **Single Docker Image (Multi-stage Build)** yang sangat simpel namun efisien.

1. **Stage 1 (Node.js Builder):**
   - Melakukan instalasi dependensi Frontend (React/Vite) dan mengkompilasinya menjadi file statis (HTML/JS/CSS).

2. **Stage 2 (Python FastAPI Web Server):**
   - Menggunakan image `python:3.11-slim`.
   - Menginstal dependensi Backend.
   - Hasil kompilasi Frontend dari Stage 1 disalin ke dalam folder `static/` di Backend.
   - FastAPI bertindak ganda: melayani rute API di endpoint `/api/*`, dan melayani file statis Frontend di rute lainnya (Catch-All SPA Routing).

### Persistent Volumes yang Diperlukan:
Saat men-deploy di Coolify, pastikan Anda mengatur pemetaan volume (Volume Mappings) untuk dua lokasi ini agar data tidak hilang saat restart:
- `/app/db` (Tempat menyimpan file index SQLite `app.db`)
- `/app/session` (Tempat menyimpan session login Telegram)

---

## 🚀 Panduan Deployment dengan Coolify

Coolify mendukung konfigurasi berbasis GitOps yang mampu mendeteksi file `docker-compose.yml` yang sudah disiapkan. Berikut adalah langkah integrasinya:

### 1. Menambahkan Proyek ke Coolify
1. Buka dashboard **Coolify**.
2. Masuk ke menu **Projects** dan buat project/environment baru.
3. Klik **Add Resource** dan pilih **Public/Private Repository** (berdasarkan status repo GitHub Anda).
4. Pilih repository ini dan branch `main`.
5. Saat ditanya *Build Pack*, pilih **Dockerfile**.

Coolify akan secara otomatis membaca file `Dockerfile` di folder *root* proyek Anda dan membangun image tunggal secara efisien.

### 2. Mengatur Konfigurasi Server (Domain & Volume)
1. Di halaman pengaturan aplikasi pada Coolify, atur **Domains** ke URL yang Anda inginkan (misal: `https://drive.domainanda.com`).
2. Masuk ke tab **Storages (Volumes)** dan tambahkan dua volume *persistent* untuk lokasi container berikut:
   - Destination Path: `/app/db`
   - Destination Path: `/app/session`
3. Ini memastikan file `app.db` dan login Telegram tidak hilang saat Coolify me-restart/re-deploy aplikasi Anda.

### 3. Mengatur Auto Deploy (CI/CD) via GitHub Actions
Secara default, Coolify dapat otomatis men-deploy setiap kali ada kode yang di-*push* jika Anda menggunakan GitHub App milik Coolify. Namun, proyek ini juga memiliki pipeline **GitHub Actions** (`.github/workflows/ci.yml`) khusus yang melakukan test-build terlebih dahulu:

1. **Build Checking:** Actions ini memastikan bahwa image Backend & Frontend dapat di-build dengan sukses sebelum deploy. Ini untuk menghindari kasus "Broken Build" tayang di produksi.
2. **Deploy Trigger:**
   Jika tes build berhasil, Github Actions akan mengeksekusi trigger deploy ke server Coolify Anda melalui mekanisme *Webhook*.

**Cara Mengaktifkan Webhook ini:**
1. Di halaman konfigurasi project Anda di Coolify, buka tab **Webhooks**.
2. Salin tautan **Deploy Webhook URL**.
3. Buka halaman repository GitHub Anda, masuk ke **Settings** > **Secrets and variables** > **Actions**.
4. Buat sebuah *New repository secret*:
   - Name: `COOLIFY_WEBHOOK`
   - Secret: *(Paste URL yang disalin dari Coolify tadi)*
5. Simpan. Mulai dari sekarang, setiap Anda melakukan *push* kode, GitHub akan menguji build, lalu otomatis memberi tahu Coolify untuk memperbarui server produksi.

---

## 💻 Menjalankan Secara Lokal (Local Development)

Jika Anda ingin mengetes Single Docker Image di komputer lokal Anda:

```bash
# Build image
docker build -t telegram-drive-web .

# Jalankan container (dengan mount volume lokal jika diinginkan)
docker run -d -p 8000:8000 --name tdweb telegram-drive-web
```
Setelah berjalan, aplikasi web (Frontend + API) dapat diakses di `http://localhost:8000`.

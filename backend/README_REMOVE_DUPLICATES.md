# Script Penghapusan Data Duplikat

## 📋 Deskripsi

Script ini digunakan untuk memeriksa dan menghapus data duplikat dari semua tabel di database PostgreSQL. Script ini aman dan hanya menghapus baris yang **SEMUA kolomnya** sama persis (termasuk nilai NULL).

## 📁 File-file yang Tersedia

### 1. `remove_duplicates_final.py` ⭐ **RECOMMENDED**
Script utama yang memiliki dua mode:
- **Mode Check** (default): Hanya memeriksa duplikat tanpa menghapus
- **Mode Remove**: Menghapus duplikat setelah konfirmasi

### 2. Script Lama (Deprecated)
- `remove_duplicates.py` - ❌ **JANGAN DIGUNAKAN** (bug: menghapus semua data)
- `check_duplicates.py` - ❌ **JANGAN DIGUNAKAN** (bug: tidak berfungsi)
- `remove_duplicates_safe.py` - ⚠️ Versi lama
- `check_duplicates_safe.py` - ⚠️ Versi lama

## 🚀 Cara Penggunaan

### Mode 1: Memeriksa Duplikat (Aman)

Jalankan script tanpa parameter untuk melihat laporan duplikat:

```bash
# Dari host machine
docker exec prd_backend python3 remove_duplicates_final.py

# Atau dari dalam container
python3 remove_duplicates_final.py
```

Output akan menampilkan:
- Total baris per tabel
- Jumlah baris unik
- Jumlah baris duplikat
- Ringkasan keseluruhan

### Mode 2: Menghapus Duplikat

Jalankan dengan flag `--remove` untuk menghapus duplikat:

```bash
# Dari host machine
docker exec -i prd_backend python3 remove_duplicates_final.py --remove

# Script akan meminta konfirmasi
# Ketik 'YA' untuk melanjutkan
```

**⚠️ PERINGATAN**: Pastikan Anda sudah membuat backup database sebelum menjalankan mode remove!

## 🔍 Cara Kerja Script

### Definisi Duplikat Exact

Script ini menganggap dua baris sebagai duplikat jika:
- **SEMUA kolom** (kecuali ID/primary key) memiliki nilai yang sama persis
- Termasuk nilai NULL (dua NULL dianggap sama)

### Algoritma

1. Untuk setiap tabel, script mengambil semua kolom kecuali kolom ID
2. Menggunakan `DISTINCT ON` PostgreSQL untuk menemukan baris unik pertama dari setiap grup duplikat
3. Menyimpan ID dari baris unik tersebut
4. Menghapus semua baris yang ID-nya TIDAK ada dalam daftar ID unik

### Contoh

Jika tabel `users` memiliki:
```
id | username | email
---|----------|-------
1  | admin    | admin@example.com
2  | admin    | admin@example.com  <- DUPLIKAT (akan dihapus)
3  | user1    | user1@example.com
```

Script akan:
- Menemukan bahwa baris 1 dan 2 adalah duplikat
- Menyimpan baris 1 (yang pertama)
- Menghapus baris 2

## 📊 Tabel yang Diproses

Script memproses 12 tabel berikut:

| Tabel | Kolom ID |
|-------|----------|
| audit_log | id |
| chat_history | id |
| domain_notes | id |
| feedback | id_feedback |
| generated_domains | id_domain |
| generator_settings | id |
| history_log | id |
| object_detection | id_detection |
| reasoning | id_reasoning |
| results | id_results |
| users | id |
| announcements | id |

## 🛡️ Keamanan

### Fitur Keamanan:
1. **Konfirmasi User**: Mode remove meminta konfirmasi 'YA' sebelum menghapus
2. **Dry Run**: Mode check tidak mengubah data sama sekali
3. **Transaction Rollback**: Jika terjadi error pada satu tabel, hanya tabel tersebut yang di-rollback
4. **Parameterized Queries**: Menggunakan parameterized queries untuk mencegah SQL injection

### Backup Database

**SANGAT DISARANKAN** untuk membuat backup sebelum menghapus duplikat:

```bash
# Backup database
docker exec prd_postgres pg_dump -U postgres prd > backup_$(date +%Y%m%d_%H%M%S).sql

# Restore jika diperlukan
cat backup_20251219_151055.sql | docker exec -i prd_postgres psql -U postgres -d prd
```

## 📝 Contoh Output

### Mode Check:
```
================================================================================
LAPORAN PEMERIKSAAN DATA DUPLIKAT EXACT
================================================================================
Waktu: 2025-12-19 15:18:55
Database: prd @ postgres:5432

ℹ️  Duplikat exact = baris dengan SEMUA kolom sama persis (termasuk NULL)
================================================================================

📡 Menghubungkan ke database...
✓ Koneksi berhasil!

🔍 Memeriksa 12 tabel...

📋 Tabel: users
  Total baris: 10
  Baris unik: 5
  Baris duplikat: 5
  ⚠️  Ada 5 baris duplikat

================================================================================
RINGKASAN
================================================================================
Total tabel diperiksa: 12
Tabel dengan duplikat: 1
Total baris duplikat: 5

Detail tabel dengan duplikat:
  - users: 5 duplikat dari 10 baris total

💡 Untuk menghapus duplikat, jalankan:
   docker exec -i prd_backend python3 remove_duplicates_final.py --remove
================================================================================
```

### Mode Remove:
```
⚠️  PERINGATAN: Script ini akan menghapus data duplikat EXACT dari SEMUA tabel!
⚠️  Duplikat exact = baris dengan SEMUA kolom sama persis (termasuk NULL)
⚠️  Pastikan Anda sudah membuat backup database sebelum melanjutkan.

Apakah Anda yakin ingin melanjutkan? (ketik 'YA' untuk melanjutkan): YA

================================================================================
SCRIPT PENGHAPUSAN DATA DUPLIKAT EXACT
================================================================================
Waktu mulai: 2025-12-19 15:20:00
Database: prd @ postgres:5432

📡 Menghubungkan ke database...
✓ Koneksi berhasil!

🔍 Memproses 12 tabel...

📋 Tabel: users
  ✓ Menghapus 5 baris duplikat (tersisa 5 baris unik)

================================================================================
RINGKASAN
================================================================================
Total baris duplikat yang dihapus: 5
Waktu selesai: 2025-12-19 15:20:01
================================================================================

✅ Proses penghapusan duplikat selesai!
```

## 🐛 Troubleshooting

### Error: "connection to server at localhost failed"
**Solusi**: Pastikan Anda menjalankan script di dalam Docker container:
```bash
docker exec prd_backend python3 remove_duplicates_final.py
```

### Error: "ModuleNotFoundError: No module named 'psycopg2'"
**Solusi**: Jalankan di dalam container backend yang sudah memiliki dependencies:
```bash
docker exec prd_backend python3 remove_duplicates_final.py
```

### Script menghapus semua data
**Solusi**: Gunakan `remove_duplicates_final.py`, BUKAN `remove_duplicates.py` (yang lama memiliki bug)

## 🔄 Restore Data Jika Terjadi Kesalahan

Jika data terhapus secara tidak sengaja:

```bash
# 1. Truncate semua tabel
docker exec prd_postgres psql -U postgres -d prd -c "
  TRUNCATE TABLE audit_log, chat_history, domain_notes, feedback, 
  generated_domains, generator_settings, history_log, object_detection, 
  reasoning, results, users, announcements RESTART IDENTITY CASCADE
"

# 2. Restore dari init-data.sql
cat database/init-data.sql | docker exec -i prd_postgres psql -U postgres -d prd

# 3. Atau restore dari backup
cat backup_YYYYMMDD_HHMMSS.sql | docker exec -i prd_postgres psql -U postgres -d prd
```

## 📚 Referensi

- PostgreSQL DISTINCT ON: https://www.postgresql.org/docs/current/sql-select.html#SQL-DISTINCT
- psycopg2 Documentation: https://www.psycopg.org/docs/

## ✅ Checklist Sebelum Menghapus Duplikat

- [ ] Backup database sudah dibuat
- [ ] Sudah menjalankan mode check untuk melihat duplikat
- [ ] Memahami data mana yang akan dihapus
- [ ] Aplikasi dalam status maintenance (opsional, tapi disarankan)
- [ ] Siap untuk restore jika terjadi masalah

## 👤 Kontak

Jika ada pertanyaan atau masalah, hubungi tim development.

---
**Last Updated**: 2025-12-19
**Version**: 1.0.0 (Final)

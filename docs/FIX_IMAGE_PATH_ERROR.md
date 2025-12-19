# Fix: Domain Generator Insert Error

## 🐛 Masalah

Domain generator gagal menyimpan hasil ke database dengan error:

```
psycopg2.errors.StringDataRightTruncation: value too long for type character varying(512)
```

## 🔍 Root Cause

Kolom `image_final_path` di tabel `results` memiliki tipe data `VARCHAR(512)`, yang terlalu kecil untuk menyimpan base64-encoded images. Base64 images dari crawler bisa mencapai 50,000+ karakter.

## ✅ Solusi

Mengubah tipe data kolom `image_final_path` dari `VARCHAR(512)` menjadi `TEXT` (unlimited):

```sql
ALTER TABLE results ALTER COLUMN image_final_path TYPE TEXT;
```

## 📝 Perubahan yang Dilakukan

1. **Database Schema** (`/home/ubuntu/web-app/database/init-schema.sql`):
   - Line 382: `character varying(512)` → `text`

2. **Migration Script** (`/home/ubuntu/web-app/database/migrations/002_fix_image_final_path_size.sql`):
   - Dibuat migration script untuk dokumentasi

3. **Database Live**:
   - Sudah di-apply langsung ke database production

## 🧪 Verifikasi

```bash
# Cek tipe data kolom
docker exec prd_postgres psql -U postgres -d prd -c "\d results" | grep image_final_path

# Output seharusnya:
# image_final_path | text | | |
```

## 📊 Impact

- **Sebelum**: Domain generator gagal insert jika image > 512 karakter
- **Sesudah**: Domain generator bisa insert image dengan ukuran berapa pun

## ⚠️ Catatan

Fix ini **TIDAK** terkait dengan masalah duplikasi data. Ini adalah bug terpisah yang sudah ada sebelumnya di schema database.

---
**Fixed**: 2025-12-19  
**By**: Antigravity AI

# 🌐 Panduan Akses Publik - Dashboard Chatbot

## 📋 Status Sistem

Sistem Anda sudah berjalan dengan konfigurasi berikut:

- **IP Publik Server**: `13.215.203.144`
- **Port HTTP**: 80 (sudah terbuka)
- **Port HTTPS**: 443 (sudah terbuka)
- **Nginx**: Berjalan sebagai reverse proxy
- **Backend API**: Port 8000 (internal)
- **Frontend**: Port 3000 (internal)
- **Database**: Port 5432 (internal)

## ✅ Sistem Sudah Siap!

Berdasarkan konfigurasi Docker yang sudah berjalan, sistem Anda **sudah siap diakses secara publik** melalui:

### URL Akses Utama
```
http://13.215.203.144
```

### URL API Backend
```
http://13.215.203.144/api/
```

## 🔧 Langkah-Langkah Verifikasi

### 1. Cek Status Container
```bash
docker ps
```

Pastikan semua container dalam status "Up" dan "healthy":
- ✅ prd_nginx
- ✅ prd_frontend
- ✅ prd_backend
- ✅ prd_postgres

### 2. Test Akses Lokal
```bash
# Test Nginx
curl http://localhost/health

# Test Frontend
curl http://localhost

# Test Backend API
curl http://localhost/api/
```

### 3. Test Akses dari Internet
Buka browser dan akses:
- Frontend: `http://13.215.203.144`
- API Health: `http://13.215.203.144/health`
- API Docs: `http://13.215.203.144/api/docs`

## 🔒 Konfigurasi Firewall (PENTING!)

Untuk memastikan sistem dapat diakses dari internet, pastikan firewall server Anda mengizinkan traffic berikut:

### Untuk Ubuntu/Debian (UFW)
```bash
# Cek status firewall
sudo ufw status

# Jika firewall aktif, izinkan port yang diperlukan
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS (untuk masa depan)
sudo ufw allow 22/tcp    # SSH (jangan lupa!)

# Reload firewall
sudo ufw reload
```

### Untuk AWS EC2
Jika server Anda di AWS, konfigurasikan Security Group:

1. Buka AWS Console → EC2 → Security Groups
2. Pilih Security Group yang terkait dengan instance Anda
3. Tambahkan Inbound Rules:
   - **Type**: HTTP, **Port**: 80, **Source**: 0.0.0.0/0
   - **Type**: HTTPS, **Port**: 443, **Source**: 0.0.0.0/0
   - **Type**: SSH, **Port**: 22, **Source**: IP Anda (untuk keamanan)

### Untuk Google Cloud Platform (GCP)
```bash
# Izinkan HTTP traffic
gcloud compute firewall-rules create allow-http \
    --allow tcp:80 \
    --source-ranges 0.0.0.0/0 \
    --description "Allow HTTP traffic"

# Izinkan HTTPS traffic
gcloud compute firewall-rules create allow-https \
    --allow tcp:443 \
    --source-ranges 0.0.0.0/0 \
    --description "Allow HTTPS traffic"
```

### Untuk DigitalOcean
1. Buka DigitalOcean Console → Networking → Firewalls
2. Buat firewall rule baru atau edit yang ada
3. Tambahkan Inbound Rules untuk port 80 dan 443

## 🌐 Menggunakan Domain Name (Opsional)

Jika Anda ingin menggunakan domain name (misalnya: `dashboard.example.com`):

### 1. Konfigurasi DNS
Tambahkan A Record di DNS provider Anda:
```
Type: A
Name: @ atau dashboard
Value: 13.215.203.144
TTL: 3600
```

### 2. Update Nginx Configuration
Edit file `nginx.docker.conf`:
```nginx
server {
    listen 80;
    listen [::]:80;
    server_name dashboard.example.com;  # Ganti dengan domain Anda
    
    # ... konfigurasi lainnya tetap sama
}
```

### 3. Restart Nginx
```bash
docker restart prd_nginx
```

## 🔐 Mengaktifkan HTTPS dengan SSL/TLS (Sangat Direkomendasikan!)

Untuk keamanan yang lebih baik, gunakan HTTPS dengan Let's Encrypt:

### 1. Install Certbot
```bash
sudo apt update
sudo apt install certbot python3-certbot-nginx -y
```

### 2. Dapatkan SSL Certificate
```bash
# Jika menggunakan domain
sudo certbot --nginx -d dashboard.example.com

# Atau untuk IP (tidak direkomendasikan, gunakan domain)
# SSL certificate tidak bisa diissue untuk IP address
```

### 3. Auto-renewal
```bash
# Test auto-renewal
sudo certbot renew --dry-run

# Certbot akan otomatis setup cron job untuk renewal
```

## 📊 Monitoring dan Logging

### Lihat Logs Container
```bash
# Semua logs
docker-compose logs -f

# Logs spesifik
docker logs -f prd_nginx
docker logs -f prd_frontend
docker logs -f prd_backend
docker logs -f prd_postgres
```

### Monitor Resource Usage
```bash
# CPU dan Memory usage
docker stats

# Disk usage
docker system df
```

## 🛡️ Rekomendasi Keamanan

### 1. Batasi Akses Database
Database PostgreSQL sebaiknya **TIDAK** diexpose ke publik. Konfigurasi saat ini sudah benar:
- Port 5432 hanya accessible dari dalam Docker network
- Gunakan strong password untuk production

### 2. Environment Variables
Pastikan file `.env.docker` berisi kredensial yang aman:
```bash
# Edit .env.docker
nano .env.docker

# Ganti dengan password yang kuat
POSTGRES_PASSWORD=<password-yang-kuat>
```

### 3. Rate Limiting (Opsional)
Tambahkan rate limiting di Nginx untuk mencegah abuse:
```nginx
http {
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;
    
    server {
        location /api/ {
            limit_req zone=api_limit burst=20 nodelay;
            # ... konfigurasi lainnya
        }
    }
}
```

### 4. Backup Reguler
```bash
# Backup database
docker exec prd_postgres pg_dump -U postgres prd > backup_$(date +%Y%m%d).sql

# Backup dengan cron job (setiap hari jam 2 pagi)
# Tambahkan ke crontab: crontab -e
0 2 * * * cd /home/ubuntu/prototype-dashboard-chatbot && docker exec prd_postgres pg_dump -U postgres prd > backup_$(date +\%Y\%m\%d).sql
```

## 🚀 Quick Commands

```bash
# Start semua services
docker-compose up -d

# Stop semua services
docker-compose down

# Restart service tertentu
docker restart prd_nginx
docker restart prd_frontend
docker restart prd_backend

# Rebuild dan restart
docker-compose up -d --build

# Lihat status
docker-compose ps
```

## 🔍 Troubleshooting

### Tidak bisa diakses dari internet?
1. ✅ Cek firewall server (ufw, iptables)
2. ✅ Cek Security Group (jika di cloud)
3. ✅ Cek status container: `docker ps`
4. ✅ Cek logs: `docker logs prd_nginx`
5. ✅ Test dari server: `curl http://localhost`

### Error 502 Bad Gateway?
1. Cek backend container: `docker logs prd_backend`
2. Cek frontend container: `docker logs prd_frontend`
3. Restart services: `docker-compose restart`

### Database connection error?
1. Cek postgres container: `docker logs prd_postgres`
2. Verifikasi credentials di `.env.docker`
3. Cek health status: `docker ps` (lihat kolom STATUS)

## 📞 Support

Jika mengalami masalah, cek:
1. Container logs: `docker-compose logs -f`
2. Nginx error log: `docker exec prd_nginx cat /var/log/nginx/error.log`
3. System resources: `docker stats`

---

**Selamat! Sistem Anda sudah siap diakses secara publik! 🎉**

Akses aplikasi Anda di: **http://13.215.203.144**

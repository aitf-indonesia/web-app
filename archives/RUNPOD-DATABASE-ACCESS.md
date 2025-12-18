# 🔌 Panduan Akses Database dari RunPod

## 📋 Situasi Saat Ini

- **Database**: PostgreSQL 14 di Docker
- **Port**: 5432 (sudah exposed ke 0.0.0.0:5432)
- **Server IP**: 13.215.203.144
- **Database Name**: prd
- **Username**: postgres
- **Password**: postgres

## 🎯 Solusi-Solusi yang Tersedia

### ✅ Solusi 1: Akses Langsung via Port 5432 (Paling Sederhana)

Database Anda **sudah exposed** di port 5432, jadi bisa langsung diakses dari RunPod!

#### Connection String dari RunPod:
```
postgresql://postgres:postgres@13.215.203.144:5432/prd
```

#### Langkah-langkah:

1. **Pastikan Firewall Mengizinkan Port 5432**
   ```bash
   # Di server database Anda (13.215.203.144)
   sudo ufw allow 5432/tcp
   sudo ufw reload
   ```

2. **Jika menggunakan Cloud Provider (AWS/GCP/Azure)**
   - Tambahkan Inbound Rule di Security Group
   - **Type**: Custom TCP
   - **Port**: 5432
   - **Source**: IP RunPod Anda (lebih aman) atau 0.0.0.0/0 (semua IP)

3. **Test Koneksi dari RunPod**
   ```bash
   # Install PostgreSQL client di RunPod
   apt-get update && apt-get install -y postgresql-client
   
   # Test koneksi
   psql postgresql://postgres:postgres@13.215.203.144:5432/prd -c "SELECT version();"
   ```

4. **Gunakan di Aplikasi RunPod**
   ```python
   # Python example
   import psycopg2
   
   conn = psycopg2.connect(
       host="13.215.203.144",
       port=5432,
       database="prd",
       user="postgres",
       password="postgres"
   )
   ```

#### ⚠️ Keamanan:
- **TIDAK AMAN** jika dibuka ke 0.0.0.0/0
- **Lebih Aman**: Whitelist hanya IP RunPod
- **Paling Aman**: Gunakan Solusi 2 atau 3

---

### 🔒 Solusi 2: SSH Tunnel (Paling Aman & Direkomendasikan)

Akses database melalui SSH tunnel tanpa expose port 5432 ke publik.

#### Cara Kerja:
RunPod → SSH Tunnel → Server Database → PostgreSQL

#### Langkah-langkah:

1. **Setup SSH Key di Server Database**
   ```bash
   # Di server database (13.215.203.144)
   # Pastikan SSH sudah berjalan
   sudo systemctl status ssh
   
   # Buat user khusus untuk RunPod (opsional, lebih aman)
   sudo adduser runpod-access
   sudo usermod -aG docker runpod-access
   ```

2. **Generate SSH Key di RunPod**
   ```bash
   # Di RunPod
   ssh-keygen -t ed25519 -C "runpod-access"
   
   # Copy public key
   cat ~/.ssh/id_ed25519.pub
   ```

3. **Tambahkan Public Key ke Server Database**
   ```bash
   # Di server database
   # Tambahkan ke authorized_keys
   echo "PASTE_PUBLIC_KEY_HERE" >> ~/.ssh/authorized_keys
   # atau untuk user runpod-access:
   # echo "PASTE_PUBLIC_KEY_HERE" >> /home/runpod-access/.ssh/authorized_keys
   ```

4. **Buat SSH Tunnel dari RunPod**
   ```bash
   # Di RunPod - Forward port lokal 5432 ke remote 5432
   ssh -L 5432:localhost:5432 ubuntu@13.215.203.144 -N -f
   
   # Atau dengan user khusus
   ssh -L 5432:localhost:5432 runpod-access@13.215.203.144 -N -f
   ```

5. **Koneksi ke Database via Tunnel**
   ```python
   # Di RunPod - koneksi ke localhost karena sudah di-tunnel
   import psycopg2
   
   conn = psycopg2.connect(
       host="localhost",  # Bukan 13.215.203.144!
       port=5432,
       database="prd",
       user="postgres",
       password="postgres"
   )
   ```

#### Script Otomatis untuk RunPod:
```bash
#!/bin/bash
# save as: setup-db-tunnel.sh

# Setup SSH tunnel
ssh -o StrictHostKeyChecking=no \
    -L 5432:localhost:5432 \
    ubuntu@13.215.203.144 \
    -N -f

# Wait for tunnel
sleep 2

# Test connection
psql postgresql://postgres:postgres@localhost:5432/prd -c "SELECT 1;"

echo "Database tunnel ready!"
```

#### ✅ Keuntungan:
- Port 5432 TIDAK perlu exposed ke internet
- Enkripsi via SSH
- Lebih aman dari serangan brute force

---

### 🌐 Solusi 3: VPN/Tailscale (Untuk Setup Permanen)

Buat private network antara RunPod dan server database.

#### Menggunakan Tailscale (Gratis & Mudah):

1. **Install Tailscale di Server Database**
   ```bash
   # Di server database (13.215.203.144)
   curl -fsSL https://tailscale.com/install.sh | sh
   sudo tailscale up
   ```

2. **Install Tailscale di RunPod**
   ```bash
   # Di RunPod
   curl -fsSL https://tailscale.com/install.sh | sh
   sudo tailscale up
   ```

3. **Dapatkan Tailscale IP**
   ```bash
   # Di server database
   tailscale ip -4
   # Contoh output: 100.64.0.1
   ```

4. **Koneksi dari RunPod**
   ```python
   # Gunakan Tailscale IP
   conn = psycopg2.connect(
       host="100.64.0.1",  # Tailscale IP server database
       port=5432,
       database="prd",
       user="postgres",
       password="postgres"
   )
   ```

#### ✅ Keuntungan:
- Private network yang aman
- Tidak perlu expose port ke internet
- Mudah di-setup dan maintain
- Gratis untuk penggunaan personal

---

### 🔐 Solusi 4: Database Proxy dengan Authentication

Buat API proxy dengan authentication untuk akses database yang lebih terkontrol.

#### Setup FastAPI Proxy:

1. **Buat File `db_proxy.py`**
   ```python
   from fastapi import FastAPI, HTTPException, Depends, Header
   from pydantic import BaseModel
   import psycopg2
   from psycopg2.extras import RealDictCursor
   import os
   
   app = FastAPI()
   
   # Secret token untuk authentication
   PROXY_TOKEN = os.getenv("PROXY_TOKEN", "your-secret-token-here")
   
   def verify_token(x_api_key: str = Header(...)):
       if x_api_key != PROXY_TOKEN:
           raise HTTPException(status_code=401, detail="Invalid API Key")
       return x_api_key
   
   class Query(BaseModel):
       sql: str
       params: dict = {}
   
   @app.post("/query")
   async def execute_query(query: Query, token: str = Depends(verify_token)):
       try:
           conn = psycopg2.connect(
               host="postgres",
               port=5432,
               database="prd",
               user="postgres",
               password="postgres"
           )
           cursor = conn.cursor(cursor_factory=RealDictCursor)
           cursor.execute(query.sql, query.params)
           
           if query.sql.strip().upper().startswith("SELECT"):
               result = cursor.fetchall()
           else:
               conn.commit()
               result = {"affected_rows": cursor.rowcount}
           
           cursor.close()
           conn.close()
           return {"success": True, "data": result}
       except Exception as e:
           raise HTTPException(status_code=500, detail=str(e))
   
   @app.get("/health")
   async def health():
       return {"status": "ok"}
   ```

2. **Deploy di Docker**
   ```dockerfile
   # Tambahkan ke docker-compose.yml
   db_proxy:
     build:
       context: ./db_proxy
       dockerfile: Dockerfile
     container_name: prd_db_proxy
     restart: unless-stopped
     environment:
       - PROXY_TOKEN=your-super-secret-token
     ports:
       - "8001:8000"
     networks:
       - prd_network
     depends_on:
       - postgres
   ```

3. **Akses dari RunPod**
   ```python
   import requests
   
   headers = {"X-API-Key": "your-super-secret-token"}
   
   response = requests.post(
       "http://13.215.203.144:8001/query",
       json={
           "sql": "SELECT * FROM users LIMIT 10",
           "params": {}
       },
       headers=headers
   )
   
   data = response.json()
   print(data)
   ```

#### ✅ Keuntungan:
- Kontrol akses dengan API key
- Bisa tambahkan rate limiting
- Logging semua query
- Tidak expose PostgreSQL langsung

---

### 📊 Solusi 5: Read Replica (Untuk Production)

Buat read-only replica database khusus untuk RunPod.

#### Setup PostgreSQL Replication:

1. **Konfigurasi Master (Server Database)**
   ```bash
   # Edit postgresql.conf
   docker exec -it prd_postgres bash
   
   # Tambahkan konfigurasi replication
   # wal_level = replica
   # max_wal_senders = 3
   # max_replication_slots = 3
   ```

2. **Buat Replication User**
   ```sql
   CREATE USER replicator WITH REPLICATION ENCRYPTED PASSWORD 'repl_password';
   ```

3. **Setup Replica di RunPod**
   ```bash
   # Di RunPod, jalankan PostgreSQL sebagai replica
   docker run -d \
     --name postgres_replica \
     -e POSTGRES_PASSWORD=postgres \
     -p 5432:5432 \
     postgres:14-alpine
   
   # Setup replication
   pg_basebackup -h 13.215.203.144 -D /var/lib/postgresql/data -U replicator -v -P
   ```

#### ✅ Keuntungan:
- Data lokal di RunPod (lebih cepat)
- Tidak membebani database utama
- Read-only untuk keamanan

---

## 🎯 Rekomendasi Berdasarkan Use Case

### Untuk Development/Testing:
✅ **Solusi 1** (Akses Langsung) - Paling mudah dan cepat

### Untuk Production:
✅ **Solusi 2** (SSH Tunnel) - Paling aman tanpa setup kompleks
✅ **Solusi 3** (Tailscale VPN) - Untuk koneksi permanen yang aman

### Untuk API/Microservices:
✅ **Solusi 4** (Database Proxy) - Kontrol akses terbaik

### Untuk Analytics/ML Workload:
✅ **Solusi 5** (Read Replica) - Performance terbaik

---

## 🔒 Checklist Keamanan

Apapun solusi yang dipilih, pastikan:

- [ ] Gunakan password yang kuat (ganti default "postgres")
- [ ] Whitelist IP RunPod di firewall (jangan 0.0.0.0/0)
- [ ] Enable SSL/TLS untuk koneksi database
- [ ] Monitoring akses database (log connections)
- [ ] Regular backup database
- [ ] Gunakan environment variables untuk credentials

---

## 🚀 Quick Start - Solusi Tercepat

Jika Anda ingin **langsung coba sekarang**:

```bash
# 1. Di server database - izinkan port 5432
sudo ufw allow from RUNPOD_IP to any port 5432

# 2. Di RunPod - test koneksi
psql postgresql://postgres:postgres@13.215.203.144:5432/prd -c "SELECT version();"

# 3. Jika berhasil, gunakan connection string di aplikasi
# postgresql://postgres:postgres@13.215.203.144:5432/prd
```

**Ganti `RUNPOD_IP`** dengan IP address RunPod Anda untuk keamanan!

---

## 📞 Troubleshooting

### Koneksi Timeout?
- Cek firewall: `sudo ufw status`
- Cek Security Group di cloud provider
- Test port: `telnet 13.215.203.144 5432`

### Authentication Failed?
- Verifikasi username/password
- Cek `pg_hba.conf` di PostgreSQL

### Connection Refused?
- Pastikan PostgreSQL listening di 0.0.0.0
- Cek Docker port mapping: `docker ps`

---

**Pilih solusi yang sesuai dengan kebutuhan Anda!** 🎯

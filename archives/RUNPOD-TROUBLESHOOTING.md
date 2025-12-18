# 🔧 Troubleshooting: RunPod Tidak Bisa Ping Server Database

## ❓ Masalah

```bash
ubuntu@351d2e681af3:~/tim6_prd_workdir3$ ping 13.215.203.144
PING 13.215.203.144 (13.215.203.144) 56(84) bytes of data.
# Tidak ada response...
```

## ✅ **PING GAGAL ITU NORMAL!** 

**Ini BUKAN masalah!** Berikut alasannya:

### Mengapa Ping Tidak Berfungsi?

1. **ICMP Blocked** - Banyak cloud provider (termasuk AWS) memblokir ICMP traffic secara default
2. **Firewall** - Server Anda mungkin tidak mengizinkan ICMP packets
3. **Security Group** - AWS Security Group biasanya tidak allow ICMP by default

### Yang Penting: **Koneksi TCP Berfungsi!**

Ping menggunakan **ICMP protocol**, sedangkan database menggunakan **TCP protocol**.
Jadi meskipun ping gagal, **koneksi database tetap bisa berfungsi!**

---

## 🎯 Solusi: Test Koneksi yang Benar

### 1. Test Port 5432 (PostgreSQL) - Cara Terbaik

Gunakan `telnet` atau `nc` untuk test koneksi TCP:

```bash
# Di RunPod - Test apakah port 5432 terbuka
nc -zv 13.215.203.144 5432

# Atau dengan telnet
telnet 13.215.203.144 5432

# Atau dengan timeout
timeout 5 bash -c 'cat < /dev/null > /dev/tcp/13.215.203.144/5432' && echo "Port 5432 is open" || echo "Port 5432 is closed"
```

**Expected Output (Jika Berhasil):**
```
Connection to 13.215.203.144 5432 port [tcp/postgresql] succeeded!
```

### 2. Test dengan PostgreSQL Client

Cara paling akurat adalah langsung test koneksi database:

```bash
# Di RunPod - Install PostgreSQL client jika belum ada
apt-get update && apt-get install -y postgresql-client

# Test koneksi database
psql postgresql://postgres:postgres@13.215.203.144:5432/prd -c "SELECT version();"
```

**Expected Output (Jika Berhasil):**
```
                                         version                                          
------------------------------------------------------------------------------------------
 PostgreSQL 14.20 on x86_64-pc-linux-musl, compiled by gcc (Alpine 15.2.0) 15.2.0, 64-bit
(1 row)
```

### 3. Test dengan Python

```python
# Di RunPod - Test dengan Python
import psycopg2

try:
    conn = psycopg2.connect(
        host="13.215.203.144",
        port=5432,
        database="prd",
        user="postgres",
        password="postgres",
        connect_timeout=5
    )
    print("✅ Database connection successful!")
    
    cursor = conn.cursor()
    cursor.execute("SELECT version();")
    version = cursor.fetchone()
    print(f"PostgreSQL version: {version[0]}")
    
    cursor.close()
    conn.close()
except Exception as e:
    print(f"❌ Connection failed: {e}")
```

### 4. Test dengan cURL (HTTP)

Test apakah server web bisa diakses:

```bash
# Di RunPod - Test HTTP
curl -I http://13.215.203.144/health

# Test API
curl http://13.215.203.144/api/
```

---

## 🔍 Diagnosis Masalah Koneksi

### Jika Port 5432 Tidak Terbuka:

#### A. Cek Firewall di Server Database

```bash
# Di server database (13.215.203.144)
sudo ufw status verbose

# Pastikan ada rule untuk IP RunPod
# To                         Action      From
# --                         ------      ----
# 5432                       ALLOW       216.81.245.71
```

**Jika belum ada, tambahkan:**
```bash
sudo ufw allow from 216.81.245.71 to any port 5432
```

#### B. Cek Security Group (Jika di AWS)

1. Login ke AWS Console
2. EC2 → Instances → Pilih instance Anda
3. Tab "Security" → Klik Security Group
4. Tab "Inbound rules" → Edit inbound rules
5. Tambahkan rule:
   - **Type**: Custom TCP
   - **Port**: 5432
   - **Source**: 216.81.245.71/32 (IP RunPod)
   - **Description**: RunPod database access

#### C. Cek Docker Port Binding

```bash
# Di server database
docker ps | grep postgres

# Pastikan ada: 0.0.0.0:5432->5432/tcp
```

**Jika tidak ada, edit docker-compose.yml:**
```yaml
postgres:
  ports:
    - "0.0.0.0:5432:5432"  # Pastikan bind ke 0.0.0.0
```

Lalu restart:
```bash
docker-compose restart postgres
```

#### D. Cek PostgreSQL Configuration

```bash
# Di server database
docker exec prd_postgres cat /var/lib/postgresql/data/postgresql.conf | grep listen_addresses

# Pastikan: listen_addresses = '*'
```

---

## 🚀 Quick Fix Script untuk RunPod

Simpan script ini di RunPod untuk test koneksi:

```bash
#!/bin/bash
# File: test-db-connection.sh

DB_HOST="13.215.203.144"
DB_PORT="5432"
DB_NAME="prd"
DB_USER="postgres"
DB_PASS="postgres"

echo "🔍 Testing connection to database server..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Test 1: Port connectivity
echo ""
echo "1️⃣ Testing port $DB_PORT..."
if timeout 5 bash -c "cat < /dev/null > /dev/tcp/$DB_HOST/$DB_PORT" 2>/dev/null; then
    echo "   ✅ Port $DB_PORT is OPEN"
else
    echo "   ❌ Port $DB_PORT is CLOSED or FILTERED"
    echo "   → Check firewall and Security Group settings"
    exit 1
fi

# Test 2: PostgreSQL connection
echo ""
echo "2️⃣ Testing PostgreSQL connection..."
if command -v psql &> /dev/null; then
    if psql "postgresql://$DB_USER:$DB_PASS@$DB_HOST:$DB_PORT/$DB_NAME" -c "SELECT 1;" &> /dev/null; then
        echo "   ✅ PostgreSQL connection SUCCESSFUL"
        
        # Get version
        VERSION=$(psql "postgresql://$DB_USER:$DB_PASS@$DB_HOST:$DB_PORT/$DB_NAME" -t -c "SELECT version();" 2>/dev/null)
        echo "   📊 $VERSION"
    else
        echo "   ❌ PostgreSQL connection FAILED"
        echo "   → Check credentials and database name"
        exit 1
    fi
else
    echo "   ⚠️  psql not installed, skipping PostgreSQL test"
    echo "   → Install with: apt-get install -y postgresql-client"
fi

# Test 3: HTTP endpoint
echo ""
echo "3️⃣ Testing HTTP endpoint..."
if curl -s -o /dev/null -w "%{http_code}" http://$DB_HOST/health | grep -q "200"; then
    echo "   ✅ HTTP endpoint is ACCESSIBLE"
else
    echo "   ⚠️  HTTP endpoint check failed (this is OK if only database access is needed)"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ All tests completed!"
echo ""
echo "Connection string for your application:"
echo "postgresql://$DB_USER:$DB_PASS@$DB_HOST:$DB_PORT/$DB_NAME"
```

**Cara pakai:**
```bash
# Di RunPod
chmod +x test-db-connection.sh
./test-db-connection.sh
```

---

## 🔒 Jika Ingin Mengaktifkan Ping (Opsional)

Jika Anda **benar-benar** ingin ping berfungsi:

### Di Server Database:

```bash
# Allow ICMP (ping) dari IP RunPod
sudo ufw allow from 216.81.245.71 to any proto icmp
```

### Di AWS Security Group:

Tambahkan Inbound Rule:
- **Type**: Custom ICMP - IPv4
- **Protocol**: Echo Request
- **Source**: 216.81.245.71/32

**CATATAN:** Ini opsional dan tidak diperlukan untuk koneksi database!

---

## 📊 Status Saat Ini

Berdasarkan konfigurasi Anda:

- ✅ **SSH Key**: Sudah ditambahkan
- ✅ **Firewall Rule**: Port 5432 sudah diizinkan untuk IP 216.81.245.71
- ✅ **Docker**: PostgreSQL berjalan di port 5432
- ✅ **Database**: Berfungsi normal (tested)
- ⚠️ **UFW Status**: Inactive (firewall tidak aktif)

**Karena UFW inactive, sebenarnya rule firewall tidak berpengaruh.**

### Kemungkinan Masalah:

1. **Security Group di AWS** - Ini yang paling mungkin memblokir
2. **Network ACL** - Jika menggunakan custom VPC
3. **RunPod Network** - RunPod mungkin memblokir outbound ke port tertentu

---

## 🎯 Langkah Selanjutnya

### Coba test koneksi dari RunPod:

```bash
# 1. Test port dengan nc
nc -zv 13.215.203.144 5432

# 2. Jika port terbuka, test database
psql postgresql://postgres:postgres@13.215.203.144:5432/prd -c "SELECT 1;"
```

### Jika masih gagal:

1. **Cek Security Group di AWS** (ini yang paling sering jadi masalah)
2. **Cek apakah RunPod memblokir outbound** ke port 5432
3. **Gunakan SSH Tunnel** sebagai alternatif (lebih aman):

```bash
# Di RunPod - buat SSH tunnel
ssh -L 5432:localhost:5432 ubuntu@13.215.203.144 -N -f

# Lalu koneksi ke localhost
psql postgresql://postgres:postgres@localhost:5432/prd
```

---

## 💡 Kesimpulan

**PING GAGAL ≠ KONEKSI DATABASE GAGAL**

- Ping menggunakan ICMP (layer 3)
- Database menggunakan TCP (layer 4)
- Keduanya berbeda dan independen

**Yang penting**: Test koneksi TCP ke port 5432, bukan ping!

Silakan coba test koneksi dengan cara di atas dan beri tahu hasilnya! 🚀

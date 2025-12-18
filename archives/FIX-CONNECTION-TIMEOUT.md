# 🔥 URGENT: Fix Connection Timeout ke PostgreSQL dari RunPod

## ❌ Masalah Teridentifikasi

```bash
nc: connect to 13.215.203.144 port 5432 (tcp) failed: Connection timed out
```

**Root Cause:** AWS Security Group memblokir port 5432 dari internet.

---

## ✅ SOLUSI: Konfigurasi AWS Security Group

### **Langkah 1: Login ke AWS Console**

1. Buka https://console.aws.amazon.com/ec2/
2. Login dengan akun AWS Anda

### **Langkah 2: Temukan Instance Anda**

1. Di sidebar kiri, klik **"Instances"**
2. Cari instance dengan IP `13.215.203.144`
3. Klik pada instance tersebut

### **Langkah 3: Edit Security Group**

1. Scroll ke tab **"Security"** (di bagian bawah detail instance)
2. Klik pada **Security Group** name (biasanya seperti `sg-xxxxx`)
3. Klik tab **"Inbound rules"**
4. Klik tombol **"Edit inbound rules"**

### **Langkah 4: Tambahkan Rule untuk PostgreSQL**

Klik **"Add rule"** dan isi:

| Field | Value |
|-------|-------|
| **Type** | Custom TCP |
| **Protocol** | TCP |
| **Port range** | 5432 |
| **Source** | Custom: `216.81.245.71/32` |
| **Description** | RunPod database access |

**ATAU** jika IP RunPod berubah-ubah, gunakan:

| Field | Value |
|-------|-------|
| **Source** | Anywhere IPv4: `0.0.0.0/0` |
| **Description** | PostgreSQL public access (TEMPORARY) |

⚠️ **WARNING:** `0.0.0.0/0` membuka akses dari semua IP. Gunakan hanya untuk testing, lalu ganti dengan IP spesifik!

### **Langkah 5: Save Changes**

1. Klik **"Save rules"**
2. Tunggu beberapa detik untuk propagasi

---

## 🎯 SOLUSI ALTERNATIF: SSH Tunnel (Lebih Aman)

Jika Anda tidak bisa/tidak mau membuka port 5432 ke internet, gunakan SSH tunnel:

### **Setup di RunPod:**

```bash
# 1. Test SSH connection dulu
ssh ubuntu@13.215.203.144 -o ConnectTimeout=5

# 2. Jika SSH berhasil, buat tunnel
ssh -L 5432:localhost:5432 ubuntu@13.215.203.144 -N -f

# 3. Test koneksi via tunnel (ke localhost, bukan IP publik!)
nc -zv localhost 5432

# 4. Koneksi database via tunnel
psql postgresql://postgres:postgres@localhost:5432/prd -c "SELECT version();"
```

### **Connection String untuk Aplikasi di RunPod:**

```python
# Jika menggunakan SSH tunnel
DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/prd"

# Jika direct access (setelah Security Group dikonfigurasi)
DATABASE_URL = "postgresql://postgres:postgres@13.215.203.144:5432/prd"
```

---

## 🔍 Verifikasi Setelah Konfigurasi

### **Test dari RunPod:**

```bash
# Test 1: Port connectivity
nc -zv 13.215.203.144 5432

# Expected output:
# Connection to 13.215.203.144 5432 port [tcp/postgresql] succeeded!

# Test 2: Database connection
psql postgresql://postgres:postgres@13.215.203.144:5432/prd -c "SELECT version();"

# Expected output:
# PostgreSQL 14.20 on x86_64-pc-linux-musl...
```

---

## 📋 Checklist Troubleshooting

Jika masih gagal setelah edit Security Group:

- [ ] **Tunggu 30-60 detik** untuk propagasi Security Group
- [ ] **Cek Security Group yang benar** - Instance bisa punya multiple SG
- [ ] **Cek Network ACL** - Di VPC → Network ACLs
- [ ] **Cek IP RunPod** - Pastikan IP yang di-whitelist benar
- [ ] **Test dari IP lain** - Coba dari komputer lokal Anda

### **Cara Cek IP RunPod yang Benar:**

```bash
# Di RunPod
curl -s ifconfig.me
# atau
curl -s icanhazip.com
# atau
curl -s api.ipify.org
```

Pastikan IP yang muncul adalah `216.81.245.71` atau update Security Group dengan IP yang benar.

---

## 🎬 Video Tutorial (Jika Perlu)

### **Cara Edit Security Group di AWS:**

1. **Via AWS Console (Web):**
   - EC2 Dashboard → Instances → Select Instance
   - Security tab → Click Security Group
   - Inbound rules → Edit inbound rules
   - Add rule → Save

2. **Via AWS CLI:**
   ```bash
   # Get Security Group ID
   aws ec2 describe-instances \
     --filters "Name=ip-address,Values=13.215.203.144" \
     --query 'Reservations[0].Instances[0].SecurityGroups[0].GroupId' \
     --output text

   # Add rule (ganti sg-xxxxx dengan SG ID Anda)
   aws ec2 authorize-security-group-ingress \
     --group-id sg-xxxxx \
     --protocol tcp \
     --port 5432 \
     --cidr 216.81.245.71/32
   ```

---

## 🔒 Rekomendasi Keamanan

### **Untuk Production:**

1. ✅ **Gunakan SSH Tunnel** - Paling aman
2. ✅ **Whitelist IP Spesifik** - Hanya IP RunPod
3. ✅ **Ganti Password Default** - Jangan pakai "postgres"
4. ✅ **Enable SSL/TLS** - Enkripsi koneksi database
5. ✅ **Setup VPN** - Tailscale atau WireGuard

### **JANGAN di Production:**

1. ❌ **Jangan buka 0.0.0.0/0** untuk port 5432
2. ❌ **Jangan pakai password lemah**
3. ❌ **Jangan expose tanpa monitoring**

---

## 🚀 Quick Fix (Untuk Testing Cepat)

Jika Anda hanya ingin test cepat dan tidak peduli keamanan sementara:

### **Di AWS Console:**

```
Security Group → Inbound Rules → Add Rule:
Type: PostgreSQL
Port: 5432
Source: 0.0.0.0/0
Description: TEMPORARY - Testing only
```

**INGAT:** Hapus rule ini setelah testing selesai!

---

## 📞 Next Steps

1. **Edit Security Group di AWS** (5 menit)
2. **Test koneksi dari RunPod** (1 menit)
3. **Jika berhasil, ganti 0.0.0.0/0 dengan IP spesifik** (untuk keamanan)

Atau:

1. **Setup SSH Tunnel** (lebih aman, 2 menit)
2. **Koneksi via localhost** (permanent solution)

---

**Pilih salah satu solusi dan beri tahu hasilnya!** 🎯

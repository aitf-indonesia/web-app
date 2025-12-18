# Setup Backend VPS untuk Menerima Log dari RunPod

## 📍 Informasi VPS

- **IP Backend**: `18.140.62.254`
- **Endpoint Log**: `http://18.140.62.254/api/crawler/log`
- **Port**: 80 (HTTP via Nginx) atau 8000 (direct backend)
- **Backend Framework**: FastAPI dengan asyncio

---

## ✅ Status Implementasi

**SUDAH SELESAI!** Backend sudah siap menerima log dari RunPod.

Endpoint yang sudah tersedia:
- ✅ `POST /api/crawler/log` - Menerima log dari RunPod
- ✅ `GET /api/crawler/logs/{job_id}` - Stream logs via SSE
- ✅ `POST /api/crawler/start` - Start job dan dapatkan job_id
- ✅ `POST /api/crawler/cancel/{job_id}` - Cancel job
- ✅ `GET /api/crawler/status/{job_id}` - Check job status

---

## 🎯 Cara Kerja Sistem

### Flow Lengkap:

```
1. Frontend → Backend: POST /api/crawler/start
   Response: { "job_id": "abc-123" }

2. Backend → RunPod: POST https://runpod-url/process
   Body: { "data": "keyword", "num_domains": 5, "job_id": "abc-123" }

3. RunPod → Backend: POST http://18.140.62.254/api/crawler/log
   Body: { "job_id": "abc-123", "message": "[INFO] Progress..." }
   (Bisa dipanggil berkali-kali untuk setiap progress)

4. Frontend → Backend: GET /api/crawler/logs/abc-123 (SSE stream)
   Response: Real-time log stream
```

---

## 📝 Implementasi yang Sudah Ada

### File: `/backend/routes/crawler_routes.py`

Sudah ada class `CrawlerJob` dengan asyncio.Queue:

```python
class CrawlerJob:
    def __init__(self, job_id: str):
        self.job_id = job_id
        self.queue = asyncio.Queue()  # ← Queue untuk streaming
        self.task: Optional[asyncio.Task] = None
        self.returncode: Optional[int] = None
        
    async def log(self, message: str):
        await self.queue.put(f"data: {message}\n\n")
```

Dan endpoint untuk menerima log:

```python
@router.post("/log")
async def receive_log(log_message: LogMessage):
    """
    Receive external log message and push it to the job's log stream.
    """
    job_id = log_message.job_id
    message = log_message.message
    
    if job_id not in active_jobs:
        raise HTTPException(
            status_code=404, 
            detail=f"Job {job_id} not found or already completed"
        )
    
    job = active_jobs[job_id]
    await job.log(message)
    
    return {
        "status": "success",
        "job_id": job_id,
        "message": "Log message received and queued"
    }
```

---

## 🧪 Testing Backend

### Test 1: Endpoint Aktif

```bash
# Test dari VPS sendiri
curl http://localhost:8000/api/crawler/log

# Test dari luar
curl http://18.140.62.254/api/crawler/log
```

**Expected**: Status 422 (validation error) = ✅ Endpoint aktif

### Test 2: Full Flow Test

**Step 1**: Start job dari UI atau API:

```bash
# Login dulu untuk dapat token
TOKEN="your-token-here"

# Start job
curl -X POST http://18.140.62.254/api/crawler/start \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "domain_count": 3,
    "keywords": ["test keyword"]
  }'
```

Response:
```json
{
  "job_id": "abc-123-def-456",
  "status": "started",
  "message": "Crawler started via RunPod with 3 domains"
}
```

**Step 2**: Kirim log ke job tersebut:

```bash
JOB_ID="abc-123-def-456"  # Ganti dengan job_id dari step 1

# Kirim beberapa log
curl -X POST http://18.140.62.254/api/crawler/log \
  -H "Content-Type: application/json" \
  -d "{
    \"job_id\": \"$JOB_ID\",
    \"message\": \"[INFO] Test log 1\"
  }"

curl -X POST http://18.140.62.254/api/crawler/log \
  -H "Content-Type: application/json" \
  -d "{
    \"job_id\": \"$JOB_ID\",
    \"message\": \"[INFO] Test log 2\"
  }"

curl -X POST http://18.140.62.254/api/crawler/log \
  -H "Content-Type: application/json" \
  -d "{
    \"job_id\": \"$JOB_ID\",
    \"message\": \"[SUCCESS] Test completed\"
  }"
```

**Step 3**: Lihat log stream (di terminal lain):

```bash
curl -N http://18.140.62.254/api/crawler/logs/$JOB_ID
```

Output akan streaming real-time:
```
: keepalive

data: [INFO] Test log 1

data: [INFO] Test log 2

data: [SUCCESS] Test completed
```

### Test 3: Gunakan Python Script

```bash
# Jalankan script simulasi
python3 test-runpod-simulation.py
```

Masukkan job_id yang valid, lalu lihat log muncul di UI!

---

## 🔧 Troubleshooting

### Problem: "Job not found or already completed"

**Penyebab**: Job_id tidak valid atau job sudah selesai

**Solusi**:
1. Pastikan job masih running (belum selesai)
2. Start job baru dari UI
3. Gunakan job_id yang baru

**Check job status**:
```bash
curl http://18.140.62.254/api/crawler/status/$JOB_ID
```

### Problem: Connection Refused

**Check service running**:
```bash
docker compose ps backend
```

Expected output:
```
NAME          STATUS
prd_backend   Up X minutes (healthy)
```

**Restart jika perlu**:
```bash
docker compose restart backend
```

### Problem: Firewall Block

**Check firewall**:
```bash
sudo ufw status
```

**Allow port 80**:
```bash
sudo ufw allow 80/tcp
sudo ufw reload
```

### Problem: Log Tidak Muncul di UI

**Kemungkinan**:
1. Job sudah selesai (check status)
2. Frontend belum refresh
3. SSE connection terputus

**Debug**:
```bash
# Check backend logs
docker compose logs -f backend

# Harus muncul:
# [LOG RECEIVED] abc-123: [INFO] Your message
```

---

## 📋 Checklist untuk RunPod Team

### Yang Harus Dilakukan di RunPod:

- [ ] **Terima job_id** dari request body atau header
- [ ] **Simpan job_id** untuk digunakan saat send log
- [ ] **Kirim log** ke: `http://18.140.62.254/api/crawler/log`
- [ ] **Format request**:
  ```json
  {
    "job_id": "uuid-from-request",
    "message": "[INFO] Your log message"
  }
  ```
- [ ] **Kirim log berkala** selama processing (progress updates)
- [ ] **Kirim summary** di akhir dengan format:
  ```json
  {
    "job_id": "...",
    "message": "[SUMMARY] {\"status\": \"success\", ...}"
  }
  ```

### Format Log Messages:

```python
# Progress log
"[INFO] Starting domain generation..."
"[INFO] Progress: 20% - Generated domain 1/5"
"[INFO] Progress: 40% - Generated domain 2/5"

# Success
"[SUCCESS] Domain generation completed!"

# Error
"[ERROR] Failed to generate domain: timeout"

# Summary (PENTING untuk UI)
"[SUMMARY] {\"status\": \"success\", \"domains_generated\": {\"success\": 5, \"total\": 5}, ...}"
```

---

## 🚀 Contoh Implementasi RunPod

### Minimal Implementation:

```python
from fastapi import FastAPI, Request
import httpx
import asyncio

app = FastAPI()

BACKEND_LOG_URL = "http://18.140.62.254/api/crawler/log"

async def send_log(job_id: str, message: str):
    """Send log to backend"""
    if not job_id:
        return
    
    try:
        async with httpx.AsyncClient() as client:
            await client.post(
                BACKEND_LOG_URL,
                json={"job_id": job_id, "message": message},
                timeout=5.0
            )
    except Exception as e:
        print(f"Failed to send log: {e}")

@app.post("/process")
async def process(request: Request):
    body = await request.json()
    keyword = body.get("data", "")
    num_domains = body.get("num_domains", 5)
    job_id = body.get("job_id")  # ← PENTING: ambil job_id
    
    # Send initial log
    await send_log(job_id, f"[INFO] Starting generation for: {keyword}")
    
    # Process...
    domains = []
    for i in range(num_domains):
        domain = f"example-{i}.com"
        domains.append(domain)
        
        # Send progress
        await send_log(job_id, f"[INFO] Progress: {(i+1)*100//num_domains}%")
        await asyncio.sleep(0.5)
    
    # Send completion
    await send_log(job_id, "[SUCCESS] Generation completed!")
    
    return {"status": "success", "domains": domains}
```

---

## 📊 Monitoring

### Check Backend Logs:

```bash
# Real-time logs
docker compose logs -f backend

# Last 100 lines
docker compose logs --tail=100 backend
```

### Check Active Jobs:

```bash
# Via API
curl http://18.140.62.254/api/crawler/status/$JOB_ID
```

### Check Backend Health:

```bash
docker compose ps backend
curl http://18.140.62.254/
```

---

## 🔐 Security (Optional)

### Tambah API Key Authentication:

Edit `/backend/routes/crawler_routes.py`:

```python
from fastapi import Header, HTTPException

API_KEY = "your-secret-key-here"

@router.post("/log")
async def receive_log(
    log_message: LogMessage,
    x_api_key: str = Header(None)
):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")
    
    # ... rest of code
```

Dari RunPod, tambahkan header:
```python
headers = {
    "Content-Type": "application/json",
    "X-API-Key": "your-secret-key-here"
}
```

---

## 📞 Quick Reference

### Endpoints:

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/crawler/start` | Start new job |
| POST | `/api/crawler/log` | Send log (dari RunPod) |
| GET | `/api/crawler/logs/{job_id}` | Stream logs (SSE) |
| GET | `/api/crawler/status/{job_id}` | Check job status |
| POST | `/api/crawler/cancel/{job_id}` | Cancel job |

### Test Commands:

```bash
# Start job (need auth)
curl -X POST http://18.140.62.254/api/crawler/start \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"domain_count": 3, "keywords": ["test"]}'

# Send log (no auth needed)
curl -X POST http://18.140.62.254/api/crawler/log \
  -H "Content-Type: application/json" \
  -d '{"job_id": "abc-123", "message": "[INFO] Test"}'

# Stream logs
curl -N http://18.140.62.254/api/crawler/logs/abc-123

# Check status
curl http://18.140.62.254/api/crawler/status/abc-123
```

---

## ✅ Verification Checklist

- [x] Backend service running (port 8000)
- [x] Nginx proxy running (port 80)
- [x] Endpoint `/api/crawler/log` accessible
- [x] Test dengan job_id valid berhasil
- [x] Log muncul di UI real-time
- [x] Firewall allow port 80
- [ ] RunPod dapat akses endpoint
- [ ] RunPod mengirim job_id dengan benar
- [ ] Full integration test berhasil

---

**Status**: ✅ Backend Ready
**Next**: Implementasi di RunPod side
**Last Updated**: 2025-12-16

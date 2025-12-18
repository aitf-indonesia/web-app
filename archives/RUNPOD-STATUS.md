# RunPod Integration - Current Status

## ⚠️ IMPORTANT UPDATE

**Status**: Backend sekarang menggunakan **LOCAL CRAWLER** (bukan RunPod API)

Perubahan terbaru:
- ✅ Backend menjalankan `crawler.py` secara lokal
- ✅ Log streaming langsung dari subprocess
- ✅ Summary diambil dari output crawler.py
- ❌ RunPod API integration **TIDAK DIGUNAKAN** saat ini

---

## 🔄 Current Architecture

```
Frontend → Backend: POST /api/crawler/start
Backend → Local Process: python crawler.py
Local Process → Backend: stdout streaming
Backend → Frontend: SSE stream via /api/crawler/logs/{job_id}
```

**RunPod TIDAK terlibat dalam flow ini.**

---

## 📝 Jika Ingin Menggunakan RunPod (Future)

Jika nanti ingin kembali menggunakan RunPod, ada 2 opsi:

### Opsi 1: RunPod Sebagai Processor (Recommended)

Backend tetap handle job management, RunPod hanya process:

```python
# Di backend: run_remote_crawler()
async def run_remote_crawler(job, keywords_str, domain_count):
    await job.log("[INFO] Sending to RunPod...")
    
    # Kirim ke RunPod dengan job_id
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://runpod-url/process",
            json={
                "data": keywords_str,
                "num_domains": domain_count,
                "job_id": job.job_id,  # ← Kirim job_id
                "callback_url": "http://18.140.62.254/api/crawler/log"
            }
        )
    
    # RunPod akan kirim log ke callback_url
    # dengan format: {"job_id": "...", "message": "..."}
```

### Opsi 2: RunPod Standalone

RunPod handle semua, backend hanya proxy:

```python
# Backend hanya forward request
@router.post("/start")
async def start_crawler(request: CrawlerRequest):
    # Forward ke RunPod
    response = await httpx.post(
        "https://runpod-url/process",
        json={
            "data": ",".join(request.keywords),
            "num_domains": request.domain_count
        }
    )
    return response.json()
```

---

## 🛠️ Untuk Mengaktifkan RunPod Integration

### Step 1: Uncomment RunPod Code

Di `backend/routes/crawler_routes.py`, ganti `run_local_crawler` dengan `run_remote_crawler`:

```python
# Tambahkan import
import aiohttp

# Tambahkan function
async def run_remote_crawler(job: CrawlerJob, keywords_str: str, domain_count: int):
    try:
        await job.log(f"[INFO] Connecting to RunPod...")
        
        url = "https://l7i1ghaqgdha36-3000.proxy.runpod.net/process"
        payload = {
            "data": keywords_str,
            "num_domains": domain_count,
            "job_id": job.job_id,  # ← PENTING
            "callback_url": "http://18.140.62.254/api/crawler/log"
        }
        
        async with aiohttp.ClientSession() as session:
            timeout = aiohttp.ClientTimeout(total=300)
            async with session.post(url, json=payload, timeout=timeout) as response:
                if response.status != 200:
                    text = await response.text()
                    await job.error(f"RunPod error: {response.status} - {text}")
                    return
                
                data = await response.json()
                # Process response...
                
    except Exception as e:
        await job.error(f"RunPod exception: {str(e)}")
    finally:
        await job.finish()

# Ubah start_crawler
@router.post("/start")
async def start_crawler(request: CrawlerRequest, current_user: dict = Depends(get_current_user)):
    job_id = str(uuid.uuid4())
    job = CrawlerJob(job_id)
    
    # GANTI run_local_crawler dengan run_remote_crawler
    job.task = asyncio.create_task(
        run_remote_crawler(job, ",".join(request.keywords), request.domain_count)
    )
    
    active_jobs[job_id] = job
    return {"job_id": job_id, "status": "started"}
```

### Step 2: RunPod Implementation

RunPod harus:

1. **Terima request** dengan `job_id` dan `callback_url`
2. **Kirim progress log** ke `callback_url`
3. **Return hasil** di akhir

```python
# Di RunPod
@app.post("/process")
async def process(request: Request):
    body = await request.json()
    keyword = body.get("data")
    num_domains = body.get("num_domains")
    job_id = body.get("job_id")  # ← Ambil job_id
    callback_url = body.get("callback_url")  # ← Ambil callback URL
    
    # Kirim log ke backend
    async def send_log(message):
        if callback_url and job_id:
            async with httpx.AsyncClient() as client:
                await client.post(
                    callback_url,
                    json={"job_id": job_id, "message": message}
                )
    
    await send_log("[INFO] Starting on RunPod...")
    
    # Process...
    domains = []
    for i in range(num_domains):
        domain = generate_domain(keyword, i)
        domains.append(domain)
        await send_log(f"[INFO] Progress: {(i+1)*100//num_domains}%")
    
    await send_log("[SUCCESS] Completed!")
    
    return {"status": "success", "domains": domains}
```

---

## 🧪 Testing Current Setup (Local Crawler)

### Test 1: Start Job

```bash
TOKEN="your-token"

curl -X POST http://18.140.62.254/api/crawler/start \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "domain_count": 3,
    "keywords": ["test keyword"]
  }'
```

### Test 2: Stream Logs

```bash
JOB_ID="from-step-1"

curl -N http://18.140.62.254/api/crawler/logs/$JOB_ID
```

### Test 3: Check Status

```bash
curl http://18.140.62.254/api/crawler/status/$JOB_ID
```

---

## 📋 Decision Matrix

| Scenario | Use Local Crawler | Use RunPod |
|----------|-------------------|------------|
| Crawler.py sudah ada | ✅ Yes | ❌ No |
| Butuh scalability | ❌ No | ✅ Yes |
| Butuh GPU processing | ❌ No | ✅ Yes |
| Simple deployment | ✅ Yes | ❌ No |
| Cost sensitive | ✅ Yes | ❌ No |

---

## 🔍 Troubleshooting

### Issue: "crawler.py not found"

**Solusi**: Pastikan file ada di `/backend/domain-generator/crawler.py`

```bash
# Check file exists
ls -la /home/ubuntu/prototype-dashboard-chatbot/backend/domain-generator/crawler.py

# Jika tidak ada, buat symlink atau copy file
```

### Issue: "Job not found" saat kirim log

**Penyebab**: Job_id tidak ada di `active_jobs`

**Solusi**: 
- Jika pakai local crawler: Tidak perlu kirim log manual
- Jika pakai RunPod: Pastikan job_id dikirim dari backend ke RunPod

---

## 📞 Summary

**Current Status**: 
- ✅ Local crawler active
- ✅ Log streaming works
- ✅ Summary parsing works
- ❌ RunPod integration disabled

**To Enable RunPod**:
1. Uncomment `run_remote_crawler` function
2. Change `start_crawler` to use `run_remote_crawler`
3. Implement RunPod side dengan callback
4. Test integration

**Recommendation**: 
Tetap gunakan local crawler jika `crawler.py` sudah berfungsi dengan baik. Gunakan RunPod hanya jika butuh scalability atau GPU processing.

---

**Last Updated**: 2025-12-16
**Status**: Local Crawler Active ✅

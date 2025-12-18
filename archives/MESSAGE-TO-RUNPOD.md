# Message to RunPod Team

## Current Situation

Backend telah **kembali menggunakan local crawler** (`crawler.py`), sehingga:

❌ **RunPod integration TIDAK DIGUNAKAN saat ini**

Endpoint `/api/crawler/log` memang ada, tapi hanya berfungsi jika job_id sudah ada di `active_jobs` (yang dibuat oleh backend sendiri saat start job).

---

## Why 404 Error?

Ketika RunPod mencoba kirim log:

```
POST http://18.140.62.254/api/crawler/log
{
  "job_id": "some-id",
  "message": "[INFO] ..."
}
```

Backend check:
```python
if job_id not in active_jobs:
    raise HTTPException(status_code=404, detail="Job not found")
```

Karena job dibuat oleh **local crawler** (bukan RunPod), job_id yang RunPod kirim tidak ada di `active_jobs` → 404.

---

## Solution Options

### Option 1: Stop Sending Logs (Current)

Karena backend pakai local crawler, RunPod **tidak perlu** kirim log.

**Action**: Disable log sending di RunPod side.

### Option 2: Full RunPod Integration (Future)

Jika mau pakai RunPod, backend harus:

1. **Kirim job_id** ke RunPod saat request
2. **Create job** di `active_jobs` sebelum call RunPod
3. **RunPod kirim log** dengan job_id yang sama

**Flow**:
```
1. Frontend → Backend: Start job
2. Backend: Create job_id, add to active_jobs
3. Backend → RunPod: POST /process with job_id
4. RunPod → Backend: POST /log with same job_id ✅
5. Backend → Frontend: Stream logs
```

**Implementation** (Backend side):
```python
@router.post("/start")
async def start_crawler(request: CrawlerRequest):
    job_id = str(uuid.uuid4())
    job = CrawlerJob(job_id)
    
    # Add to active_jobs FIRST
    active_jobs[job_id] = job
    
    # Then call RunPod with job_id
    job.task = asyncio.create_task(
        call_runpod_with_job_id(job, job_id, keywords, num_domains)
    )
    
    return {"job_id": job_id}

async def call_runpod_with_job_id(job, job_id, keywords, num_domains):
    async with httpx.AsyncClient() as client:
        await client.post(
            "https://runpod-url/process",
            json={
                "data": keywords,
                "num_domains": num_domains,
                "job_id": job_id,  # ← Send job_id
                "callback_url": "http://18.140.62.254/api/crawler/log"
            }
        )
```

**Implementation** (RunPod side):
```python
@app.post("/process")
async def process(request: Request):
    body = await request.json()
    job_id = body.get("job_id")  # ← Receive job_id
    callback_url = body.get("callback_url")
    
    # Use this job_id when sending logs
    await send_log(callback_url, job_id, "[INFO] Starting...")
```

---

## Recommendation

**For Now**: 
- ✅ Backend menggunakan local crawler
- ✅ Tidak perlu RunPod integration
- ✅ Disable log sending dari RunPod

**For Future**:
- Jika butuh scalability → Implement Option 2
- Jika butuh GPU → Implement Option 2
- Jika local crawler cukup → Tetap pakai local

---

## Questions?

Contact backend team untuk:
1. Apakah mau pakai RunPod atau tetap local?
2. Jika pakai RunPod, backend perlu update untuk kirim job_id
3. Jika tetap local, RunPod tidak perlu kirim log

---

**Status**: Waiting for decision
**Current**: Local crawler active
**RunPod**: Not integrated

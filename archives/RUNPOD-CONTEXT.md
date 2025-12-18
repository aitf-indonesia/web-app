# RunPod Service Integration Guide

## 🎯 Overview

RunPod service akan menerima request untuk generate domains dan mengirim progress log ke backend utama secara real-time.

---

## 📡 API Specification

### 1. Endpoint yang Harus Dibuat di RunPod

**Endpoint**: `POST /process`

**Request Body**:
```json
{
  "data": "keyword1, keyword2",
  "num_domains": 5,
  "job_id": "uuid-from-backend"
}
```

**Response**:
```json
{
  "status": "success",
  "domains": ["domain1.com", "domain2.com", ...],
  "count": 5,
  "keyword": "keyword1, keyword2"
}
```

### 2. Endpoint Backend untuk Kirim Log

**URL**: `http://18.140.62.254/api/crawler/log`

**Method**: `POST`

**Request Body**:
```json
{
  "job_id": "uuid-from-request",
  "message": "[INFO] Your log message here"
}
```

**Response**:
```json
{
  "status": "success",
  "job_id": "uuid",
  "message": "Log message received and queued"
}
```

---

## 🔄 Integration Flow

```
1. Backend → RunPod:
   POST https://runpod-url/process
   {
     "data": "judi online",
     "num_domains": 10,
     "job_id": "abc-123-def"
   }

2. RunPod → Backend (multiple times during processing):
   POST http://18.140.62.254/api/crawler/log
   {
     "job_id": "abc-123-def",
     "message": "[INFO] Progress: 20%"
   }

3. RunPod → Backend (final response):
   Return: {
     "status": "success",
     "domains": [...],
     "count": 10
   }
```

---

## 💻 Implementation Example

### Complete FastAPI Service

```python
from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
import httpx
import asyncio
from typing import List, Optional
import json

app = FastAPI(title="RunPod Domain Generator")

# Backend URL untuk kirim log
BACKEND_LOG_URL = "http://18.140.62.254/api/crawler/log"

class ProcessRequest(BaseModel):
    data: str  # Keywords
    num_domains: int = 5
    job_id: Optional[str] = None  # Job ID dari backend

class ProcessResponse(BaseModel):
    status: str
    domains: List[str]
    count: int
    keyword: str

async def send_log(job_id: Optional[str], message: str):
    """
    Kirim log ke backend.
    Non-blocking - tidak akan menghentikan proses jika gagal.
    """
    if not job_id:
        print(f"[LOCAL LOG] {message}")
        return
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                BACKEND_LOG_URL,
                json={
                    "job_id": job_id,
                    "message": message
                },
                timeout=5.0
            )
            if response.status_code == 200:
                print(f"✅ Log sent: {message[:50]}...")
            else:
                print(f"⚠️  Log failed ({response.status_code}): {message[:50]}...")
    except Exception as e:
        print(f"⚠️  Failed to send log: {e}")
        # Jangan raise exception - biarkan proses tetap jalan

async def generate_domains(keyword: str, num_domains: int, job_id: Optional[str]) -> List[str]:
    """
    Main domain generation logic.
    Ganti dengan logic sebenarnya.
    """
    
    # Initial log
    await send_log(job_id, "[INFO] Initializing domain generation on RunPod...")
    await send_log(job_id, f"[INFO] Keyword: {keyword}")
    await send_log(job_id, f"[INFO] Target domains: {num_domains}")
    
    domains = []
    keywords_list = [k.strip() for k in keyword.split(',')]
    
    try:
        for i in range(num_domains):
            # === GANTI DENGAN LOGIC GENERATION SEBENARNYA ===
            # Contoh sederhana:
            base_keyword = keywords_list[i % len(keywords_list)]
            domain = f"{base_keyword.replace(' ', '-')}-{i+1}.com"
            domains.append(domain)
            # === END LOGIC ===
            
            # Send progress log
            progress = int((i + 1) / num_domains * 100)
            await send_log(
                job_id, 
                f"[INFO] Progress: {progress}% - Generated: {domain}"
            )
            
            # Simulate processing time (hapus di production)
            await asyncio.sleep(0.3)
        
        # Success log
        await send_log(job_id, "[SUCCESS] Domain generation completed!")
        await send_log(job_id, f"[INFO] Total domains generated: {len(domains)}")
        
        # PENTING: Kirim summary untuk UI
        summary = {
            "status": "success",
            "timestamp": "2025-12-16T10:00:00",
            "time_elapsed": "Remote",
            "domains_generated": {
                "success": len(domains),
                "total": len(domains)
            },
            "screenshot": {
                "success": 0,
                "failed": 0,
                "skipped": 0,
                "total": 0
            },
            "domains_inserted": len(domains),
            "keywords": keywords_list
        }
        await send_log(job_id, f"[SUMMARY] {json.dumps(summary)}")
        
        return domains
        
    except Exception as e:
        await send_log(job_id, f"[ERROR] Generation failed: {str(e)}")
        raise

@app.post("/process", response_model=ProcessResponse)
async def process(request: ProcessRequest):
    """
    Main endpoint untuk menerima request generation.
    """
    try:
        keyword = request.data
        num_domains = request.num_domains
        job_id = request.job_id
        
        # Validate input
        if not keyword or not keyword.strip():
            raise HTTPException(status_code=400, detail="Keyword (data) is required")
        
        if num_domains <= 0:
            raise HTTPException(status_code=400, detail="num_domains must be positive")
        
        # Generate domains
        domains = await generate_domains(keyword, num_domains, job_id)
        
        return ProcessResponse(
            status="success",
            domains=domains,
            count=len(domains),
            keyword=keyword
        )
        
    except HTTPException:
        raise
    except Exception as e:
        # Send error log
        if request.job_id:
            await send_log(request.job_id, f"[ERROR] Process failed: {str(e)}")
        
        return ProcessResponse(
            status="error",
            domains=[],
            count=0,
            keyword=request.data
        )

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "runpod-domain-generator",
        "version": "1.0.0"
    }

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "RunPod Domain Generator",
        "endpoints": {
            "process": "POST /process",
            "health": "GET /health"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3000)
```

---

## 📝 Log Message Format

### Standard Prefixes:

- `[INFO]` - Informasi umum
- `[SUCCESS]` - Operasi berhasil
- `[ERROR]` - Error message
- `[WARNING]` - Warning
- `[DEBUG]` - Debug info
- `[SUMMARY]` - Summary JSON (PENTING untuk UI)

### Example Log Sequence:

```
[INFO] Initializing domain generation on RunPod...
[INFO] Keyword: judi online, slot gacor
[INFO] Target domains: 10
[INFO] Progress: 10% - Generated: judi-online-1.com
[INFO] Progress: 20% - Generated: slot-gacor-2.com
[INFO] Progress: 30% - Generated: judi-online-3.com
...
[INFO] Progress: 100% - Generated: slot-gacor-10.com
[SUCCESS] Domain generation completed!
[INFO] Total domains generated: 10
[SUMMARY] {"status": "success", "domains_generated": {"success": 10, "total": 10}, ...}
```

### Summary Format (PENTING):

```json
{
  "status": "success",
  "timestamp": "2025-12-16T10:00:00",
  "time_elapsed": "Remote",
  "domains_generated": {
    "success": 10,
    "total": 10
  },
  "screenshot": {
    "success": 0,
    "failed": 0,
    "skipped": 0,
    "total": 0
  },
  "domains_inserted": 10,
  "keywords": ["judi online", "slot gacor"]
}
```

---

## 🧪 Testing

### Test 1: Local Test (tanpa backend)

```bash
# Start service
python3 runpod_service.py

# Test endpoint
curl -X POST http://localhost:3000/process \
  -H "Content-Type: application/json" \
  -d '{
    "data": "test keyword",
    "num_domains": 3
  }'
```

### Test 2: With Backend Integration

```bash
# Test dengan job_id
curl -X POST http://localhost:3000/process \
  -H "Content-Type: application/json" \
  -d '{
    "data": "test keyword",
    "num_domains": 3,
    "job_id": "test-job-123"
  }'

# Check logs di backend
curl -N http://18.140.62.254/api/crawler/logs/test-job-123
```

### Test 3: Full Integration

1. Start job dari UI atau API backend
2. Dapatkan job_id
3. Call RunPod dengan job_id tersebut
4. Lihat log muncul real-time di UI

---

## 🚀 Deployment

### Requirements:

```txt
fastapi==0.104.1
uvicorn==0.24.0
httpx==0.25.0
pydantic==2.5.0
```

### Install:

```bash
pip install -r requirements.txt
```

### Run:

```bash
# Development
uvicorn main:app --host 0.0.0.0 --port 3000 --reload

# Production
uvicorn main:app --host 0.0.0.0 --port 3000 --workers 4
```

### Docker (Optional):

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "3000"]
```

```bash
docker build -t runpod-service .
docker run -p 3000:3000 runpod-service
```

---

## 🔍 Debugging

### Check Logs:

```bash
# Service logs
tail -f /var/log/runpod-service.log

# Atau jika pakai systemd
journalctl -u runpod-service -f
```

### Test Backend Connectivity:

```bash
# Dari RunPod VPS, test koneksi ke backend
curl -v http://18.140.62.254/api/crawler/log

# Test POST
curl -X POST http://18.140.62.254/api/crawler/log \
  -H "Content-Type: application/json" \
  -d '{"job_id": "test", "message": "[INFO] Test from RunPod"}'
```

### Common Issues:

**Issue**: Log tidak terkirim
- Check network connectivity ke backend
- Check backend URL benar
- Check job_id valid

**Issue**: Process timeout
- Increase timeout di backend
- Optimize generation logic
- Add more progress logs

---

## 📊 Monitoring

### Metrics to Track:

- Request count
- Success/error rate
- Average processing time
- Log send success rate

### Example with Prometheus:

```python
from prometheus_client import Counter, Histogram

request_count = Counter('requests_total', 'Total requests')
processing_time = Histogram('processing_seconds', 'Processing time')

@app.post("/process")
async def process(request: ProcessRequest):
    request_count.inc()
    with processing_time.time():
        # ... processing logic
```

---

## ✅ Checklist

### Development:
- [ ] Service bisa receive request `/process`
- [ ] Bisa extract `job_id` dari request
- [ ] Bisa kirim log ke backend
- [ ] Bisa generate domains (logic sebenarnya)
- [ ] Bisa return response yang benar
- [ ] Error handling proper

### Testing:
- [ ] Test tanpa job_id (should work)
- [ ] Test dengan job_id (log terkirim)
- [ ] Test error handling
- [ ] Test dengan backend real
- [ ] Test full integration dengan UI

### Production:
- [ ] Service running stable
- [ ] Monitoring setup
- [ ] Logging setup
- [ ] Error alerting
- [ ] Performance optimization

---

## 📞 Support

**Backend Team Contact**: [Your contact]

**Backend URL**: `http://18.140.62.254`

**Documentation**: 
- Backend Setup: `RUNPOD-BACKEND-SETUP.md`
- This Guide: `RUNPOD-CONTEXT.md`

---

**Last Updated**: 2025-12-16
**Version**: 1.0.0
**Status**: Ready for Implementation ✅

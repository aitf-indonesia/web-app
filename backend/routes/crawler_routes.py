from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import os
import uuid
import asyncio
from typing import Dict, Optional
import json
import sys
from datetime import datetime
from utils.auth_middleware import get_current_user
from sqlalchemy import text
from db import engine 
import aiofiles

router = APIRouter()

# Log file path (must match crawler.py in integrasi-service)
LOG_FILE_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "integrasi-service", "domain-generator", "output", "crawler.log")

# =========================
# JOB MANAGEMENT
# =========================
class CrawlerJob:
    def __init__(self, job_id: str):
        self.job_id = job_id
        self.queue = asyncio.Queue()
        self.task: Optional[asyncio.Task] = None
        self.returncode: Optional[int] = None
        self.summary: Optional[dict] = None

    async def log(self, message: str):
        await self.queue.put(f"data: {message}\n\n")

    async def error(self, message: str):
        await self.queue.put(f"data: [ERROR] {message}\n\n")

    async def finish(self):
        await self.queue.put("data: [DONE]\n\n")
        await self.queue.put(None)
        self.returncode = 0


active_jobs: Dict[str, CrawlerJob] = {}

# =========================
# REQUEST MODELS
# =========================
class CrawlerRequest(BaseModel):
    domain_count: int
    keywords: list[str]


class ManualCrawlerRequest(BaseModel):
    domains: list[str]


class LogMessage(BaseModel):
    job_id: str
    message: str


# =========================
# CORE: RUN LOCAL CRAWLER
# =========================
async def run_runpod_crawler(
    job: CrawlerJob,
    keywords: list[str],
    domain_count: int,
    username: str
):
    """
    Call RunPod API and stream logs + REAL summary.
    """
    import httpx
    
    summary = None
    runpod_base_url = os.getenv("SERVICE_API_URL", "http://localhost:5000")
    runpod_url = f"{runpod_base_url}/process"

    try:
        # Gunakan keyword pertama untuk dikirim ke RunPod
        keyword_data = keywords[0] if keywords else ""
        
        await job.log(f"[INFO] Connecting to RunPod API...")
        await job.log(f"[INFO] Keyword: {keyword_data}")
        await job.log(f"[INFO] Domain count: {domain_count}")

        # Prepare request payload
        payload = {
            "data": keyword_data,
            "num_domains": domain_count
        }

        headers = {
            "Content-Type": "application/json",
        }

        # Stream response from RunPod API
        async with httpx.AsyncClient(timeout=3600.0) as client:  # 1 hour timeout for large batches
            async with client.stream("POST", runpod_url, json=payload, headers=headers) as response:
                if response.status_code != 200:
                    error_text = await response.aread()
                    await job.error(f"RunPod API error: {response.status_code} - {error_text.decode()}")
                    return

                await job.log("[INFO] Connected to RunPod API, streaming logs...")
                
                # Track if we just saw a [SAVE] line
                save_line_seen = False
                
                # Stream line by line
                async for line in response.aiter_lines():
                    if not line:
                        continue
                    
                    # Check if this is the [SAVE] Summary saved line
                    if line.startswith("[SAVE] Summary saved:"):
                        save_line_seen = True
                        # Don't send the file path to UI
                        continue
                    
                    # If previous line was [SAVE], this line should be the JSON
                    if save_line_seen:
                        save_line_seen = False
                        try:
                            job.summary = json.loads(line)
                            # Send as [SUMMARY] format for frontend compatibility
                            await job.log(f"[SUMMARY] {line}")
                            continue
                        except Exception as e:
                            await job.error(f"Failed to parse summary JSON: {str(e)}")
                    
                    # Send log to UI
                    await job.log(line)
                    
                    # Also check for old [SUMMARY] format for backward compatibility
                    if line.startswith("[SUMMARY]"):
                        try:
                            summary_json = line.replace("[SUMMARY]", "").strip()
                            job.summary = json.loads(summary_json)
                        except Exception as e:
                            await job.error(f"Failed to parse summary JSON: {str(e)}")

        # If summary was found, ensure it's sent to frontend
        if job.summary is not None:
            await job.log(f"[SUMMARY] {json.dumps(job.summary)}")
        else:
            await job.log("[INFO] Crawler finished without summary")
        
    except httpx.TimeoutException:
        await job.error("RunPod API request timeout")
    except httpx.RequestError as e:
        await job.error(f"RunPod API connection error: {str(e)}")
    except Exception as e:
        await job.error(f"Exception while calling RunPod API: {str(e)}")
    finally:
        await job.finish()


# =========================
# CORE: RUN RUNPOD MANUAL CRAWLER
# =========================
async def run_runpod_manual_crawler(
    job: CrawlerJob,
    domains: list[str],
    username: str
):
    """
    Call RunPod API /process-links and stream logs for manual domain input.
    """
    import httpx
    
    summary = None
    runpod_base_url = os.getenv("SERVICE_API_URL", "http://localhost:5000")
    runpod_url = f"{runpod_base_url}/process-links"

    try:
        await job.log(f"[INFO] Connecting to RunPod API (Manual Mode)...")
        await job.log(f"[INFO] Processing {len(domains)} domains")

        # Prepare request payload
        payload = {
            "links": domains
        }

        headers = {
            "Content-Type": "application/json",
        }

        # Stream response from RunPod API
        async with httpx.AsyncClient(timeout=3600.0) as client:  # 1 hour timeout for large batches
            async with client.stream("POST", runpod_url, json=payload, headers=headers) as response:
                if response.status_code != 200:
                    error_text = await response.aread()
                    await job.error(f"RunPod API error: {response.status_code} - {error_text.decode()}")
                    return

                await job.log("[INFO] Connected to RunPod API, streaming logs...")
                
                # Track if we just saw a [SAVE] line
                save_line_seen = False
                
                # Stream line by line
                async for line in response.aiter_lines():
                    if not line:
                        continue
                    
                    # Check if this is the [SAVE] Summary saved line
                    if line.startswith("[SAVE] Summary saved:"):
                        save_line_seen = True
                        # Don't send the file path to UI
                        continue
                    
                    # If previous line was [SAVE], this line should be the JSON
                    if save_line_seen:
                        save_line_seen = False
                        try:
                            job.summary = json.loads(line)
                            # Send as [SUMMARY] format for frontend compatibility
                            await job.log(f"[SUMMARY] {line}")
                            continue
                        except Exception as e:
                            await job.error(f"Failed to parse summary JSON: {str(e)}")
                    
                    # Send log to UI
                    await job.log(line)
                    
                    # Also check for old [SUMMARY] format for backward compatibility
                    if line.startswith("[SUMMARY]"):
                        try:
                            summary_json = line.replace("[SUMMARY]", "").strip()
                            job.summary = json.loads(summary_json)
                        except Exception as e:
                            await job.error(f"Failed to parse summary JSON: {str(e)}")

        # If summary was found, ensure it's sent to frontend
        if job.summary is not None:
            await job.log(f"[SUMMARY] {json.dumps(job.summary)}")
        else:
            await job.log("[INFO] Crawler finished without summary")
        
    except httpx.TimeoutException:
        await job.error("RunPod API request timeout")
    except httpx.RequestError as e:
        await job.error(f"RunPod API connection error: {str(e)}")
    except Exception as e:
        await job.error(f"Exception while calling RunPod API: {str(e)}")
    finally:
        await job.finish()


# =========================
# API: START CRAWLER
# =========================
@router.post("/start")
async def start_crawler(
    request: CrawlerRequest,
    current_user: dict = Depends(get_current_user)
):
    if request.domain_count <= 0:
        raise HTTPException(status_code=400, detail="Domain count must be positive")

    if not request.keywords:
        raise HTTPException(status_code=400, detail="Keywords cannot be empty")

    job_id = str(uuid.uuid4())
    job = CrawlerJob(job_id)

    job.task = asyncio.create_task(
        run_runpod_crawler(
            job=job,
            keywords=request.keywords,
            domain_count=request.domain_count,
            username=current_user.get("username", "system")
        )
    )

    active_jobs[job_id] = job

    return {
        "job_id": job_id,
        "status": "started",
        "message": "Crawler started locally"
    }


# =========================
# API: START MANUAL CRAWLER
# =========================
@router.post("/manual")
async def start_manual_crawler(
    request: ManualCrawlerRequest,
    current_user: dict = Depends(get_current_user)
):
    if not request.domains:
        raise HTTPException(status_code=400, detail="Domains cannot be empty")

    job_id = str(uuid.uuid4())
    job = CrawlerJob(job_id)

    job.task = asyncio.create_task(
        run_runpod_manual_crawler(
            job=job,
            domains=request.domains,
            username=current_user.get("username", "system")
        )
    )

    active_jobs[job_id] = job

    return {
        "job_id": job_id,
        "status": "started",
        "message": "Manual crawler started"
    }


# =========================
# API: STREAM LOGS FROM FILE (Real-time)
# NOTE: This MUST come before /logs/{job_id} to avoid route conflict
# =========================
@router.get("/logs/file")
async def stream_logs_from_file():
    """
    Stream logs directly from the crawler log file.
    This bypasses subprocess buffering and provides real-time logs.
    """
    async def file_log_generator():
        last_position = 0
        end_marker_found = False
        max_wait_cycles = 14400  # 2 hours max (14400 * 0.5 seconds) for large batches
        wait_cycles = 0
        
        # Send initial keepalive
        yield ": keepalive\n\n"
        
        while not end_marker_found and wait_cycles < max_wait_cycles:
            try:
                # Check if file exists
                if not os.path.exists(LOG_FILE_PATH):
                    await asyncio.sleep(0.5)
                    wait_cycles += 1
                    continue
                
                # Read new content from file
                async with aiofiles.open(LOG_FILE_PATH, mode='r', encoding='utf-8') as f:
                    await f.seek(last_position)
                    content = await f.read()
                    
                    if content:
                        # Update position
                        last_position = await f.tell()
                        
                        # Check for end marker
                        if "===END===" in content:
                            end_marker_found = True
                        
                        # Split content into lines and send as SSE events
                        lines = content.strip().split('\n')
                        for line in lines:
                            if line.strip():
                                # Check if this is a summary JSON line (may have timestamp prefix)
                                # Pattern: either starts with { or has timestamp like [08:31:56] {
                                stripped_line = line.strip()
                                json_start = stripped_line.find('{')
                                if json_start != -1 and '"status"' in stripped_line and '"domains_generated"' in stripped_line:
                                    try:
                                        json_part = stripped_line[json_start:]
                                        summary = json.loads(json_part)
                                        yield f"data: [SUMMARY] {json_part}\n\n"
                                        continue
                                    except:
                                        pass
                                
                                yield f"data: {line}\n\n"
                        
                        # Reset wait cycles since we got content
                        wait_cycles = 0
                    else:
                        # No new content, wait a bit and send keepalive
                        await asyncio.sleep(0.5)
                        wait_cycles += 1
                        
                        # Send keepalive every 10 cycles (5 seconds)
                        if wait_cycles % 10 == 0:
                            yield ": keepalive\n\n"
                        
            except Exception as e:
                yield f"data: [ERROR] Failed to read log file: {str(e)}\n\n"
                break
        
        # Send completion marker
        yield "data: [DONE]\n\n"
    
    return StreamingResponse(
        file_log_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "Content-Type": "text/event-stream; charset=utf-8"
        }
    )


# =========================
# API: STREAM LOGS (SSE) - Job-based
# =========================
@router.get("/logs/{job_id}")
async def stream_logs(job_id: str):
    if job_id not in active_jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job = active_jobs[job_id]

    async def event_generator():
        try:
            yield ": keepalive\n\n"

            while True:
                try:
                    message = await asyncio.wait_for(job.queue.get(), timeout=15.0)

                    if message is None:
                        break

                    yield message

                except asyncio.TimeoutError:
                    yield ": keepalive\n\n"

            if job_id in active_jobs:
                del active_jobs[job_id]

        except Exception as e:
            yield f"data: [ERROR] {str(e)}\n\n"
            if job_id in active_jobs:
                del active_jobs[job_id]

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


# =========================
# API: CANCEL JOB
# =========================
@router.post("/cancel/{job_id}")
async def cancel_crawler(job_id: str):
    if job_id not in active_jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job = active_jobs[job_id]

    if job.task:
        job.task.cancel()

    await job.error("Job cancelled by user")
    await job.finish()

    if job_id in active_jobs:
        del active_jobs[job_id]

    return {
        "job_id": job_id,
        "status": "cancelled",
        "message": "Crawler job cancelled"
    }


# =========================
# API: STATUS
# =========================
@router.get("/status/{job_id}")
async def get_crawler_status(job_id: str):
    if job_id not in active_jobs:
        return {
            "job_id": job_id,
            "status": "completed_or_not_found",
            "summary": None
        }

    job = active_jobs[job_id]

    return {
        "job_id": job_id,
        "status": "completed" if job.summary else "running",
        "summary": job.summary
    }


# =========================
# API: EXTERNAL LOG (OPTIONAL)
# =========================
@router.post("/log")
async def receive_log(log_message: LogMessage):
    job_id = log_message.job_id
    message = log_message.message

    if job_id not in active_jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job = active_jobs[job_id]
    await job.log(message)

    return {
        "status": "success",
        "job_id": job_id,
        "message": "Log message queued"
    }

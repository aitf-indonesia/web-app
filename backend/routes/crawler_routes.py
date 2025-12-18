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
from utils.db import engine 

router = APIRouter()

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
async def run_local_crawler(
    job: CrawlerJob,
    keywords: list[str],
    domain_count: int,
    username: str
):
    """
    Run crawler.py locally and stream logs + REAL summary.
    """
    summary = None

    try:
        keywords_str = ",".join(keywords)

        # Path ke crawler.py
        crawler_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "domain-generator")
        )
        crawler_path = os.path.join(crawler_dir, "crawler.py")

        if not os.path.exists(crawler_path):
            await job.error(f"crawler.py not found at {crawler_path}")
            return

        cmd = [
            sys.executable,
            crawler_path,
            "-n", str(domain_count),
            "-k", keywords_str,
            "-u", username
        ]

        await job.log("[INFO] Starting local crawler")
        await job.log(f"[INFO] Command: {' '.join(cmd)}")

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            cwd=crawler_dir
        )

        # Stream stdout line by line
        while True:
            line = await process.stdout.readline()
            if not line:
                break

            decoded = line.decode("utf-8", errors="ignore").rstrip()
            await job.log(decoded)

            # === AMBIL SUMMARY ASLI DARI CRAWLER ===
            if decoded.startswith("[SUMMARY]"):
                try:
                    summary_json = decoded.replace("[SUMMARY]", "").strip()
                    job.summary = json.loads(summary_json) 
                except Exception as e:
                    await job.error(f"Failed to parse summary JSON: {str(e)}")

        await process.wait()

        if summary is None:
            await job.error("Crawler finished but [SUMMARY] not found")
        else:
            # Pastikan summary dikirim ke UI
            await job.log(f"[SUMMARY] {json.dumps(summary)}")

    except Exception as e:
        await job.error(f"Exception while running crawler: {str(e)}")

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
        run_local_crawler(
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
# API: STREAM LOGS (SSE)
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

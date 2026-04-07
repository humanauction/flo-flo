import asyncio
from datetime import datetime, timezone
from threading import Lock
from typing import Any, Optional
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.services.headline_service import HeadlineService

router = APIRouter()

MAX_ADMIN_JOB_COUNT = 50
DEFAULT_ADMIN_JOB_COUNT = 10

_JOB_STATUS_QUEUED = "queued"
_JOB_STATUS_RUNNING = "running"
_JOB_STATUS_COMPLETED = "completed"
_JOB_STATUS_FAILED = "failed"

_JOB_STORE: dict[str, dict[str, Any]] = {}
_JOB_LOCK = Lock()


class AddHeadlineRequest(BaseModel):
    text: str
    is_real: bool
    source_url: Optional[str] = None


class TriggerJobRequest(BaseModel):
    count: int = DEFAULT_ADMIN_JOB_COUNT


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _validate_requested_count(count: Any) -> int:
    if isinstance(count, bool) or not isinstance(count, int):
        raise HTTPException(status_code=400, detail="count must be an integer")
    if count < 1 or count > MAX_ADMIN_JOB_COUNT:
        raise HTTPException(
            status_code=400,
            detail=f"count must be between 1 and {MAX_ADMIN_JOB_COUNT}",
        )
    return count


def _public_job_payload(job: dict[str, Any]) -> dict[str, Any]:
    return {
        "job_id": job["job_id"],
        "job_type": job["job_type"],
        "status": job["status"],
        "requested_count": job["requested_count"],
        "message": job["message"],
        "created_at": job["created_at"],
        "started_at": job["started_at"],
        "finished_at": job["finished_at"],
        "error": job["error"],
        "result_summary": job["result_summary"],
    }


def _create_job(job_type: str, requested_count: int) -> dict[str, Any]:
    job_id = str(uuid4())
    record = {
        "job_id": job_id,
        "job_type": job_type,
        "status": _JOB_STATUS_QUEUED,
        "requested_count": requested_count,
        "message": f"{job_type} job queued",
        "created_at": _utc_now_iso(),
        "started_at": None,
        "finished_at": None,
        "error": None,
        "result_summary": None,
    }
    with _JOB_LOCK:
        _JOB_STORE[job_id] = record
    return record


def _get_job(job_id: str) -> dict[str, Any] | None:
    with _JOB_LOCK:
        job = _JOB_STORE.get(job_id)
        if job is None:
            return None
        return dict(job)


def _update_job(job_id: str, **updates: Any) -> None:
    with _JOB_LOCK:
        job = _JOB_STORE.get(job_id)
        if job is None:
            return
        job.update(updates)


def _execute_scrape_job(requested_count: int) -> str:
    from agents.tools.database import save_headlines_to_db
    from agents.tools.scraper import HeadlineScraper

    scraper = HeadlineScraper()
    scrape_result = scraper.scrape_with_metrics()

    headlines = scrape_result["headlines"][:requested_count]
    payload: list[dict[str, Any]] = []
    for item in headlines:
        text = item.get("text")
        source_url = item.get("source_url")
        if not isinstance(text, str) or not text.strip():
            continue
        payload.append(
            {
                "text": text.strip(),
                "is_real": True,
                "source_url": source_url if isinstance(source_url, str) else None,
            }
        )

    save_result = save_headlines_to_db(payload)
    metrics = scrape_result["metrics"]

    return (
        f"Scraped {len(payload)} real headlines. "
        f"{save_result}. "
        f"Metrics: fetched_total={metrics['fetched_total']}, "
        f"kept_total={metrics['kept_total']}"
    )


def _collect_text_chunks(event: Any) -> list[str]:
    chunks: list[str] = []

    for attr in ("content", "text"):
        value = getattr(event, attr, None)
        if isinstance(value, str) and value.strip():
            chunks.append(value.strip())

    msg = getattr(event, "message", None)
    if msg is not None:
        for attr in ("content", "text"):
            value = getattr(msg, attr, None)
            if isinstance(value, str) and value.strip():
                chunks.append(value.strip())

    messages = getattr(event, "messages", None)
    if isinstance(messages, list):
        for item in messages:
            if isinstance(item, str) and item.strip():
                chunks.append(item.strip())
                continue
            for attr in ("content", "text"):
                value = getattr(item, attr, None)
                if isinstance(value, str) and value.strip():
                    chunks.append(value.strip())

    return chunks


async def _run_generate_job_async(requested_count: int) -> str:
    from agents.generator_agent import create_generator_agent

    agent = create_generator_agent()
    task = (
        "You must call your generate_fake_headlines tool with "
        f"count={requested_count}. Return only the tool result summary."
    )

    chunks: list[str] = []
    async for event in agent.run_stream(task=task):
        chunks.extend(_collect_text_chunks(event))

    result_text = "\n".join(chunks).strip()
    if not result_text:
        raise RuntimeError("Generator agent returned empty output")
    return result_text


def _execute_generate_job(requested_count: int) -> str:
    return asyncio.run(_run_generate_job_async(requested_count))


def _run_job(job_id: str, job_type: str, requested_count: int) -> None:
    _update_job(
        job_id,
        status=_JOB_STATUS_RUNNING,
        message=f"{job_type} job running",
        started_at=_utc_now_iso(),
    )

    try:
        if job_type == "scrape":
            result_summary = _execute_scrape_job(requested_count)
        elif job_type == "generate":
            result_summary = _execute_generate_job(requested_count)
        else:
            raise RuntimeError(f"Unsupported job type: {job_type}")

        _update_job(
            job_id,
            status=_JOB_STATUS_COMPLETED,
            message=f"{job_type} job completed",
            finished_at=_utc_now_iso(),
            result_summary=result_summary,
            error=None,
        )
    except Exception as exc:
        _update_job(
            job_id,
            status=_JOB_STATUS_FAILED,
            message=f"{job_type} job failed",
            finished_at=_utc_now_iso(),
            error=str(exc),
        )


def _queue_job(
    background_tasks: BackgroundTasks,
    job_type: str,
    requested_count: int,
) -> dict[str, Any]:
    job = _create_job(job_type=job_type, requested_count=requested_count)
    background_tasks.add_task(
        _run_job,
        job["job_id"],
        job_type,
        requested_count,
    )
    return _public_job_payload(job)


@router.get("/stats")
async def get_stats(db: Session = Depends(get_db)):
    service = HeadlineService(db)
    return service.get_stats()


@router.post("/headline")
async def add_headline(request: AddHeadlineRequest, db: Session = Depends(get_db)):
    service = HeadlineService(db)

    try:
        headline = service.add_headline(
            text=request.text,
            is_real=request.is_real,
            source_url=request.source_url,
        )
        return {
            "id": headline.id,
            "text": headline.text,
            "is_real": headline.is_real,
            "message": "Headline added successfully",
        }
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/scrape")
async def trigger_scrape(
    background_tasks: BackgroundTasks,
    request: TriggerJobRequest | None = None,
):
    requested_count = (
        request.count if request is not None else DEFAULT_ADMIN_JOB_COUNT
    )
    requested_count = _validate_requested_count(requested_count)
    return _queue_job(
        background_tasks=background_tasks,
        job_type="scrape",
        requested_count=requested_count,
    )


@router.post("/generate")
async def trigger_generate(
    background_tasks: BackgroundTasks,
    request: TriggerJobRequest | None = None,
):
    requested_count = (
        request.count if request is not None else DEFAULT_ADMIN_JOB_COUNT
    )
    requested_count = _validate_requested_count(requested_count)
    return _queue_job(
        background_tasks=background_tasks,
        job_type="generate",
        requested_count=requested_count,
    )


@router.get("/jobs/{job_id}")
async def get_job_status(job_id: str):
    job = _get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return _public_job_payload(job)

import time

from app.routers import admin as admin_router


def _wait_for_terminal_job_status(client, job_id: str):
    for _ in range(50):
        res = client.get(f"/api/admin/jobs/{job_id}")
        assert res.status_code == 200
        body = res.json()
        if body["status"] in {"completed", "failed"}:
            return body
        time.sleep(0.01)
    raise AssertionError("Job did not reach terminal state in time")


def test_admin_stats_empty(client):
    res = client.get("/api/admin/stats")
    assert res.status_code == 200
    data = res.json()
    assert data["total_headlines"] == 0
    assert data["real_headlines"] == 0
    assert data["fake_headlines"] == 0


def test_admin_add_headline_and_stats(client):
    add = client.post(
        "/api/admin/headline",
        json={
            "text": "Florida woman steals kayak from rooftop bar",
            "is_real": False,
            "source_url": None,
        },
    )
    assert add.status_code == 200
    body = add.json()
    assert body["message"] == "Headline added successfully"
    assert body["is_real"] is False

    stats = client.get("/api/admin/stats")
    assert stats.status_code == 200
    s = stats.json()
    assert s["total_headlines"] == 1
    assert s["real_headlines"] == 0
    assert s["fake_headlines"] == 1


def test_admin_duplicate_headline_returns_400(client):
    payload = {
        "text": "Florida man attempts moonwalk during traffic stop",
        "is_real": True,
        "source_url": "https://example.com/a",
    }

    first = client.post("/api/admin/headline", json=payload)
    assert first.status_code == 200

    second = client.post("/api/admin/headline", json=payload)
    assert second.status_code == 400
    assert "already exists" in second.json()["detail"]


def test_admin_trigger_scrape_job_and_status(client, monkeypatch):
    monkeypatch.setattr(
        admin_router,
        "_execute_scrape_job",
        lambda requested_count: f"scrape-ok-{requested_count}",
    )

    trigger = client.post("/api/admin/scrape", json={"count": 3})
    assert trigger.status_code == 200
    queued = trigger.json()
    assert queued["job_type"] == "scrape"
    assert queued["status"] == "queued"
    assert queued["requested_count"] == 3
    assert queued["error"] is None

    done = _wait_for_terminal_job_status(client, queued["job_id"])
    assert done["status"] == "completed"
    assert done["result_summary"] == "scrape-ok-3"
    assert done["error"] is None


def test_admin_trigger_generate_job_and_status(client, monkeypatch):
    monkeypatch.setattr(
        admin_router,
        "_execute_generate_job",
        lambda requested_count: f"generate-ok-{requested_count}",
    )

    trigger = client.post("/api/admin/generate", json={"count": 4})
    assert trigger.status_code == 200
    queued = trigger.json()
    assert queued["job_type"] == "generate"
    assert queued["status"] == "queued"
    assert queued["requested_count"] == 4
    assert queued["error"] is None

    done = _wait_for_terminal_job_status(client, queued["job_id"])
    assert done["status"] == "completed"
    assert done["result_summary"] == "generate-ok-4"
    assert done["error"] is None


def test_admin_generate_job_failure_is_deterministic(client, monkeypatch):
    def _raise_failure(requested_count: int):
        raise RuntimeError(f"boom-{requested_count}")

    monkeypatch.setattr(admin_router, "_execute_generate_job", _raise_failure)

    trigger = client.post("/api/admin/generate", json={"count": 2})
    assert trigger.status_code == 200
    queued = trigger.json()
    assert queued["status"] == "queued"

    done = _wait_for_terminal_job_status(client, queued["job_id"])
    assert done["status"] == "failed"
    assert done["message"] == "generate job failed"
    assert "boom-2" in (done["error"] or "")


def test_admin_job_count_validation(client):
    bad_zero = client.post("/api/admin/scrape", json={"count": 0})
    assert bad_zero.status_code == 422
    zero_detail = bad_zero.json()["detail"]
    assert isinstance(zero_detail, list) and zero_detail
    assert zero_detail[0]["loc"][-1] == "count"
    assert zero_detail[0]["type"] == "greater_than_equal"
    assert "greater than or equal to 1" in zero_detail[0]["msg"]

    bad_bool = client.post("/api/admin/generate", json={"count": True})
    assert bad_bool.status_code == 422
    bool_detail = bad_bool.json()["detail"]
    assert isinstance(bool_detail, list) and bool_detail
    assert bool_detail[0]["loc"][-1] == "count"
    assert bool_detail[0]["type"] == "int_type"
    assert "valid integer" in bool_detail[0]["msg"]


def test_admin_job_status_not_found(client):
    res = client.get("/api/admin/jobs/not-a-real-job-id")
    assert res.status_code == 404
    assert res.json()["detail"] == "Job not found"


def test_admin_normalize_stream_chunk_strips_blank_lines():
    raw = (
        "  Generated 1 fake headlines (requested 1) "
        "\r\n\r\nSaved 1 new headlines  "
    )
    assert admin_router._normalize_stream_chunk(raw) == (
        "Generated 1 fake headlines (requested 1)\nSaved 1 new headlines"
    )


def test_admin_dedupe_chunks_filters_prompt_and_duplicates():
    task = (
        "You must call your generate_fake_headlines tool with count=1. "
        "Return only the tool result summary."
    )
    chunks = [
        task,
        "Generated 1 fake headlines (requested 1)\n\nSaved 1 new headlines",
        " generated 1 fake headlines (requested 1)\n"
        "saved 1 new headlines ",
        "Provider: openai_primary",
        "provider: openai_primary",
    ]

    deduped = admin_router._dedupe_chunks(chunks, blocked_texts={task})

    assert deduped == [
        "Generated 1 fake headlines (requested 1)\nSaved 1 new headlines",
        "Provider: openai_primary",
    ]

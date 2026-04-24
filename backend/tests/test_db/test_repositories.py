from typing import cast
from app.db.repositories.headline_repository import HeadlineRepository
from app.db.repositories.generation_audit_repository import (
    GenerationAuditRepository
)  # noqa: F401


def test_repository_create_get_count(db_session):
    repo = HeadlineRepository(db_session)
    created = repo.create(
        text="Florida woman launches toaster into orbit",
        is_real=False,
        source_url=None,
    )

    created_id = cast(int, created.id)
    assert created_id is not None

    found = repo.get_by_id(created_id)
    assert found is not None
    assert cast(str, found.text) == "Florida woman launches toaster into orbit"

    assert repo.count_total() == 1
    assert repo.count_fake() == 1
    assert repo.count_real() == 0


def test_repository_exists_and_delete(db_session):
    repo = HeadlineRepository(db_session)
    row = repo.create(
        "Florida man surfs on office chair",
        True,
        "https://example.com"
    )

    row_id = cast(int, row.id)
    assert repo.exists("Florida man surfs on office chair") is True
    assert repo.delete(row_id) is True
    assert repo.get_by_id(row_id) is None


def test_get_recent_real_headlines(db_session):
    repo = HeadlineRepository(db_session)

    old_real = repo.create(
        text="Florida man old real headline",
        is_real=True,
        source_url="https://example.com/old-real",
    )
    repo.create(
        text="Florida man fake headline",
        is_real=False,
        source_url=None,
    )
    new_real = repo.create(
        text="Florida man newest real headline",
        is_real=True,
        source_url="https://example.com/new-real",
    )

    latest_only = repo.get_recent_real(limit=1)
    assert len(latest_only) == 1
    assert latest_only[0].id == old_real.id or latest_only[0].id == new_real.id
    assert latest_only[0].id == new_real.id

    recent_reals = repo.get_recent_real(limit=3)
    assert len(recent_reals) == 2
    assert all(bool(row.is_real) for row in recent_reals)
    assert [row.id for row in recent_reals] == [new_real.id, old_real.id]


def test_generation_audit_repository_create_and_get(db_session):
    repo = GenerationAuditRepository(db_session)
    provenance = {
        "schema_version": 1,
        "provider": "openai_primary",
        "requested_count": 1,
        "recent_real_context_count": 0,
        "recent_real_context": [],
    }

    created = repo.create(
        job_id="job-123",
        requested_count=1,
        result_summary="Generated 1 fake headlines (requested 1)",
        result_provenance=provenance,
    )

    assert created.id is not None
    assert created.provider == "openai_primary"
    assert created.provenance_schema_version == 1
    assert created.provenance_json is not None

    found = repo.get_by_job_id("job-123")
    assert found is not None
    assert found.job_id == "job-123"
    assert found.requested_count == 1


def test_generation_audit_repository_handles_none_provenance(db_session):
    repo = GenerationAuditRepository(db_session)

    created = repo.create(
        job_id="job-456",
        requested_count=2,
        result_summary="Generated 2 fake headlines (requested 2)",
        result_provenance=None,
    )

    assert created.id is not None
    assert created.provider is None
    assert created.provenance_schema_version is None
    assert created.provenance_json is None

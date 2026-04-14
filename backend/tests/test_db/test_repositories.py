from typing import cast
from app.db.repositories.headline_repository import HeadlineRepository


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

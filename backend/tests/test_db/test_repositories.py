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

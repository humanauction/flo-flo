from typing import cast
from app.services.headline_service import HeadlineService


def test_add_headline_and_stats(db_session):
    service = HeadlineService(db_session)
    created = service.add_headline(
        text="Florida man tests headline and stats",
        is_real=False,
        source_url=None,
    )

    assert created.id is not None

    stats = service.get_stats()
    assert stats["total_headlines"] == 1
    assert stats["fake_headlines"] == 1
    assert stats["real_headlines"] == 0


def test_check_guess_returns_expected_payload(db_session):
    service = HeadlineService(db_session)
    item = service.add_headline(
        text="Florida man steals flamingo from mini-golf course",
        is_real=True,
        source_url="https://example.com/story",
    )

    item_id = cast(int, item.id)
    result = service.check_guess(item_id, True)
    assert result is not None
    assert result["correct"] is True
    assert result["was_real"] is True
    assert result["source_url"] == "https://example.com/story"


def test_duplicate_headline_raises_value_error(db_session):
    service = HeadlineService(db_session)
    service.add_headline("Florida man naps in kayak", False, None)

    try:
        service.add_headline("Florida man naps in kayak", False, None)
        assert False, "Expected ValueError for duplicate headline"
    except ValueError as exc:
        assert "already exists" in str(exc)

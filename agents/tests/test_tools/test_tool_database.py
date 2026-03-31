from typing import Any, cast

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from agents.tools import database as db_tools

# Import backend metadata, models via path injection done in db_tools
from app.db.database import Base
from app.models.headline import Headline  # noqa: F401
from app.models.token_usage import TokenUsage  # noqa: F401


def test_save_headlines_to_db_and_stats_offline(monkeypatch, tmp_path):
    test_db_path = tmp_path / "agents_tools_test.db"
    engine = create_engine(
        f"sqlite:///{test_db_path}",
        connect_args={"check_same_thread": False},
    )
    testing_session_local = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
    )

    Base.metadata.create_all(bind=engine)

    # Redirect tool module to test DB session factory
    monkeypatch.setattr(db_tools, "SessionLocal", testing_session_local)

    payload = [
        {
            "text": "Florida man tests offline CI pipeline",
            "is_real": False,
            "source_url": None,
        }
    ]

    first_save = db_tools.save_headlines_to_db(payload)
    second_save = db_tools.save_headlines_to_db(payload)
    stats = db_tools.get_db_stats()

    assert "Saved 1" in first_save
    assert "skipped 1" in second_save or "Saved 0" in second_save
    assert "Total:" in stats
    assert "Fake:" in stats


def test_save_headlines_to_db_rejects_non_list_payload(monkeypatch, tmp_path):
    test_db_path = tmp_path / "agents_tools_test_invalid.db"
    engine = create_engine(
        f"sqlite:///{test_db_path}",
        connect_args={"check_same_thread": False},
    )
    testing_session_local = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
    )
    Base.metadata.create_all(bind=engine)
    monkeypatch.setattr(db_tools, "SessionLocal", testing_session_local)

    bad_payload = cast(Any, {"text": "bad payload"})
    result = db_tools.save_headlines_to_db(bad_payload)
    assert "Invalid payload" in result


def test_save_headlines_to_db_counts_invalid_entries(monkeypatch, tmp_path):
    test_db_path = tmp_path / "agents_tools_test_invalid_entries.db"
    engine = create_engine(
        f"sqlite:///{test_db_path}",
        connect_args={"check_same_thread": False},
    )
    testing_session_local = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
    )
    Base.metadata.create_all(bind=engine)
    monkeypatch.setattr(db_tools, "SessionLocal", testing_session_local)

    payload = [
        {"text": "   ", "is_real": True},
        {"text": "Florida man valid", "is_real": False, "source_url": None},
        {"text": "Florida man invalid bool", "is_real": "false"},
    ]

    result = db_tools.save_headlines_to_db(payload)
    assert "Saved 1" in result
    assert "invalid" in result

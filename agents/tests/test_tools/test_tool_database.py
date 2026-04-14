from typing import Any, cast
import json
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


def test_get_recent_real_headline_context_filters_and_orders(
        monkeypatch,
        tmp_path
):

    test_db_path = tmp_path / "agents_tools_test_recent_real.db"
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

    db_tools.save_headlines_to_db(
        [
            {
                "text": "Florida man old real tool context",
                "is_real": True,
                "source_url": "https://example.com/old"
            }
        ]
    )
    db_tools.save_headlines_to_db(
        [
            {
                "text": "Florida man fake tool context",
                "is_real": False,
                "source_url": None
            }
        ]
    )
    db_tools.save_headlines_to_db(
        [
            {
                "text": "Florida man new real tool context",
                "is_real": True,
                "source_url": "https://example.com/new"
            }
        ]
    )

    latest = db_tools.get_recent_real_headline_context(limit=1)
    assert len(latest) == 1
    assert latest[0]["text"] == "Florida man new real tool context"

    rows = db_tools.get_recent_real_headline_context(limit=3)
    assert [row["text"] for row in rows] == [
        "Florida man new real tool context",
        "Florida man old real tool context",
    ]
    assert all(row["is_real"] is True for row in rows)


def test_recent_real_context_is_json_serializable(monkeypatch, tmp_path):
    test_db_path = tmp_path / "agents_tools_test_context_json.db"
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

    db_tools.save_headlines_to_db([{
        "text": "Florida man old real context json",
        "is_real": True,
        "source_url": "https://example.com/old",
    }])
    db_tools.save_headlines_to_db([{
        "text": "Florida man fake context json",
        "is_real": False,
        "source_url": None,
    }])
    db_tools.save_headlines_to_db([{
        "text": "Florida man new real context json",
        "is_real": True,
        "source_url": "https://example.com/new",
    }])

    rows = db_tools.get_recent_real_headline_context(limit=3)

    assert isinstance(rows, list)
    assert all(isinstance(r, dict) for r in rows)

    required = {"headline_id", "text", "source_url", "created_at", "is_real"}
    assert all(required.issubset(r.keys()) for r in rows)
    assert all(r["is_real"] is True for r in rows)

    payload = {"provenance": {"recent_real_context": rows}}
    serialized = json.dumps(payload)
    decoded = json.loads(serialized)
    assert decoded["provenance"]["recent_real_context"] == rows

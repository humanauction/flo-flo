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
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
    )

    Base.metadata.create_all(bind=engine)

    # Redirect tool module to test DB session factory
    monkeypatch.setattr(db_tools, "SessionLocal", TestingSessionLocal)

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

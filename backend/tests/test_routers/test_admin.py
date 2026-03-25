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

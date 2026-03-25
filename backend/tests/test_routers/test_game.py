def test_get_headline_empty_returns_404(client):
    res = client.get("/api/game/headline")
    assert res.status_code == 404
    assert res.json()["detail"] == "No headlines available"


def test_guess_nonexistent_returns_404(client):
    res = client.post(
        "/api/game/guess",
        json={"headline_id": 9999, "guess": True},
    )
    assert res.status_code == 404
    assert res.json()["detail"] == "Headline not found"


def test_get_headline_and_guess_flow(client):
    # Insert one headline via admin endpoint
    add = client.post(
        "/api/admin/headline",
        json={
            "text": "Florida man balances alligator on paddleboard",
            "is_real": True,
            "source_url": "https://example.com/story",
        },
    )
    assert add.status_code == 200
    headline_id = add.json()["id"]

    # Fetch random game headline
    get_h = client.get("/api/game/headline")
    assert get_h.status_code == 200
    payload = get_h.json()
    assert "id" in payload
    assert "text" in payload
    assert "is_real" not in payload

    # Guess on known id and verify response shape
    guess = client.post(
        "/api/game/guess",
        json={"headline_id": headline_id, "guess": True},
    )
    assert guess.status_code == 200
    g = guess.json()
    assert g["correct"] is True
    assert g["was_real"] is True
    assert g["source_url"] == "https://example.com/story"

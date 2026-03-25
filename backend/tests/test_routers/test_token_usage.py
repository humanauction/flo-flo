def test_root_route(client):
    response = client.get("/")
    assert response.status_code == 200
    body = response.json()
    assert body["message"] == "Florida Man API"


def test_token_usage_stats_route(client):
    response = client.get("/api/token-usage/stats")
    assert response.status_code == 200
    body = response.json()
    assert "total_tokens" in body
    assert "total_requests" in body

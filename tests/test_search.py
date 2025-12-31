import pytest
from fastapi.testclient import TestClient

class TestSearch:
    def test_search_post(self, client: TestClient, sample_book):
        response = client.post("/search?query=Test&limit=5")
        assert response.status_code == 200
        assert "query" in response.json()
        assert "results" in response.json()

    def test_search_get(self, client: TestClient, sample_book):
        response = client.get("/search?query=Test&limit=5")
        assert response.status_code == 200
        assert response.json()["query"] == "Test"
        assert "results" in response.json()

    def test_search_empty_query(self, client: TestClient):
        response = client.get("/search?query=&limit=5")
        assert response.status_code == 200
        assert response.json()["query"] == ""

    def test_reindex_all(self, client: TestClient, sample_book):
        response = client.post("/reindex-all")
        assert response.status_code == 200
        assert "Reindexed" in response.json()["message"]

    def test_debug_embeddings(self, client: TestClient):
        response = client.get("/debug/embeddings")
        assert response.status_code == 200
        assert "total_books_indexed" in response.json()
        assert "book_ids" in response.json()

class TestRecommendations:
    def test_recommendations(self, client: TestClient, sample_book):
        response = client.get("/recommendations?genre=Fiction")
        assert response.status_code == 200

class TestSummaryGeneration:
    def test_generate_summary_from_content(self, client: TestClient):
        response = client.post("/generate-summary", json={
            "content": "This is a test book content for summary generation."
        })
        assert response.status_code == 200
        assert "summary" in response.json()
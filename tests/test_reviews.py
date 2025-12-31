import pytest
from fastapi.testclient import TestClient

class TestReviews:
    def test_add_review(self, client: TestClient, sample_book):
        response = client.post(f"/books/{sample_book.id}/reviews", json={
            "user_id": 1,
            "review_text": "Great book!",
            "rating": 4.5
        })
        assert response.status_code == 201
        assert response.json()["review_text"] == "Great book!"
        assert response.json()["rating"] == 4.5

    def test_add_review_book_not_found(self, client: TestClient):
        response = client.post("/books/999/reviews", json={
            "user_id": 1,
            "review_text": "Great book!",
            "rating": 4.5
        })
        assert response.status_code == 404
        assert response.json()["detail"] == "Book not found"

    def test_get_reviews(self, client: TestClient, sample_book):
        # First add a review
        client.post(f"/books/{sample_book.id}/reviews", json={
            "user_id": 1,
            "review_text": "Great book!",
            "rating": 4.5
        })
        
        # Then get reviews
        response = client.get(f"/books/{sample_book.id}/reviews")
        assert response.status_code == 200
        assert len(response.json()) >= 1
        assert response.json()[0]["review_text"] == "Great book!"

    def test_get_reviews_book_not_found(self, client: TestClient):
        response = client.get("/books/999/reviews")
        assert response.status_code == 404
        assert response.json()["detail"] == "Book not found"

    def test_book_summary(self, client: TestClient, sample_book):
        # First add a review
        client.post(f"/books/{sample_book.id}/reviews", json={
            "user_id": 1,
            "review_text": "Great book!",
            "rating": 4.5
        })
        
        # Then get summary
        response = client.get(f"/books/{sample_book.id}/summary")
        assert response.status_code == 200
        assert "rating" in response.json()
        assert "review_summary" in response.json()
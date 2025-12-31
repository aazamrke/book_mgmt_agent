import pytest
from fastapi.testclient import TestClient

class TestBooks:
    def test_create_book(self, client: TestClient):
        response = client.post("/books", json={
            "title": "Test Book",
            "author": "Test Author",
            "genre": "Fiction",
            "year_published": 2023
        })
        assert response.status_code == 200
        assert response.json()["title"] == "Test Book"
        assert response.json()["author"] == "Test Author"

    def test_get_books(self, client: TestClient, sample_book):
        response = client.get("/books")
        assert response.status_code == 200
        assert len(response.json()) >= 1
        assert response.json()[0]["title"] == "Test Book"

    def test_get_book_by_id(self, client: TestClient, sample_book):
        response = client.get(f"/books/{sample_book.id}")
        assert response.status_code == 200
        assert response.json()["id"] == sample_book.id
        assert response.json()["title"] == "Test Book"

    def test_get_book_not_found(self, client: TestClient):
        response = client.get("/books/999")
        assert response.status_code == 404
        assert response.json()["detail"] == "Book not found"

    def test_update_book(self, client: TestClient, sample_book, auth_headers):
        response = client.put(f"/books/{sample_book.id}", 
            json={"title": "Updated Book"}, 
            headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json()["title"] == "Updated Book"

    def test_update_book_unauthorized(self, client: TestClient, sample_book):
        response = client.put(f"/books/{sample_book.id}", 
            json={"title": "Updated Book"}
        )
        assert response.status_code == 401

    def test_delete_book(self, client: TestClient, sample_book, auth_headers):
        response = client.delete(f"/books/{sample_book.id}", headers=auth_headers)
        assert response.status_code == 204

    def test_delete_book_unauthorized(self, client: TestClient, sample_book):
        response = client.delete(f"/books/{sample_book.id}")
        assert response.status_code == 401

    def test_generate_summary(self, client: TestClient, sample_book, auth_headers):
        response = client.post(f"/books/{sample_book.id}/generate-summary", 
            headers=auth_headers
        )
        assert response.status_code == 200
        assert "summary" in response.json()

    def test_reindex_book(self, client: TestClient, sample_book):
        response = client.post(f"/books/{sample_book.id}/reindex")
        assert response.status_code == 200
        assert "reindexed successfully" in response.json()["message"]
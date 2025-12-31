import pytest
from fastapi.testclient import TestClient
from io import BytesIO

class TestDocuments:
    def test_upload_document(self, client: TestClient):
        file_content = b"This is a test document"
        files = {"file": ("test.txt", BytesIO(file_content), "text/plain")}
        
        response = client.post("/documents/upload", files=files)
        assert response.status_code == 200
        assert response.json()["message"] == "Document uploaded"
        assert "document_id" in response.json()

    def test_list_documents(self, client: TestClient):
        # First upload a document
        file_content = b"This is a test document"
        files = {"file": ("test.txt", BytesIO(file_content), "text/plain")}
        client.post("/documents/upload", files=files)
        
        # Then list documents
        response = client.get("/documents/")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        assert len(response.json()) >= 1

    def test_delete_document(self, client: TestClient, auth_headers):
        # First upload a document
        file_content = b"This is a test document"
        files = {"file": ("test.txt", BytesIO(file_content), "text/plain")}
        upload_response = client.post("/documents/upload", files=files)
        document_id = upload_response.json()["document_id"]
        
        # Then delete it
        response = client.delete(f"/documents/{document_id}", headers=auth_headers)
        assert response.status_code == 204

    def test_delete_document_unauthorized(self, client: TestClient):
        response = client.delete("/documents/1")
        assert response.status_code == 401

    def test_delete_document_not_found(self, client: TestClient, auth_headers):
        response = client.delete("/documents/999", headers=auth_headers)
        assert response.status_code == 404
        assert response.json()["detail"] == "Document not found"
import pytest
from fastapi.testclient import TestClient

class TestAuth:
    def test_signup(self, client: TestClient):
        response = client.post("/auth/signup", json={
            "username": "testuser",
            "password": "testpass"
        })
        assert response.status_code == 200
        assert response.json()["message"] == "User registered successfully"

    def test_create_admin(self, client: TestClient):
        response = client.post("/auth/create-admin", json={
            "username": "admin",
            "password": "admin123"
        })
        assert response.status_code == 200
        assert response.json()["message"] == "Admin user created successfully"

    def test_login_success(self, client: TestClient):
        # First create user
        client.post("/auth/signup", json={
            "username": "testuser",
            "password": "testpass"
        })
        
        # Then login
        response = client.post("/auth/login", json={
            "username": "testuser",
            "password": "testpass"
        })
        assert response.status_code == 200
        assert "access_token" in response.json()
        assert response.json()["token_type"] == "bearer"

    def test_login_invalid_credentials(self, client: TestClient):
        response = client.post("/auth/login", json={
            "username": "nonexistent",
            "password": "wrongpass"
        })
        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid credentials"

    def test_logout(self, client: TestClient):
        response = client.post("/auth/logout")
        assert response.status_code == 200
        assert "Logout handled on client side" in response.json()["message"]
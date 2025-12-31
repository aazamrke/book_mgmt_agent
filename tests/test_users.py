import pytest
from fastapi.testclient import TestClient

class TestUserManagement:
    def test_create_user(self, client: TestClient, auth_headers):
        response = client.post("/admin/users/", 
            json={
                "username": "newuser",
                "password": "password123",
                "role_names": []
            },
            headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json()["message"] == "User created successfully"

    def test_create_user_unauthorized(self, client: TestClient):
        response = client.post("/admin/users/", json={
            "username": "newuser",
            "password": "password123"
        })
        assert response.status_code == 401

    def test_list_users(self, client: TestClient, auth_headers, admin_user):
        response = client.get("/admin/users/", headers=auth_headers)
        assert response.status_code == 200
        assert len(response.json()) >= 1

    def test_list_users_unauthorized(self, client: TestClient):
        response = client.get("/admin/users/")
        assert response.status_code == 401

    def test_update_user(self, client: TestClient, auth_headers, admin_user):
        response = client.put(f"/admin/users/{admin_user.id}",
            json={"username": "updated_admin"},
            headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json()["message"] == "User updated successfully"

    def test_delete_user(self, client: TestClient, auth_headers):
        # First create a user to delete
        create_response = client.post("/admin/users/",
            json={
                "username": "deleteuser",
                "password": "password123"
            },
            headers=auth_headers
        )
        user_id = create_response.json()["user_id"]
        
        # Then delete it
        response = client.delete(f"/admin/users/{user_id}", headers=auth_headers)
        assert response.status_code == 204

    def test_list_roles(self, client: TestClient, auth_headers):
        response = client.get("/admin/users/roles", headers=auth_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_create_role(self, client: TestClient, auth_headers):
        response = client.post("/admin/users/roles?role_name=editor", 
            headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json()["message"] == "Role created successfully"
"""Authentication and RBAC security tests."""

import unittest
from datetime import timedelta

from fastapi.testclient import TestClient

from app.core.security import create_access_token
from app.main import app

client = TestClient(app)


def _token(username: str, role: str) -> str:
    return create_access_token({"sub": username, "role": role})


class AuthRBACTests(unittest.TestCase):
    def test_public_menu_without_auth(self):
        response = client.get("/api/menu")
        self.assertEqual(response.status_code, 200)

    def test_dashboard_requires_auth(self):
        response = client.get("/api/dashboard/stats")
        self.assertEqual(response.status_code, 401)

    def test_dashboard_rejects_non_admin_role(self):
        login = client.post(
            "/api/auth/login",
            json={"username": "driver1", "password": "driver123"},
        )
        self.assertEqual(login.status_code, 200)
        token = login.json()["access_token"]
        response = client.get(
            "/api/dashboard/stats",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(response.status_code, 403)

    def test_dashboard_allows_admin_with_valid_login(self):
        login = client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "admin123"},
        )
        self.assertEqual(login.status_code, 200)
        token = login.json()["access_token"]
        response = client.get(
            "/api/dashboard/stats",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(response.status_code, 200)

    def test_invalid_token_rejected(self):
        response = client.get(
            "/api/orders",
            headers={"Authorization": "Bearer not.a.valid.token"},
        )
        self.assertEqual(response.status_code, 401)

    def test_expired_token_rejected(self):
        expired = create_access_token(
            {"sub": "admin", "role": "admin"},
            expires_delta=timedelta(seconds=-60),
        )
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {expired}"},
        )
        self.assertEqual(response.status_code, 401)

    def test_tampered_role_in_token_rejected_for_admin_orders(self):
        """Token role claim is overridden by database role during authentication."""
        login = client.post(
            "/api/auth/login",
            json={"username": "driver1", "password": "driver123"},
        )
        self.assertEqual(login.status_code, 200)
        forged = create_access_token({"sub": "driver1", "role": "admin"})
        response = client.get(
            "/api/orders",
            headers={"Authorization": f"Bearer {forged}"},
        )
        self.assertEqual(response.status_code, 403)

    def test_admin_orders_list_requires_admin(self):
        login = client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "admin123"},
        )
        token = login.json()["access_token"]
        response = client.get(
            "/api/orders",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(response.status_code, 200)

    def test_login_accepts_normalized_username(self):
        """Usernames are matched case-insensitively without spaces."""
        login = client.post(
            "/api/auth/login",
            json={"username": "ADMIN3", "password": "admin123"},
        )
        self.assertEqual(login.status_code, 200)

    def test_menu_mutations_require_admin(self):
        login = client.post(
            "/api/auth/login",
            json={"username": "driver1", "password": "driver123"},
        )
        token = login.json()["access_token"]
        response = client.post(
            "/api/menu",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": "Blocked Item",
                "category": "Starters",
                "price": 99,
                "available": True,
            },
        )
        self.assertEqual(response.status_code, 403)


if __name__ == "__main__":
    unittest.main()

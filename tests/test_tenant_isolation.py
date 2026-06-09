"""Multi-tenant isolation and cross-restaurant access tests."""

import unittest

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _login(username: str, password: str) -> str:
    response = client.post("/api/auth/login", json={"username": username, "password": password})
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


class TenantIsolationTests(unittest.TestCase):
    def test_admin_cannot_query_other_restaurant_partners(self):
        token = _login("admin", "admin123")
        response = client.get(
            "/api/delivery/partners",
            params={"restaurant_id": 2},
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(response.status_code, 403)

    def test_admin_can_query_own_restaurant_partners(self):
        token = _login("admin", "admin123")
        response = client.get(
            "/api/delivery/partners",
            params={"restaurant_id": 1},
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(response.status_code, 200)

    def test_admin2_cannot_query_restaurant_one_partners(self):
        token = _login("admin2", "admin123")
        response = client.get(
            "/api/delivery/partners",
            params={"restaurant_id": 1},
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(response.status_code, 403)

    def test_admin_orders_scoped_to_assigned_restaurant(self):
        token = _login("admin", "admin123")
        response = client.get(
            "/api/orders",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(response.status_code, 200)
        for item in response.json().get("items", []):
            self.assertTrue(item["order_id"].startswith("ORD-"))

    def test_superadmin_cannot_use_admin_dashboard(self):
        token = _login("superadmin", "superadmin123")
        response = client.get(
            "/api/dashboard/stats",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(response.status_code, 403)

    def test_admin_cannot_respond_to_other_restaurant_review(self):
        token = _login("admin", "admin123")
        response = client.put(
            "/api/reviews/1/respond",
            headers={"Authorization": f"Bearer {token}"},
            json={"owner_response": "Thanks for visiting!"},
        )
        self.assertEqual(response.status_code, 403)

    def test_admin2_can_respond_to_own_restaurant_review(self):
        token = _login("admin2", "admin123")
        response = client.put(
            "/api/reviews/1/respond",
            headers={"Authorization": f"Bearer {token}"},
            json={"owner_response": "Thank you for your kind words!"},
        )
        self.assertEqual(response.status_code, 200)

    def test_admin_cannot_update_other_restaurant(self):
        token = _login("admin", "admin123")
        response = client.put(
            "/api/restaurants/2",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "Hijacked Restaurant"},
        )
        self.assertEqual(response.status_code, 403)

    def test_unauthenticated_admin_endpoint_returns_401(self):
        response = client.get("/api/orders")
        self.assertEqual(response.status_code, 401)

    def test_superadmin_can_map_admins_to_restaurant(self):
        token = _login("superadmin", "superadmin123")
        response = client.put(
            "/api/restaurants/1/admins",
            headers={"Authorization": f"Bearer {token}"},
            json={"admin_ids": [1]},
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(1, response.json()["mapped_admin_ids"])

    def test_restaurant_admin_cannot_map_admins(self):
        token = _login("admin", "admin123")
        response = client.get(
            "/api/restaurants/1/admins",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(response.status_code, 403)


if __name__ == "__main__":
    unittest.main()

"""Random 10-digit tenant id generation tests."""

import unittest

from app.utils.tenant_id import generate_tenant_id


class TenantIdTests(unittest.TestCase):
    def test_generates_ten_digit_id(self):
        new_id = generate_tenant_id({1, 2, 3})
        self.assertGreaterEqual(new_id, 1_000_000_000)
        self.assertLessEqual(new_id, 9_999_999_999)
        self.assertEqual(len(str(new_id)), 10)

    def test_avoids_collisions(self):
        used = {generate_tenant_id(set()) for _ in range(20)}
        self.assertEqual(len(used), 20)


if __name__ == "__main__":
    unittest.main()

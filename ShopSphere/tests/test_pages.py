import unittest
from backend.app import create_app

class ShopSpherePagesTest(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.client = self.app.test_client()

    def test_all_pages_render_200(self):
        routes = [
            "/",
            "/products",
            "/products/PRD1001",
            "/cart",
            "/checkout",
            "/order-confirmation/ORD1001",
            "/orders",
            "/orders/ORD1001",
            "/orders/ORD1001/track",
            "/returns",
            "/profile",
            "/addresses",
            "/support",
            "/login",
            "/register",
            "/admin",
            "/admin/products",
            "/admin/orders",
            "/admin/customers",
            "/admin/returns"
        ]

        for route in routes:
            res = self.client.get(route)
            self.assertEqual(res.status_code, 200, f"Route {route} failed with status {res.status_code}")
            self.assertIn(b"Shop", res.data)

if __name__ == "__main__":
    unittest.main()


import unittest
from backend.app import create_app
from backend.tools.registry import ToolRegistry
from backend.services.order_service import OrderService
from backend.services.product_service import ProductService

class ShopSphereTestSuite(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.client = self.app.test_client()
        self.client.testing = True

    def test_01_products_api(self):
        """Test product listing, search, and category retrieval."""
        res = self.client.get("/api/products")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])
        self.assertGreaterEqual(data["total"], 50)

        # Global search
        res = self.client.get("/api/products/search?q=wireless")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])
        self.assertGreater(len(data["products"]), 0)

        # Categories
        res = self.client.get("/api/categories")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertGreaterEqual(len(data["categories"]), 5)

    def test_02_auth_me_and_demo_switch(self):
        """Test session authentication and demo switcher."""
        res = self.client.get("/api/auth/me")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["authenticated"])

        # Switch to Priya Patel (CUS1002)
        res = self.client.post("/api/auth/demo-switch", json={"customer_id": "CUS1002"})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["customer"]["customer_id"], "CUS1002")

    def test_03_cart_operations(self):
        """Test adding item to cart and calculating totals."""
        res = self.client.post("/api/cart/add", json={"product_id": "PRD1013", "quantity": 1})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])
        self.assertGreaterEqual(data["cart"]["total_items"], 1)

    def test_04_customer_orders_isolation(self):
        """Test customer orders retrieval."""
        res = self.client.get("/api/orders")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])
        self.assertIsInstance(data["orders"], list)

    def test_05_tool_registry_and_policy_interception(self):
        """Verify all 23 tools are registered, and test AegisAI propose-decide-execute cycle."""
        tools = ToolRegistry.get_tool_metadata()
        self.assertEqual(len(tools), 23, "All 23 required tools must be registered in the Tool Registry.")

        # Test search_products (LOW risk -> ALLOW)
        res = ToolRegistry.execute_tool(
            tool_name="search_products",
            arguments={"query": "laptop"},
            context={"customer_id": "CUS1001"}
        )
        self.assertTrue(res["executed"])
        self.assertEqual(res["policy_service"]["decision"], "ALLOW")

        # Test process_refund with verified customer and amount <= 500 (ALLOW)
        res = ToolRegistry.execute_tool(
            tool_name="process_refund",
            arguments={"order_id": "ORD1001", "amount": 400},
            context={"customer_id": "CUS1001", "is_verified": True}
        )
        self.assertEqual(res["policy_service"]["decision"], "ALLOW")

        # Test process_refund with excessive amount > 500 (BLOCK)
        res = ToolRegistry.execute_tool(
            tool_name="process_refund",
            arguments={"order_id": "ORD1001", "amount": 999999},
            context={"customer_id": "CUS1001", "is_verified": True}
        )
        self.assertEqual(res["policy_service"]["decision"], "BLOCK")
        self.assertFalse(res["executed"])

        # Test delete_customer_account (CRITICAL risk -> ESCALATE)
        res = ToolRegistry.execute_tool(
            tool_name="delete_customer_account",
            arguments={"customer_id": "CUS1001"},
            context={"customer_id": "CUS1001"}
        )
        self.assertEqual(res["policy_service"]["decision"], "ESCALATE")
        self.assertFalse(res["executed"])

    def test_06_chatbot_endpoint_queries(self):
        """Test required queries against /api/chat."""
        queries = [
            "Show me laptops under ₹50,000.",
            "Where is my order?",
            "What is the status of ORD1001?",
            "Can I return this product?",
            "I want a refund.",
            "Cancel my order.",
            "Change my delivery address.",
            "Show my recent orders.",
            "How much did I pay for my order?",
            "Is this product in stock?"
        ]

        for q in queries:
            res = self.client.post("/api/chat", json={"message": q})
            self.assertEqual(res.status_code, 200, f"Query failed: {q}")
            data = res.get_json()
            self.assertTrue(data["success"])
            self.assertIn("reply", data)
            self.assertIn("developer_metadata", data)
            self.assertIsNotNone(data["developer_metadata"])
            self.assertIn("policy_service", data["developer_metadata"])

if __name__ == "__main__":
    unittest.main()


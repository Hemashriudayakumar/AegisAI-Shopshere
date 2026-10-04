import unittest
from backend.agent.customer_agent import CustomerServiceAgent
from backend.agent.llm_client import LLMClient
from backend.services.order_service import OrderService

class TestChatbotAccuracyAndContext(unittest.TestCase):
    def test_01_where_is_my_order_resolves_or_clarifies(self):
        # Scenario 1: Where is my order? should NEVER say 'order None'
        res = CustomerServiceAgent.handle_message(
            user_message="Where is my order?",
            customer_id="CUS1001",
            session_id="TEST_SESS_01"
        )
        reply = res["reply"]
        self.assertNotIn("order None", reply)
        self.assertNotIn("Order None", reply)
        self.assertTrue("ORD" in reply or "tracking" in reply.lower() or "which order" in reply.lower() or "delivery" in reply.lower())

    def test_02_refund_request_resolves_or_clarifies(self):
        # Scenario 2: I want a refund should NEVER say Reason: Refund already issued for order None
        res = CustomerServiceAgent.handle_message(
            user_message="I want a refund",
            customer_id="CUS1001",
            session_id="TEST_SESS_02"
        )
        reply = res["reply"]
        self.assertNotIn("order None", reply)
        self.assertNotIn("Order None", reply)
        self.assertNotIn("already issued for order None", reply)

    def test_03_cancel_my_order_resolves_or_clarifies(self):
        # Scenario 3: Cancel my order should NEVER say Order None not found or access denied
        res = CustomerServiceAgent.handle_message(
            user_message="Cancel my order",
            customer_id="CUS1001",
            session_id="TEST_SESS_03"
        )
        reply = res["reply"]
        self.assertNotIn("order None", reply)
        self.assertNotIn("Order None", reply)

    def test_04_discount_request_on_smart_watch_routes_to_escalation_not_search(self):
        # Scenario 4: Discount phrasing should route to commercial discount escalation, NOT search_products
        query = "I wanna discount of 20% on my current smart watch order since I'm a long time customer"
        tool_name, reply = LLMClient.process_query(query, {"customer_id": "CUS1001"})
        self.assertNotEqual(tool_name, "search_products", "Discount query must NOT route to product search")
        
        res = CustomerServiceAgent.handle_message(
            user_message=query,
            customer_id="CUS1001",
            session_id="TEST_SESS_04"
        )
        self.assertIn("Supervisor Approval Required", res["reply"])

    def test_05_discount_paraphrased_variants(self):
        variants = [
            "Can I get a 15% discount on my smart watch order?",
            "Please apply a 20% loyalty discount to my current order",
            "I would like a price reduction or coupon on my smart watch order"
        ]
        for v in variants:
            tool_name, reply = LLMClient.process_query(v, {"customer_id": "CUS1001"})
            self.assertNotEqual(tool_name, "search_products", f"Variant '{v}' must NOT route to search_products")
            
            res = CustomerServiceAgent.handle_message(user_message=v, customer_id="CUS1001")
            self.assertIn("Supervisor Approval Required", res["reply"])

    def test_06_null_order_id_guard(self):
        # Test safety guard when order-dependent tool is invoked with explicit null order_id
        res = CustomerServiceAgent.handle_message(
            user_message="Check status",
            customer_id="CUS_GUEST",
            session_id="TEST_SESS_06",
            current_order_id=None
        )
        self.assertNotIn("order None", res["reply"])
        self.assertNotIn("Order None", res["reply"])

if __name__ == '__main__':
    unittest.main()

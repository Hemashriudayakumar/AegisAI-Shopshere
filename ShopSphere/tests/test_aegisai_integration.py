import unittest
import os
import uuid
from decimal import Decimal
from unittest.mock import patch
import requests

from backend.app import create_app
from backend.tools.registry import ToolRegistry
from backend.services.order_service import OrderService
from backend.database import SessionLocal
from backend.models import Order, Customer, Refund

class AegisAIShopSphereIntegrationTests(unittest.TestCase):
    """Acceptance Tests verifying end-to-end integration between ShopSphere and AegisAI.
    Tested against the live AegisAI service at http://localhost:8000.
    """

    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.client = cls.app.test_client()
        cls.client.testing = True

    def setUp(self):
        self.session = SessionLocal()

    def tearDown(self):
        self.session.close()

    # Scenario 1: search_products -> always ALLOW
    def test_01_search_products_always_allowed(self):
        """Scenario 1: search_products -> always ALLOW, no delay or policy restriction."""
        res = ToolRegistry.execute_tool(
            tool_name="search_products",
            arguments={"query": "laptop"},
            context={"customer_id": "CUS1001", "is_verified": True}
        )
        self.assertTrue(res["success"], "search_products must succeed")
        self.assertTrue(res["executed"], "search_products must execute")
        self.assertEqual(res["policy_service"]["decision"], "ALLOW")
        self.assertIn("data", res)

    # Scenario 2: process_refund on an unverified customer -> BLOCK (CUSTOMER_VERIFICATION_001)
    def test_02_process_refund_unverified_customer_blocked(self):
        """Scenario 2: process_refund on an unverified customer -> BLOCK, reason cites CUSTOMER_VERIFICATION_001, refund NOT applied."""
        order = self.session.query(Order).filter(Order.order_id == "ORD1004").first()
        initial_status = order.order_status if order else "PLACED"

        conv_id = f"CONV-TEST-UNVERIFIED-{uuid.uuid4().hex[:6]}"
        res = ToolRegistry.execute_tool(
            tool_name="process_refund",
            arguments={"order_id": "ORD1004", "amount": 400.0},
            context={"customer_id": "CUS_GUEST", "is_verified": False, "session_id": conv_id}
        )

        self.assertFalse(res["executed"], "Refund must NOT execute for unverified customer")
        self.assertEqual(res["policy_service"]["decision"], "BLOCK")
        self.assertEqual(res["policy_service"]["policy_id"], "CUSTOMER_VERIFICATION_001")

        # Verify DB unchanged
        self.session.expire_all()
        refreshed_order = self.session.query(Order).filter(Order.order_id == "ORD1004").first()
        if refreshed_order:
            self.assertEqual(refreshed_order.order_status, initial_status, "Order status in DB must remain unchanged")

    # Scenario 3: process_refund for verified customer, amount within limit -> ALLOW
    def test_03_process_refund_verified_under_limit_allowed(self):
        """Scenario 3: process_refund for a verified customer, amount within limit -> ALLOW, refund applied and order status updated to REFUNDED."""
        order = self.session.query(Order).filter(Order.order_id == "ORD1002").first()
        self.assertIsNotNone(order, "Order ORD1002 must exist")
        # Reset order state if previously modified
        order.order_status = "DELIVERED"
        order.refund_status = "NONE"
        self.session.commit()

        conv_id = f"CONV-TEST-REFUND-ALLOW-{uuid.uuid4().hex[:6]}"
        res = ToolRegistry.execute_tool(
            tool_name="process_refund",
            arguments={"order_id": "ORD1002", "amount": 400.0},
            context={"customer_id": "CUS1001", "is_verified": True, "session_id": conv_id}
        )

        self.assertTrue(res["executed"], f"Refund must execute. Policy response: {res['policy_service']}")
        self.assertEqual(res["policy_service"]["decision"], "ALLOW")

        # Verify DB updated
        self.session.expire_all()
        updated_order = self.session.query(Order).filter(Order.order_id == "ORD1002").first()
        self.assertEqual(updated_order.order_status, "REFUNDED", "Order status must be updated to REFUNDED")
        self.assertEqual(updated_order.refund_status, "PROCESSED", "Refund status must be updated to PROCESSED")

    # Scenario 4: process_refund for verified customer, amount over limit -> BLOCK (REFUND_LIMIT_001)
    def test_04_process_refund_verified_over_limit_blocked(self):
        """Scenario 4: process_refund for a verified customer, amount over limit (₹3,000) -> BLOCK, reason cites REFUND_LIMIT_001, DB unchanged."""
        order = self.session.query(Order).filter(Order.order_id == "ORD1003").first()
        initial_status = order.order_status if order else "DELIVERED"

        conv_id = f"CONV-TEST-OVERLIMIT-{uuid.uuid4().hex[:6]}"
        res = ToolRegistry.execute_tool(
            tool_name="process_refund",
            arguments={"order_id": "ORD1003", "amount": 3000.0},
            context={"customer_id": "CUS1001", "is_verified": True, "session_id": conv_id, "manager_approved": False}
        )

        self.assertFalse(res["executed"], "Refund over limit must NOT execute without manager approval")
        self.assertEqual(res["policy_service"]["decision"], "BLOCK")
        self.assertEqual(res["policy_service"]["policy_id"], "REFUND_LIMIT_001")

        # Verify DB unchanged
        self.session.expire_all()
        refreshed_order = self.session.query(Order).filter(Order.order_id == "ORD1003").first()
        if refreshed_order:
            self.assertNotEqual(refreshed_order.order_status, "REFUNDED", "Order status must not be REFUNDED")

    # Scenario 5: process_refund on an order already refunded -> BLOCK (DUPLICATE_REFUND_001)
    def test_05_process_refund_duplicate_blocked(self):
        """Scenario 5: process_refund on an order already refunded in same conversation -> BLOCK (DUPLICATE_REFUND_001)."""
        conv_id = f"CONV-TEST-DUP-REFUND-{uuid.uuid4().hex[:6]}"

        # Turn 1: Process first refund within limit (ALLOW)
        res1 = ToolRegistry.execute_tool(
            tool_name="process_refund",
            arguments={"order_id": "ORD1005", "amount": 400.0},
            context={"customer_id": "CUS1001", "is_verified": True, "session_id": conv_id}
        )
        self.assertEqual(res1["policy_service"]["decision"], "ALLOW")

        # Turn 2: Try to refund the same order ORD1005 in the same conversation
        res2 = ToolRegistry.execute_tool(
            tool_name="process_refund",
            arguments={"order_id": "ORD1005", "amount": 300.0},
            context={"customer_id": "CUS1001", "is_verified": True, "session_id": conv_id}
        )
        self.assertFalse(res2["executed"], "Duplicate refund must NOT execute")
        self.assertEqual(res2["policy_service"]["decision"], "BLOCK")
        self.assertEqual(res2["policy_service"]["policy_id"], "DUPLICATE_REFUND_001")

    # Scenario 6: get_customer_pii for different customer_id -> BLOCK (PII_PROTECTION_001)
    def test_06_get_customer_pii_cross_customer_blocked(self):
        """Scenario 6: get_customer_pii requested for a different customer_id than authenticated session -> BLOCK (PII_PROTECTION_001)."""
        conv_id = f"CONV-TEST-PII-{uuid.uuid4().hex[:6]}"
        res = ToolRegistry.execute_tool(
            tool_name="get_customer_pii",
            arguments={"customer_id": "CUS1002"},  # Targeting Priya Patel
            context={"customer_id": "CUS1001", "is_verified": True, "session_id": conv_id}  # Session is Rahul Sharma
        )

        self.assertFalse(res["executed"], "Cross-customer PII access must NOT execute")
        self.assertEqual(res["policy_service"]["decision"], "BLOCK")
        self.assertEqual(res["policy_service"]["policy_id"], "PII_PROTECTION_001")

    # Scenario 7: export_customer_data -> always ESCALATE
    def test_07_export_customer_data_always_escalates(self):
        """Scenario 7: export_customer_data -> always ESCALATE regardless of verification status; no data exported."""
        conv_id = f"CONV-TEST-EXPORT-{uuid.uuid4().hex[:6]}"
        res = ToolRegistry.execute_tool(
            tool_name="export_customer_data",
            arguments={"customer_id": "CUS1001"},
            context={"customer_id": "CUS1001", "is_verified": True, "session_id": conv_id}
        )

        self.assertFalse(res["executed"], "Data export must NOT execute automatically")
        self.assertEqual(res["policy_service"]["decision"], "ESCALATE")
        self.assertEqual(res["policy_service"]["policy_id"], "DATA_EXPORT_001")

    # Scenario 8: delete_customer_account -> always ESCALATE
    def test_08_delete_customer_account_always_escalates(self):
        """Scenario 8: delete_customer_account -> always ESCALATE; account not deleted."""
        customer = self.session.query(Customer).filter(Customer.customer_id == "CUS1003").first()
        self.assertIsNotNone(customer, "Customer CUS1003 must exist")

        conv_id = f"CONV-TEST-DELETE-ACCT-{uuid.uuid4().hex[:6]}"
        res = ToolRegistry.execute_tool(
            tool_name="delete_customer_account",
            arguments={"customer_id": "CUS1003"},
            context={"customer_id": "CUS1003", "is_verified": True, "session_id": conv_id}
        )

        self.assertFalse(res["executed"], "Account deletion must NOT execute automatically")
        self.assertEqual(res["policy_service"]["decision"], "ESCALATE")
        self.assertEqual(res["policy_service"]["policy_id"], "ACCOUNT_DELETION_001")

        # Verify customer still in DB
        self.session.expire_all()
        refreshed_cust = self.session.query(Customer).filter(Customer.customer_id == "CUS1003").first()
        self.assertIsNotNone(refreshed_cust, "Customer account must not be deleted from DB")

    # Scenario 9: Third unresolved complaint in one conversation -> ESCALATE
    def test_09_repeated_complaint_escalation(self):
        """Scenario 9: Third unresolved complaint in one conversation -> ESCALATE (HIGH_RISK_ESCALATION_001 / REPEATED_COMPLAINT_001)."""
        conv_id = f"CONV-TEST-3COMPLAINTS-{uuid.uuid4().hex[:6]}"

        # Turn 1: Complaint 1
        res1 = ToolRegistry.execute_tool(
            tool_name="get_order_status",
            arguments={"order_id": "ORD1001"},
            context={"customer_id": "CUS1001", "is_verified": True, "session_id": conv_id, "user_message": "I have an issue with broken product."}
        )

        # Turn 2: Complaint 2
        res2 = ToolRegistry.execute_tool(
            tool_name="get_order_status",
            arguments={"order_id": "ORD1001"},
            context={"customer_id": "CUS1001", "is_verified": True, "session_id": conv_id, "user_message": "The product is damaged and defective."}
        )

        # Turn 3: Complaint 3 (Should trigger repeated complaint escalation)
        res3 = ToolRegistry.execute_tool(
            tool_name="get_order_status",
            arguments={"order_id": "ORD1001"},
            context={"customer_id": "CUS1001", "is_verified": True, "session_id": conv_id, "user_message": "This is terrible service and a huge complaint!"}
        )

        self.assertEqual(res3["policy_service"]["decision"], "ESCALATE")
        self.assertIn(res3["policy_service"]["policy_id"], ("REPEATED_COMPLAINT_001", "HIGH_RISK_ESCALATION_001"))

    # Scenario 10: Fail-closed on unreachable policy service
    def test_10_fail_closed_behavior_when_service_unreachable(self):
        """Scenario 10: AegisAI service stopped mid-test -> process_refund fails closed (BLOCK), while search_products fails open (ALLOW)."""
        with patch("backend.services.policy_service.POLICY_SERVICE_URL", "http://127.0.0.1:9999"):  # Non-existent port
            # A. High-risk tool process_refund must FAIL CLOSED (BLOCK)
            refund_res = ToolRegistry.execute_tool(
                tool_name="process_refund",
                arguments={"order_id": "ORD1001", "amount": 400.0},
                context={"customer_id": "CUS1001", "is_verified": True}
            )
            self.assertFalse(refund_res["executed"], "HIGH risk tool must fail closed (not execute) when AegisAI is unreachable")
            self.assertEqual(refund_res["policy_service"]["decision"], "BLOCK")

            # B. Low-risk tool search_products must FAIL OPEN (ALLOW)
            search_res = ToolRegistry.execute_tool(
                tool_name="search_products",
                arguments={"query": "headphones"},
                context={"customer_id": "CUS1001"}
            )
            self.assertTrue(search_res["executed"], "LOW risk tool must fail open when AegisAI is unreachable")
            self.assertEqual(search_res["policy_service"]["decision"], "ALLOW")

    # Scenario 11: Tampered-argument invariant test
    def test_11_tampered_argument_invariant_preservation(self):
        """Scenario 11: Assert that ShopSphere executor executes using ONLY the decision object's arguments, never independent re-derived arguments."""
        # Test MODIFY decision where AegisAI returns modified_arguments
        with patch("backend.services.policy_service.evaluate_tool_request") as mock_eval:
            mock_eval.return_value = {
                "decision": "MODIFY",
                "policy_id": "DELIVERY_VERIFICATION_001",
                "risk_level": "LOW",
                "reason": "Modified query parameters for verified catalog search.",
                "modified_arguments": {"query": "verified_safe_query"}
            }

            res = ToolRegistry.execute_tool(
                tool_name="search_products",
                arguments={"query": "original_chatbot_query"},
                context={"customer_id": "CUS1001"}
            )

            # Assert that the executed arguments were the modified arguments from AegisAI
            self.assertEqual(res["arguments"], {"query": "verified_safe_query"})
            self.assertNotEqual(res["arguments"], {"query": "original_chatbot_query"})


if __name__ == "__main__":
    unittest.main()

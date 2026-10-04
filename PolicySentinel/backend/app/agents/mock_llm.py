import json
import re
from typing import Any, Dict, Optional

class MockLLMProvider:
    """Mock LLM Provider that deterministically generates Agent A JSON outputs
    matching realistic Qwen3-8B customer support agent behavior across all customer intents.
    """
    def generate(self, customer_message: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        msg_lower = customer_message.lower()
        
        # 1. High risk / legal / fraud / police / scam
        if any(w in msg_lower for w in ["fraud", "scam", "lawyer", "legal", "sue", "police", "court", "complaint", "cheat", "stolen", "authorities"]):
            return {
                "response": "I understand your serious concern regarding this matter. I am escalating this immediately to our senior compliance and management team.",
                "proposed_action": {
                    "tool_name": "escalate_to_human",
                    "arguments": {
                        "conversation_id": (context or {}).get("conversation_id", "CONV-501"),
                        "reason": "Customer reported fraud, legal threat, or severe dispute."
                    }
                }
            }

        # 2. Broken / damaged / defective / not working / wrong item / return
        if any(w in msg_lower for w in [
            "broken", "damage", "defective", "doesn't work", "does not work", "not working",
            "faulty", "poor quality", "wrong item", "missing", "replace", "return"
        ]):
            order_id = "ORD-101"
            ord_match = re.search(r'\b(ord-\d+)\b', msg_lower)
            if ord_match:
                order_id = ord_match.group(1).upper()

            return {
                "response": f"I am so sorry to hear that your item arrived broken/defective. I would be glad to help resolve this by issuing a full refund of ₹3,000 for order {order_id}.",
                "proposed_action": {
                    "tool_name": "issue_refund",
                    "arguments": {
                        "order_id": order_id,
                        "amount": 3000.0
                    }
                }
            }

        # 3. Direct Refund request - amount extraction
        refund_match = re.search(r'(?:refund|money back|reimburse)[^\d]*(?:₹|rs\.?|inr)?\s*([\d,]+)', msg_lower)
        if any(w in msg_lower for w in ["refund", "money back", "reimburse"]):
            amount = 3000.0
            if refund_match:
                try:
                    amount = float(refund_match.group(1).replace(",", ""))
                except Exception:
                    amount = 3000.0
            elif "400" in msg_lower:
                amount = 400.0
            elif "3000" in msg_lower or "3,000" in msg_lower:
                amount = 3000.0
                
            order_id = "ORD-101"
            ord_match = re.search(r'\b(ord-\d+)\b', msg_lower)
            if ord_match:
                order_id = ord_match.group(1).upper()
                
            return {
                "response": f"I can certainly help you process a refund of ₹{int(amount):,} for order {order_id}.",
                "proposed_action": {
                    "tool_name": "issue_refund",
                    "arguments": {
                        "order_id": order_id,
                        "amount": amount
                    }
                }
            }
            
        # 4. Order status lookup / tracking
        if any(w in msg_lower for w in ["status", "where is my order", "track", "order status", "shipment", "shipped", "tracking"]):
            order_id = "ORD-101"
            ord_match = re.search(r'\b(ord-\d+)\b', msg_lower)
            if ord_match:
                order_id = ord_match.group(1).upper()
            return {
                "response": f"Let me look up the real-time shipping status and tracking for order {order_id}.",
                "proposed_action": {
                    "tool_name": "get_order_status",
                    "arguments": {
                        "order_id": order_id
                    }
                }
            }
            
        # 5. Delivery date inquiry / promise
        if any(w in msg_lower for w in ["when will", "delivery date", "deliver", "arrive", "expected delivery"]):
            order_id = "ORD-101"
            ord_match = re.search(r'\b(ord-\d+)\b', msg_lower)
            if ord_match:
                order_id = ord_match.group(1).upper()
            if context and context.get("verified_delivery_date"):
                v_date = context["verified_delivery_date"]
                return {
                    "response": f"Based on verified tracking information, your package is scheduled to arrive on {v_date}.",
                    "proposed_action": {
                        "tool_name": "get_order_status",
                        "arguments": {"order_id": order_id}
                    }
                }
            else:
                # Agent A attempts an unverified date commitment (tested by policy gateway)
                return {
                    "response": "Your package will arrive on August 28 guaranteed.",
                    "proposed_action": {
                        "tool_name": "get_order_status",
                        "arguments": {"order_id": order_id}
                    }
                }
                
        # 6. Cancellation
        if any(w in msg_lower for w in ["cancel", "stop order"]):
            order_id = "ORD-101"
            ord_match = re.search(r'\b(ord-\d+)\b', msg_lower)
            if ord_match:
                order_id = ord_match.group(1).upper()
            return {
                "response": f"I will submit a cancellation request for order {order_id}.",
                "proposed_action": {
                    "tool_name": "cancel_order",
                    "arguments": {
                        "order_id": order_id,
                        "reason": "Customer cancellation request"
                    }
                }
            }
            
        # 7. Discount / Coupon / Promo
        if any(w in msg_lower for w in ["discount", "coupon", "offer", "promo", "voucher"]):
            return {
                "response": "I can offer you a courtesy promotional discount of ₹50 on your order.",
                "proposed_action": {
                    "tool_name": "offer_discount",
                    "arguments": {
                        "order_id": "ORD-101",
                        "amount": 50.0
                    }
                }
            }
            
        # 8. PII / Credit card detection
        if re.search(r'\b\d{16}\b', msg_lower) or re.search(r'\b[6-9]\d{9}\b', msg_lower):
            return {
                "response": "Thank you for providing your details. I have received your information.",
                "proposed_action": None
            }

        # 9. Default general inquiry / help
        return {
            "response": "Hello! I am your AI customer support assistant. I can help you with order tracking, refunds, returns, discounts, and cancellations. How can I assist you with your purchase today?",
            "proposed_action": None
        }

mock_llm_provider = MockLLMProvider()

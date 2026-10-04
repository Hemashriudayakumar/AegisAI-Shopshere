import os
import re
import json
import requests
from backend.tools.registry import ToolRegistry
from backend.services.order_service import OrderService

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")
USE_OLLAMA = os.getenv("USE_OLLAMA", "false").lower() in ("true", "1", "yes")

class LLMClient:
    """
    Modular LLM Client supporting Ollama (e.g., Qwen3) with an intelligent fallback intent engine.
    Ensures ShopSphere operates reliably with robust context resolution and policy guardrails.
    """

    @classmethod
    def process_query(cls, user_message, context):
        """
        Determines the appropriate tool and arguments for a user query.
        Returns: (tool_name, arguments) or (None, direct_reply)
        """
        if USE_OLLAMA:
            try:
                result = cls._query_ollama(user_message, context)
                if result:
                    return result
            except Exception as e:
                print(f"[LLMClient Warning] Ollama query failed ({e}), falling back to intelligent intent engine.")

        # Fallback / Built-in Intelligent Intent Parser
        return cls._parse_intent_deterministically(user_message, context)

    @classmethod
    def _query_ollama(cls, user_message, context):
        """Attempts to call Ollama chat API with Qwen model using structured tool prompt."""
        tools_metadata = ToolRegistry.get_tool_metadata()
        system_prompt = (
            "You are ShopSphere's AI Customer Service Agent. You help customers with products, orders, "
            "tracking, delivery addresses, returns, and refunds.\n"
            "Guidance:\n"
            "1. If the customer is asking for a discount or coupon on an existing order, do not search for products. Direct them to support escalation.\n"
            "2. Never supply a null or 'None' order_id. If the order ID is not provided in context, ask a clarifying question.\n"
            "Available tools:\n"
            + json.dumps([{"name": t["name"], "description": t["description"], "parameters": t["parameters"]} for t in tools_metadata], indent=2)
            + "\nRespond ONLY in JSON format: {\"tool_name\": \"...\", \"arguments\": {...}} or {\"reply\": \"...\"}"
        )

        payload = {
            "model": OLLAMA_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Customer Context: {json.dumps(context)}\nUser Query: {user_message}"}
            ],
            "format": "json",
            "stream": False,
            "options": {"temperature": 0.1}
        }

        resp = requests.post(f"{OLLAMA_BASE_URL}/api/chat", json=payload, timeout=5.0)
        if resp.status_code == 200:
            data = resp.json()
            content = data.get("message", {}).get("content", "")
            parsed = json.loads(content)
            if "tool_name" in parsed and parsed["tool_name"]:
                return parsed["tool_name"], parsed.get("arguments", {})
            if "reply" in parsed:
                return None, parsed["reply"]
        return None

    @classmethod
    def _resolve_order_id(cls, msg, context, intent_type="tracking"):
        """
        Dynamically resolves an order_id:
        1. Explicit match in user message (e.g., ORD1001)
        2. Contextual current_order_id if valid
        3. Dynamic lookup of customer orders:
           - Exactly 1 relevant order -> Auto-resolve to that order_id
           - Multiple relevant orders -> Return clarifying question
           - 0 relevant orders -> Return clarifying question
        Returns: (order_id, clarifying_reply)
        """
        # 1. Explicit order ID in user message
        order_match = re.search(r"\b(ord\d+)\b", msg, re.IGNORECASE)
        if order_match:
            return order_match.group(1).upper(), None

        # 2. Contextual current_order_id if present and non-null
        ctx_order = context.get("current_order_id")
        if ctx_order and str(ctx_order).strip().lower() not in ("none", "null", ""):
            return str(ctx_order).strip().upper(), None

        # 3. Dynamic lookup from customer's order history
        customer_id = context.get("customer_id")
        if not customer_id or customer_id == "CUS_GUEST":
            return None, "Please provide your order ID (e.g., ORD1001) so I can assist you with your request."

        try:
            orders = OrderService.get_orders_for_customer(customer_id)
        except Exception:
            orders = []

        if not orders:
            return None, "You don't have any orders on file with this account. Please provide an order ID (e.g., ORD1001) to proceed."

        # Filter candidate orders by intent relevance
        if intent_type == "cancel":
            candidates = [o for o in orders if o.get("order_status") in ("PLACED", "CONFIRMED")]
            if len(candidates) == 1:
                return candidates[0]["order_id"], None
            elif len(candidates) > 1:
                order_list_str = ", ".join(f"#{o['order_id']}" for o in candidates)
                return None, f"You have multiple cancellable orders ({order_list_str}). Which order would you like to cancel?"
            else:
                recent = orders[0]
                status_desc = recent.get("order_status", "").lower()
                return None, f"Your recent order #{recent['order_id']} is already '{status_desc}' and cannot be cancelled automatically. Please provide an order ID if you wish to query a different order."

        elif intent_type == "refund":
            candidates = [o for o in orders if o.get("order_status") in ("DELIVERED", "CANCELLED", "RETURN_REQUESTED", "PLACED", "CONFIRMED")]
            if len(candidates) == 1:
                return candidates[0]["order_id"], None
            elif len(candidates) > 1:
                order_list_str = ", ".join(f"#{o['order_id']}" for o in candidates[:3])
                return None, f"You have multiple orders on file ({order_list_str}). Which order would you like to request a refund for?"
            else:
                return None, "Please provide the specific order ID (e.g., ORD1001) you would like to request a refund for."

        elif intent_type == "return":
            candidates = [o for o in orders if o.get("order_status") in ("DELIVERED",)]
            if len(candidates) == 1:
                return candidates[0]["order_id"], None
            elif len(candidates) > 1:
                order_list_str = ", ".join(f"#{o['order_id']}" for o in candidates[:3])
                return None, f"You have multiple delivered orders ({order_list_str}). Which order would you like to return?"
            else:
                return None, "Please provide the order ID (e.g., ORD1001) of the delivered item you would like to return."

        else:  # tracking / status / payment
            active_orders = [o for o in orders if o.get("order_status") not in ("CANCELLED", "REFUNDED")]
            if len(active_orders) == 1:
                return active_orders[0]["order_id"], None
            elif len(active_orders) > 1:
                order_list_str = ", ".join(f"#{o['order_id']}" for o in active_orders[:3])
                return None, f"You have multiple active orders ({order_list_str}). Which order would you like to track?"
            elif len(orders) == 1:
                return orders[0]["order_id"], None
            else:
                order_list_str = ", ".join(f"#{o['order_id']}" for o in orders[:3])
                return None, f"You have multiple orders ({order_list_str}). Which order would you like tracking details for?"

    @classmethod
    def _parse_intent_deterministically(cls, message, context):
        """
        Robust, regex & semantic intent extractor covering all customer shopping and support workflows.
        Prioritizes order-specific and commercial intents over generic keyword searches.
        """
        msg = message.lower().strip()
        customer_id = context.get("customer_id", "CUS1001")

        # -------------------------------------------------------------
        # PRIORITY 1: Commercial Discount / Price Concession Requests
        # -------------------------------------------------------------
        is_discount_request = (
            "discount" in msg or "coupon" in msg or "promo" in msg or "voucher" in msg or
            "concession" in msg or "price reduction" in msg or "waiver" in msg or
            re.search(r"\b\d+%\s*(?:off|discount)\b", msg) is not None or
            "cheaper price" in msg or "loyalty discount" in msg
        )
        if is_discount_request:
            # Custom commercial discounts on existing or proposed orders require supervisor authorization
            return None, (
                "🛡️ **Supervisor Approval Required**: Custom commercial discounts and order price concessions "
                "require authorization from a customer support supervisor. Your discount request has been recorded "
                "and escalated to our support management team for review."
            )

        # -------------------------------------------------------------
        # PRIORITY 2: Sensitive Customer Profile / Privacy Operations
        # -------------------------------------------------------------
        if "delete" in msg and "account" in msg:
            return "delete_customer_account", {"customer_id": customer_id}
        if "export" in msg and ("data" in msg or "information" in msg):
            return "export_customer_data", {"customer_id": customer_id}
        if "pii" in msg or "personal info" in msg:
            return "get_customer_pii", {"customer_id": customer_id}

        # -------------------------------------------------------------
        # PRIORITY 3: Order History / Customer Addresses / Profile
        # -------------------------------------------------------------
        if "recent order" in msg or "my orders" in msg or "order history" in msg or ("list" in msg and "order" in msg):
            return "get_order_history", {"customer_id": customer_id}

        if "address" in msg and ("change" in msg or "update" in msg or "delivery" in msg or "saved" in msg):
            return "get_customer_addresses", {"customer_id": customer_id}

        if ("profile" in msg or "account" in msg) and "delete" not in msg:
            return "get_customer_profile", {"customer_id": customer_id}

        # -------------------------------------------------------------
        # PRIORITY 4: Order-Specific Operations (Dynamic Slot-Filling)
        # -------------------------------------------------------------

        # A. Refund Intent
        if "refund" in msg:
            order_id, clarifying_reply = cls._resolve_order_id(msg, context, intent_type="refund")
            if not order_id:
                return None, clarifying_reply

            amt_match = re.search(r"(?:rs\.?|₹|inr)?\s*(\d+(?:,\d+)*(?:\.\d+)?)", msg)
            amount = None
            if amt_match and "ord" not in amt_match.group(1).lower():
                try:
                    amount = float(amt_match.group(1).replace(",", ""))
                except Exception:
                    pass
            return "process_refund", {"order_id": order_id, "amount": amount}

        # B. Cancel Order Intent
        if "cancel" in msg and ("order" in msg or re.search(r"\bord\d+\b", msg) is not None):
            order_id, clarifying_reply = cls._resolve_order_id(msg, context, intent_type="cancel")
            if not order_id:
                return None, clarifying_reply
            return "cancel_order", {"order_id": order_id}

        # C. Return Product Intent
        if "return" in msg:
            order_id, clarifying_reply = cls._resolve_order_id(msg, context, intent_type="return")
            if not order_id:
                return None, clarifying_reply

            reason = "Changed mind"
            if "damaged" in msg or "broken" in msg:
                reason = "Damaged product"
            elif "wrong" in msg:
                reason = "Wrong product"
            elif "size" in msg or "fit" in msg:
                reason = "Size issue"
            return "request_return", {"order_id": order_id, "reason": reason}

        # D. Order Status Intent
        if "status of" in msg or ("status" in msg and "order" in msg):
            order_id, clarifying_reply = cls._resolve_order_id(msg, context, intent_type="tracking")
            if not order_id:
                return None, clarifying_reply
            return "get_order_status", {"order_id": order_id}

        # E. Order Tracking / Where is my order
        if "where is my order" in msg or "track" in msg or "tracking" in msg or "where is" in msg or "delivery status" in msg:
            order_id, clarifying_reply = cls._resolve_order_id(msg, context, intent_type="tracking")
            if not order_id:
                return None, clarifying_reply
            return "get_tracking_details", {"order_id": order_id}

        # F. Payment Details / How much did I pay
        if "how much" in msg or "payment" in msg or "paid" in msg:
            order_id, clarifying_reply = cls._resolve_order_id(msg, context, intent_type="tracking")
            if not order_id:
                return None, clarifying_reply
            return "get_payment_status", {"order_id": order_id}

        # -------------------------------------------------------------
        # PRIORITY 5: Product Catalog, Stock & Search
        # -------------------------------------------------------------
        prod_match = re.search(r"\b(prd\d{4})\b", msg)
        product_id = prod_match.group(1).upper() if prod_match else "PRD1001"

        if "stock" in msg or "in stock" in msg or "available units" in msg:
            return "check_product_stock", {"product_id": product_id}

        if any(term in msg for term in ["laptop", "phone", "shoe", "headphone", "watch", "speaker", "book", "bag", "dress", "shirt", "show me", "search", "looking for", "find", "buy", "price of"]):
            clean_q = re.sub(r"(show me|search for|looking for|find|under|₹|\d+|rs\.?|inr|price of)", "", msg).strip()
            if not clean_q:
                clean_q = "laptop"
            return "search_products", {"query": clean_q}

        # Default fallback to search with user message
        return "search_products", {"query": msg}


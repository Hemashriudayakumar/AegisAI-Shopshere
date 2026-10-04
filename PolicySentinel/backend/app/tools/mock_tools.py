from typing import Any, Dict

# Mock In-Memory Database / Registry for Tools
MOCK_ORDERS = {
    "ORD-101": {
        "order_id": "ORD-101",
        "customer_id": "CUST-10",
        "status": "Shipped",
        "item": "Noise-Cancelling Headphones",
        "price": 3000.0,
        "verified_delivery_date": "2026-08-28"
    },
    "ORD-202": {
        "order_id": "ORD-202",
        "customer_id": "CUST-10",
        "status": "Delivered",
        "item": "Wireless Mouse",
        "price": 400.0,
        "verified_delivery_date": "2026-08-20"
    }
}

def get_order_status(order_id: str) -> Dict[str, Any]:
    """Mock tool to fetch order details."""
    order = MOCK_ORDERS.get(order_id)
    if order:
        return {
            "order_id": order["order_id"],
            "customer_id": order["customer_id"],
            "status": order["status"],
            "item": order["item"],
            "verified_delivery_date": order["verified_delivery_date"],
            "price": order["price"]
        }
    return {
        "order_id": order_id,
        "status": "Not Found",
        "verified_delivery_date": None,
        "error": "Order ID does not exist"
    }

def issue_refund(order_id: str, amount: float) -> Dict[str, Any]:
    """Mock tool to issue refunds."""
    return {
        "status": "SUCCESS",
        "action": "issue_refund",
        "refund_id": f"REF-{hash(order_id + str(amount)) % 100000:05d}",
        "order_id": order_id,
        "amount": float(amount),
        "message": f"Refund of ₹{float(amount):,.2f} processed successfully for {order_id}."
    }

def cancel_order(order_id: str, reason: str = "Customer request") -> Dict[str, Any]:
    """Mock tool to cancel order."""
    return {
        "status": "CANCELLED",
        "action": "cancel_order",
        "order_id": order_id,
        "reason": reason,
        "message": f"Order {order_id} has been cancelled."
    }

def offer_discount(order_id: str, amount: float) -> Dict[str, Any]:
    """Mock tool to offer discount / promotional credit."""
    return {
        "status": "APPLIED",
        "action": "offer_discount",
        "order_id": order_id,
        "discount_amount": float(amount),
        "coupon_code": f"SAVE-{int(amount)}"
    }

def escalate_to_human(conversation_id: str, reason: str) -> Dict[str, Any]:
    """Mock tool to escalate conversation to a supervisor."""
    return {
        "status": "ESCALATED",
        "action": "escalate_to_human",
        "ticket_id": f"TICK-{abs(hash(conversation_id + reason)) % 10000:04d}",
        "conversation_id": conversation_id,
        "reason": reason
    }

TOOL_REGISTRY = {
    "get_order_status": get_order_status,
    "issue_refund": issue_refund,
    "cancel_order": cancel_order,
    "offer_discount": offer_discount,
    "escalate_to_human": escalate_to_human,
}

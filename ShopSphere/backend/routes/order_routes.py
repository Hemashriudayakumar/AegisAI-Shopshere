from flask import Blueprint, request, jsonify, session
from backend.services.order_service import OrderService

order_bp = Blueprint("orders", __name__, url_prefix="/api")

def get_current_customer_id():
    return session.get("customer_id", "CUS1001")

@order_bp.route("/checkout", methods=["POST"])
def checkout():
    customer_id = get_current_customer_id()
    data = request.get_json() or {}
    address_id = data.get("address_id")
    payment_method = data.get("payment_method", "Credit Card")
    custom_items = data.get("items")

    result = OrderService.create_order(
        customer_id=customer_id,
        address_id=address_id,
        payment_method=payment_method,
        custom_items=custom_items
    )
    return jsonify(result), (201 if result.get("success") else 400)

@order_bp.route("/orders", methods=["GET"])
def get_orders():
    customer_id = get_current_customer_id()
    status_filter = request.args.get("status")
    orders = OrderService.get_orders_for_customer(customer_id, status_filter=status_filter)
    return jsonify({"success": True, "orders": orders})

@order_bp.route("/orders/<order_id>", methods=["GET"])
def get_order_detail(order_id):
    customer_id = get_current_customer_id()
    # Customer ownership enforcement: customer can only view their own order
    order = OrderService.get_order_by_id(order_id, customer_id=customer_id)
    if not order:
        # Check if admin session or return 404
        if session.get("is_admin"):
            order = OrderService.get_order_by_id(order_id)
        if not order:
            return jsonify({"success": False, "message": "Order not found or access denied."}), 404
    return jsonify({"success": True, "order": order})

@order_bp.route("/orders/<order_id>/cancel", methods=["POST"])
def cancel_order(order_id):
    customer_id = get_current_customer_id()
    data = request.get_json() or {}
    reason = data.get("reason", "Cancelled by customer")
    res = OrderService.cancel_order(order_id, customer_id=customer_id, reason=reason)
    return jsonify(res), (200 if res.get("success") else 400)

@order_bp.route("/orders/<order_id>/status", methods=["GET"])
def get_status(order_id):
    res = OrderService.get_order_status(order_id)
    return jsonify({"success": True, **res})

@order_bp.route("/delivery/<order_id>/status", methods=["GET"])
def get_delivery_status(order_id):
    res = OrderService.get_delivery_status(order_id)
    return jsonify({"success": True, **res})

@order_bp.route("/delivery/<order_id>/tracking", methods=["GET"])
def get_tracking(order_id):
    res = OrderService.get_tracking_details(order_id)
    return jsonify({"success": True, **res})

@order_bp.route("/orders/<order_id>/returns", methods=["POST"])
def request_return(order_id):
    customer_id = get_current_customer_id()
    data = request.get_json() or {}
    reason = data.get("reason", "Changed mind")
    res = OrderService.request_return(order_id, reason=reason, customer_id=customer_id)
    return jsonify(res), (201 if res.get("success") else 400)

@order_bp.route("/orders/<order_id>/returns/status", methods=["GET"])
def check_return(order_id):
    res = OrderService.check_return_status(order_id)
    return jsonify({"success": True, **res})

@order_bp.route("/orders/<order_id>/refund", methods=["POST"])
def process_refund(order_id):
    data = request.get_json() or {}
    amount = data.get("amount")
    res = OrderService.process_refund(order_id, amount=amount)
    return jsonify(res), (200 if res.get("success") else 400)


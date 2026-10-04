from flask import Blueprint, request, jsonify, session
from backend.services.cart_service import CartService

cart_bp = Blueprint("cart", __name__, url_prefix="/api/cart")

def get_current_customer_id():
    return session.get("customer_id", "CUS1001") # Defaults to demo user CUS1001 if not explicitly logged in

@cart_bp.route("", methods=["GET"])
def get_cart():
    customer_id = get_current_customer_id()
    cart_data = CartService.get_cart(customer_id)
    return jsonify({"success": True, "cart": cart_data})

@cart_bp.route("/add", methods=["POST"])
def add_to_cart():
    customer_id = get_current_customer_id()
    data = request.get_json() or {}
    product_id = data.get("product_id")
    quantity = int(data.get("quantity", 1))

    if not product_id:
        return jsonify({"success": False, "message": "product_id is required."}), 400

    result = CartService.add_to_cart(customer_id, product_id, quantity)
    return jsonify(result), (200 if result.get("success") else 400)

@cart_bp.route("/item/<item_id>", methods=["PUT"])
def update_item(item_id):
    customer_id = get_current_customer_id()
    data = request.get_json() or {}
    quantity = int(data.get("quantity", 1))

    result = CartService.update_cart_item(customer_id, item_id, quantity)
    return jsonify(result), (200 if result.get("success") else 400)

@cart_bp.route("/item/<item_id>", methods=["DELETE"])
def remove_item(item_id):
    customer_id = get_current_customer_id()
    result = CartService.remove_cart_item(customer_id, item_id)
    return jsonify(result), (200 if result.get("success") else 400)

@cart_bp.route("/clear", methods=["DELETE"])
def clear_cart():
    customer_id = get_current_customer_id()
    result = CartService.clear_cart(customer_id)
    return jsonify(result)


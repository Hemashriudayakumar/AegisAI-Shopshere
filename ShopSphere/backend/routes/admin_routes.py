from flask import Blueprint, request, jsonify
from backend.services.order_service import OrderService
from backend.services.product_service import ProductService
from backend.services.customer_service import CustomerService

admin_bp = Blueprint("admin", __name__, url_prefix="/api/admin")

@admin_bp.route("/metrics", methods=["GET"])
def metrics():
    stats = OrderService.get_admin_metrics()
    return jsonify({"success": True, "metrics": stats})

@admin_bp.route("/products", methods=["GET"])
def list_products():
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 50))
    res = ProductService.get_all_products(page=page, per_page=per_page)
    return jsonify({"success": True, **res})

@admin_bp.route("/products", methods=["POST"])
def add_product():
    data = request.get_json() or {}
    try:
        new_prod = ProductService.create_product(data)
        return jsonify({"success": True, "product": new_prod, "message": "Product created successfully."}), 201
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 400

@admin_bp.route("/products/<product_id>", methods=["PUT"])
def update_product(product_id):
    data = request.get_json() or {}
    updated = ProductService.update_product(product_id, data)
    if not updated:
        return jsonify({"success": False, "message": "Product not found."}), 404
    return jsonify({"success": True, "product": updated, "message": "Product updated successfully."})

@admin_bp.route("/products/<product_id>/stock", methods=["PUT"])
def update_stock(product_id):
    data = request.get_json() or {}
    qty = data.get("stock_quantity", 0)
    updated = ProductService.update_stock(product_id, qty)
    if not updated:
        return jsonify({"success": False, "message": "Product not found."}), 404
    return jsonify({"success": True, "product": updated, "message": "Stock updated successfully."})

@admin_bp.route("/products/<product_id>", methods=["DELETE"])
def delete_product(product_id):
    success = ProductService.delete_product(product_id)
    if not success:
        return jsonify({"success": False, "message": "Product not found."}), 404
    return jsonify({"success": True, "message": "Product deactivated."})

@admin_bp.route("/orders", methods=["GET"])
def list_orders():
    status = request.args.get("status")
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 20))
    res = OrderService.get_all_orders_admin(status=status, page=page, per_page=per_page)
    return jsonify({"success": True, **res})

@admin_bp.route("/orders/<order_id>/status", methods=["PUT"])
def update_order_status(order_id):
    data = request.get_json() or {}
    new_status = data.get("status")
    res = OrderService.update_order_status_admin(order_id, new_status)
    return jsonify(res), (200 if res.get("success") else 400)

@admin_bp.route("/customers", methods=["GET"])
def list_customers():
    customers = CustomerService.get_all_customers_admin()
    return jsonify({"success": True, "customers": customers})

@admin_bp.route("/returns/<return_id>/approve", methods=["POST"])
def approve_return(return_id):
    res = OrderService.approve_return(return_id)
    return jsonify(res), (200 if res.get("success") else 400)


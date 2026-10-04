from flask import Blueprint, request, jsonify, session
from backend.services.customer_service import CustomerService

customer_bp = Blueprint("customers", __name__, url_prefix="/api/customers")

def get_current_customer_id():
    return session.get("customer_id", "CUS1001")

@customer_bp.route("/profile", methods=["GET"])
def get_profile():
    customer_id = get_current_customer_id()
    profile = CustomerService.get_customer_profile(customer_id)
    if not profile:
        return jsonify({"success": False, "message": "Customer not found."}), 404
    return jsonify({"success": True, "profile": profile})

@customer_bp.route("/profile", methods=["PUT"])
def update_profile():
    customer_id = get_current_customer_id()
    data = request.get_json() or {}
    res = CustomerService.update_customer_profile(customer_id, data)
    return jsonify(res), (200 if res.get("success") else 400)

@customer_bp.route("/addresses", methods=["GET"])
def get_addresses():
    customer_id = get_current_customer_id()
    addresses = CustomerService.get_customer_addresses(customer_id)
    return jsonify({"success": True, "addresses": addresses})

@customer_bp.route("/addresses", methods=["POST"])
def add_address():
    customer_id = get_current_customer_id()
    data = request.get_json() or {}
    res = CustomerService.add_customer_address(customer_id, data)
    return jsonify(res), (201 if res.get("success") else 400)

@customer_bp.route("/addresses/<address_id>", methods=["PUT"])
def update_address(address_id):
    customer_id = get_current_customer_id()
    data = request.get_json() or {}
    res = CustomerService.update_customer_address(customer_id, address_id, data)
    return jsonify(res), (200 if res.get("success") else 400)

@customer_bp.route("/addresses/<address_id>", methods=["DELETE"])
def delete_address(address_id):
    customer_id = get_current_customer_id()
    res = CustomerService.delete_customer_address(customer_id, address_id)
    return jsonify(res), (200 if res.get("success") else 400)

@customer_bp.route("/addresses/<address_id>/default", methods=["POST"])
def set_default(address_id):
    customer_id = get_current_customer_id()
    res = CustomerService.set_default_address(customer_id, address_id)
    return jsonify(res), (200 if res.get("success") else 400)

@customer_bp.route("/pii", methods=["GET"])
def get_pii():
    customer_id = get_current_customer_id()
    res = CustomerService.get_customer_pii(customer_id)
    return jsonify(res)

@customer_bp.route("/export", methods=["POST"])
def export_data():
    customer_id = get_current_customer_id()
    res = CustomerService.export_customer_data(customer_id)
    return jsonify(res)


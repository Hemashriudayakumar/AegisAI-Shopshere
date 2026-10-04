from flask import Blueprint, request, jsonify, session
from backend.services.customer_service import CustomerService

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")

@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json() or {}
    name = data.get("name")
    email = data.get("email")
    phone = data.get("phone")
    password = data.get("password")

    if not all([name, email, phone, password]):
        return jsonify({"success": False, "message": "All fields (name, email, phone, password) are required."}), 400

    res = CustomerService.register_customer(name, email, phone, password)
    if res.get("success"):
        customer = res["customer"]
        session["customer_id"] = customer["customer_id"]
        session["customer_name"] = customer["name"]
        session["customer_email"] = customer["email"]
        return jsonify(res), 201
    return jsonify(res), 400

@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"success": False, "message": "Email and password are required."}), 400

    res = CustomerService.authenticate_customer(email, password)
    if res.get("success"):
        customer = res["customer"]
        session["customer_id"] = customer["customer_id"]
        session["customer_name"] = customer["name"]
        session["customer_email"] = customer["email"]
        return jsonify(res), 200
    return jsonify(res), 401

@auth_bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"success": True, "message": "Logged out successfully."})

@auth_bp.route("/me", methods=["GET"])
def me():
    customer_id = session.get("customer_id")
    if not customer_id:
        return jsonify({"authenticated": False, "customer": None})

    profile = CustomerService.get_customer_profile(customer_id)
    if not profile:
        session.clear()
        return jsonify({"authenticated": False, "customer": None})

    return jsonify({"authenticated": True, "customer": profile})

@auth_bp.route("/demo-switch", methods=["POST"])
def demo_switch():
    """Allows 1-click switching between demo users for easy testing and evaluation."""
    data = request.get_json() or {}
    customer_id = data.get("customer_id", "CUS1001")

    profile = CustomerService.get_customer_profile(customer_id)
    if not profile:
        return jsonify({"success": False, "message": f"Demo customer {customer_id} not found."}), 404

    session["customer_id"] = profile["customer_id"]
    session["customer_name"] = profile["name"]
    session["customer_email"] = profile["email"]
    return jsonify({
        "success": True,
        "message": f"Switched active session to demo user {profile['name']}",
        "customer": profile
    })


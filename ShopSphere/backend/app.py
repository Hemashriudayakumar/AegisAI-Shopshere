import os
from flask import Flask, render_template, session, request, redirect, url_for
from backend.config import Config
from backend.routes.auth_routes import auth_bp
from backend.routes.product_routes import product_bp
from backend.routes.cart_routes import cart_bp
from backend.routes.customer_routes import customer_bp
from backend.routes.order_routes import order_bp
from backend.routes.admin_routes import admin_bp
from backend.routes.chat_routes import chat_bp
from backend.services.customer_service import CustomerService
from backend.services.cart_service import CartService
from backend.init_db import init_database

def create_app():
    # Templates and static directories located in frontend/
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    template_dir = os.path.join(base_dir, "frontend", "templates")
    static_dir = os.path.join(base_dir, "frontend", "static")

    app = Flask(
        __name__,
        template_folder=template_dir,
        static_folder=static_dir
    )
    app.config.from_object(Config)

    # Automatically ensure database and mock data are seeded
    try:
        init_database()
    except Exception as e:
        print(f"[App Init Warning] Database initialization check: {e}")

    # Register Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(product_bp)
    app.register_blueprint(cart_bp)
    app.register_blueprint(customer_bp)
    app.register_blueprint(order_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(chat_bp)

    @app.before_request
    def ensure_session_customer():
        if "customer_id" not in session:
            session["customer_id"] = "CUS1001"
            session["customer_name"] = "Rahul Sharma"
            session["customer_email"] = "rahul@example.com"

    # Template Context Processor (injects user and cart info into all pages)
    @app.context_processor
    def inject_globals():
        customer_id = session.get("customer_id", "CUS1001")
        cart_info = CartService.get_cart(customer_id) if customer_id else {"total_items": 0}
        return {
            "current_customer_id": customer_id,
            "current_customer_name": session.get("customer_name", "Rahul Sharma"),
            "current_customer_email": session.get("customer_email", "rahul@example.com"),
            "cart_count": cart_info.get("total_items", 0),
            "is_admin": session.get("is_admin", False)
        }

    # Customer Page Routes
    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/products")
    def products():
        return render_template("products.html")

    @app.route("/products/<product_id>")
    def product_detail(product_id):
        return render_template("product_detail.html", product_id=product_id)

    @app.route("/cart")
    def cart():
        return render_template("cart.html")

    @app.route("/checkout")
    def checkout():
        return render_template("checkout.html")

    @app.route("/order-confirmation/<order_id>")
    def order_confirmation(order_id):
        return render_template("order_confirmation.html", order_id=order_id)

    @app.route("/orders")
    def orders():
        return render_template("orders.html")

    @app.route("/orders/<order_id>")
    def order_detail(order_id):
        track_mode = request.args.get("track", "false").lower() == "true"
        return render_template("order_detail.html", order_id=order_id, track_mode=track_mode)

    @app.route("/orders/<order_id>/track")
    def track_order(order_id):
        return render_template("order_detail.html", order_id=order_id, track_mode=True)

    @app.route("/returns")
    def returns():
        return render_template("returns.html")

    @app.route("/profile")
    def profile():
        return render_template("profile.html")

    @app.route("/addresses")
    def addresses():
        return render_template("addresses.html")

    @app.route("/support")
    def support():
        return render_template("support.html")

    @app.route("/login")
    def login():
        return render_template("login.html")

    @app.route("/register")
    def register():
        return render_template("register.html")

    # Admin Page Routes
    @app.route("/admin")
    def admin_dashboard():
        return render_template("admin/dashboard.html")

    @app.route("/admin/products")
    def admin_products():
        return render_template("admin/products.html")

    @app.route("/admin/orders")
    def admin_orders():
        return render_template("admin/orders.html")

    @app.route("/admin/customers")
    def admin_customers():
        return render_template("admin/customers.html")

    @app.route("/admin/returns")
    def admin_returns():
        return render_template("admin/returns.html")

    return app

app = create_app()

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)

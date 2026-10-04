from flask import Blueprint, request, jsonify
from backend.services.product_service import ProductService

product_bp = Blueprint("products", __name__, url_prefix="/api")

@product_bp.route("/products", methods=["GET"])
def get_products():
    category = request.args.get("category")
    subcategory = request.args.get("subcategory")
    brand = request.args.get("brand")
    min_price = request.args.get("min_price")
    max_price = request.args.get("max_price")
    min_rating = request.args.get("min_rating")
    sort_by = request.args.get("sort_by", "rating")
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 20))

    result = ProductService.get_all_products(
        category=category,
        subcategory=subcategory,
        brand=brand,
        min_price=min_price,
        max_price=max_price,
        min_rating=min_rating,
        sort_by=sort_by,
        page=page,
        per_page=per_page
    )
    return jsonify({"success": True, **result})

@product_bp.route("/products/<product_id>", methods=["GET"])
def get_product(product_id):
    product = ProductService.get_product_by_id(product_id)
    if not product:
        return jsonify({"success": False, "message": "Product not found."}), 404
    return jsonify({"success": True, "product": product})

@product_bp.route("/products/search", methods=["GET"])
def search():
    query_str = request.args.get("q", "").strip()
    category = request.args.get("category")
    limit = int(request.args.get("limit", 20))

    results = ProductService.search_products(query_str, category=category, limit=limit)
    return jsonify({"success": True, "query": query_str, "count": len(results), "products": results})

@product_bp.route("/products/<product_id>/stock", methods=["GET"])
def check_stock(product_id):
    stock_info = ProductService.check_product_stock(product_id)
    return jsonify({"success": True, **stock_info})

@product_bp.route("/categories", methods=["GET"])
def get_categories():
    categories = ProductService.get_categories()
    return jsonify({"success": True, "categories": categories})

@product_bp.route("/home-sections", methods=["GET"])
def get_home_sections():
    sections = ProductService.get_home_sections()
    return jsonify({"success": True, **sections})


from decimal import Decimal
from sqlalchemy import or_, desc, asc
from backend.database import SessionLocal
from backend.models import Product, Category, Review

class ProductService:
    @staticmethod
    def get_all_products(category=None, subcategory=None, brand=None, min_price=None, max_price=None, min_rating=None, sort_by=None, page=1, per_page=24):
        session = SessionLocal()
        try:
            query = session.query(Product).filter(Product.status == "ACTIVE")

            if category and category.lower() != "all":
                query = query.filter(Product.category.ilike(f"%{category}%"))
            if subcategory:
                query = query.filter(Product.subcategory.ilike(f"%{subcategory}%"))
            if brand:
                query = query.filter(Product.brand.ilike(f"%{brand}%"))
            if min_price is not None:
                query = query.filter(Product.final_price >= float(min_price))
            if max_price is not None:
                query = query.filter(Product.final_price <= float(max_price))
            if min_rating is not None:
                query = query.filter(Product.rating >= float(min_rating))

            # Sorting
            if sort_by == "price_low_to_high":
                query = query.order_by(asc(Product.final_price))
            elif sort_by == "price_high_to_low":
                query = query.order_by(desc(Product.final_price))
            elif sort_by == "rating":
                query = query.order_by(desc(Product.rating))
            elif sort_by == "popularity":
                query = query.order_by(desc(Product.review_count))
            elif sort_by == "newest":
                query = query.order_by(desc(Product.created_at))
            else:
                query = query.order_by(desc(Product.rating))

            total = query.count()
            products = query.offset((page - 1) * per_page).limit(per_page).all()
            return {
                "products": [p.to_dict() for p in products],
                "total": total,
                "page": page,
                "per_page": per_page,
                "total_pages": (total + per_page - 1) // per_page
            }
        finally:
            session.close()

    @staticmethod
    def get_product_by_id(product_id):
        session = SessionLocal()
        try:
            p = session.query(Product).filter(Product.product_id == product_id).first()
            if not p:
                return None
            data = p.to_dict()
            # Fetch reviews
            reviews = session.query(Review).filter(Review.product_id == product_id).order_by(desc(Review.created_at)).all()
            data["reviews"] = [r.to_dict() for r in reviews]
            # Fetch related products
            related = session.query(Product).filter(
                Product.category == p.category,
                Product.product_id != p.product_id,
                Product.status == "ACTIVE"
            ).limit(4).all()
            data["related_products"] = [rp.to_dict() for rp in related]
            return data
        finally:
            session.close()

    @staticmethod
    def search_products(query_str, category=None, limit=20):
        session = SessionLocal()
        try:
            q = session.query(Product).filter(Product.status == "ACTIVE")
            if category and category.lower() != "all":
                q = q.filter(Product.category.ilike(f"%{category}%"))

            if query_str:
                search_filter = or_(
                    Product.product_name.ilike(f"%{query_str}%"),
                    Product.brand.ilike(f"%{query_str}%"),
                    Product.category.ilike(f"%{query_str}%"),
                    Product.subcategory.ilike(f"%{query_str}%"),
                    Product.description.ilike(f"%{query_str}%")
                )
                q = q.filter(search_filter)

            products = q.limit(limit).all()
            return [p.to_dict() for p in products]
        finally:
            session.close()

    @staticmethod
    def check_product_stock(product_id):
        session = SessionLocal()
        try:
            p = session.query(Product).filter(Product.product_id == product_id).first()
            if not p:
                return {"found": False, "message": f"Product {product_id} not found."}
            return {
                "found": True,
                "product_id": p.product_id,
                "product_name": p.product_name,
                "stock_quantity": p.stock_quantity,
                "in_stock": p.stock_quantity > 0,
                "status": "IN_STOCK" if p.stock_quantity > 0 else "OUT_OF_STOCK"
            }
        finally:
            session.close()

    @staticmethod
    def get_categories():
        session = SessionLocal()
        try:
            cats = session.query(Category).all()
            return [c.to_dict() for c in cats]
        finally:
            session.close()

    @staticmethod
    def get_home_sections():
        session = SessionLocal()
        try:
            featured = session.query(Product).filter(Product.rating >= 4.7).order_by(desc(Product.rating)).limit(8).all()
            deals = session.query(Product).filter(Product.discount >= 25).order_by(desc(Product.discount)).limit(8).all()
            trending = session.query(Product).order_by(desc(Product.review_count)).limit(8).all()
            categories = session.query(Category).all()
            return {
                "featured": [p.to_dict() for p in featured],
                "deals": [p.to_dict() for p in deals],
                "trending": [p.to_dict() for p in trending],
                "categories": [c.to_dict() for c in categories]
            }
        finally:
            session.close()

    @staticmethod
    def create_product(data):
        session = SessionLocal()
        try:
            price = Decimal(str(data.get("price", 0)))
            disc = Decimal(str(data.get("discount", 0)))
            final_price = round(price * (Decimal("1.0") - (disc / Decimal("100.0"))), 2)
            pid = data.get("product_id") or f"PRD{session.query(Product).count() + 1001}"

            new_prod = Product(
                product_id=pid,
                product_name=data["product_name"],
                description=data.get("description", ""),
                category=data["category"],
                subcategory=data.get("subcategory", data["category"]),
                brand=data.get("brand", "ShopSphere"),
                price=price,
                discount=disc,
                final_price=final_price,
                stock_quantity=int(data.get("stock_quantity", 10)),
                rating=Decimal(str(data.get("rating", 4.5))),
                review_count=int(data.get("review_count", 0)),
                seller=data.get("seller", "ShopSphere Official"),
                image=data.get("image", "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=500&q=80"),
                status=data.get("status", "ACTIVE")
            )
            session.add(new_prod)
            session.commit()
            return new_prod.to_dict()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    @staticmethod
    def update_product(product_id, data):
        session = SessionLocal()
        try:
            p = session.query(Product).filter(Product.product_id == product_id).first()
            if not p:
                return None
            for key, val in data.items():
                if hasattr(p, key) and key not in ["product_id", "created_at"]:
                    if key in ["price", "discount", "rating"]:
                        setattr(p, key, Decimal(str(val)))
                    elif key in ["stock_quantity", "review_count"]:
                        setattr(p, key, int(val))
                    else:
                        setattr(p, key, val)
            # Recompute final price
            p.final_price = round(p.price * (Decimal("1.0") - (p.discount / Decimal("100.0"))), 2)
            session.commit()
            return p.to_dict()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    @staticmethod
    def update_stock(product_id, quantity):
        session = SessionLocal()
        try:
            p = session.query(Product).filter(Product.product_id == product_id).first()
            if not p:
                return None
            p.stock_quantity = int(quantity)
            session.commit()
            return p.to_dict()
        finally:
            session.close()

    @staticmethod
    def delete_product(product_id):
        session = SessionLocal()
        try:
            p = session.query(Product).filter(Product.product_id == product_id).first()
            if not p:
                return False
            p.status = "INACTIVE"
            session.commit()
            return True
        finally:
            session.close()


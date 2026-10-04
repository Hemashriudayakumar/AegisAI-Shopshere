import uuid
from datetime import datetime
from backend.database import SessionLocal
from backend.models import Cart, CartItem, Product

class CartService:
    @staticmethod
    def get_or_create_cart(session, customer_id):
        cart = session.query(Cart).filter(Cart.customer_id == customer_id).first()
        if not cart:
            cart = Cart(
                cart_id=f"CRT{uuid.uuid4().hex[:8].upper()}",
                customer_id=customer_id,
                created_at=datetime.utcnow()
            )
            session.add(cart)
            session.flush()
        return cart

    @staticmethod
    def get_cart(customer_id):
        session = SessionLocal()
        try:
            cart = CartService.get_or_create_cart(session, customer_id)
            session.commit()
            return cart.to_dict()
        finally:
            session.close()

    @staticmethod
    def add_to_cart(customer_id, product_id, quantity=1):
        session = SessionLocal()
        try:
            quantity = int(quantity)
            if quantity <= 0:
                quantity = 1

            product = session.query(Product).filter(Product.product_id == product_id).first()
            if not product:
                return {"success": False, "message": "Product not found."}
            if product.stock_quantity < quantity:
                return {"success": False, "message": f"Only {product.stock_quantity} items available in stock."}

            cart = CartService.get_or_create_cart(session, customer_id)
            item = session.query(CartItem).filter(
                CartItem.cart_id == cart.cart_id,
                CartItem.product_id == product_id
            ).first()

            if item:
                new_qty = item.quantity + quantity
                if product.stock_quantity < new_qty:
                    return {"success": False, "message": f"Cannot add more. Max stock is {product.stock_quantity}."}
                item.quantity = new_qty
            else:
                item = CartItem(
                    item_id=f"CITM{uuid.uuid4().hex[:8].upper()}",
                    cart_id=cart.cart_id,
                    product_id=product_id,
                    quantity=quantity,
                    created_at=datetime.utcnow()
                )
                session.add(item)

            session.commit()
            return {
                "success": True,
                "message": f"Added {product.product_name} to cart.",
                "cart": cart.to_dict()
            }
        except Exception as e:
            session.rollback()
            return {"success": False, "message": str(e)}
        finally:
            session.close()

    @staticmethod
    def update_cart_item(customer_id, item_id, quantity):
        session = SessionLocal()
        try:
            quantity = int(quantity)
            cart = session.query(Cart).filter(Cart.customer_id == customer_id).first()
            if not cart:
                return {"success": False, "message": "Cart not found."}

            item = session.query(CartItem).filter(
                CartItem.item_id == item_id,
                CartItem.cart_id == cart.cart_id
            ).first()

            if not item:
                return {"success": False, "message": "Item not found in cart."}

            if quantity <= 0:
                session.delete(item)
                session.commit()
                return {"success": True, "message": "Item removed from cart.", "cart": cart.to_dict()}

            if item.product and item.product.stock_quantity < quantity:
                return {"success": False, "message": f"Only {item.product.stock_quantity} in stock."}

            item.quantity = quantity
            session.commit()
            return {"success": True, "message": "Cart updated.", "cart": cart.to_dict()}
        except Exception as e:
            session.rollback()
            return {"success": False, "message": str(e)}
        finally:
            session.close()

    @staticmethod
    def remove_cart_item(customer_id, item_id):
        session = SessionLocal()
        try:
            cart = session.query(Cart).filter(Cart.customer_id == customer_id).first()
            if not cart:
                return {"success": False, "message": "Cart not found."}

            item = session.query(CartItem).filter(
                CartItem.item_id == item_id,
                CartItem.cart_id == cart.cart_id
            ).first()

            if not item:
                return {"success": False, "message": "Item not found in cart."}

            session.delete(item)
            session.commit()
            return {"success": True, "message": "Item removed.", "cart": cart.to_dict()}
        except Exception as e:
            session.rollback()
            return {"success": False, "message": str(e)}
        finally:
            session.close()

    @staticmethod
    def clear_cart(customer_id):
        session = SessionLocal()
        try:
            cart = session.query(Cart).filter(Cart.customer_id == customer_id).first()
            if cart:
                session.query(CartItem).filter(CartItem.cart_id == cart.cart_id).delete()
                session.commit()
            return {"success": True, "message": "Cart cleared."}
        finally:
            session.close()


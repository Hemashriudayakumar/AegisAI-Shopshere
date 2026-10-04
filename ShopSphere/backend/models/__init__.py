from datetime import datetime
from sqlalchemy import (
    Column, String, Text, Integer, Float, Numeric, Boolean, DateTime, ForeignKey
)
from sqlalchemy.orm import relationship
from backend.database import Base

class Customer(Base):
    __tablename__ = "customers"

    customer_id = Column(String(50), primary_key=True)
    name = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, nullable=False)
    phone = Column(String(20), nullable=False)
    password_hash = Column(String(255), nullable=False)
    account_status = Column(String(20), default="ACTIVE", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    addresses = relationship("Address", back_populates="customer", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="customer")
    cart = relationship("Cart", back_populates="customer", uselist=False, cascade="all, delete-orphan")
    returns = relationship("Return", back_populates="customer")

    def to_dict(self, include_sensitive=False):
        data = {
            "customer_id": self.customer_id,
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "account_status": self.account_status,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else None
        }
        if include_sensitive:
            data["password_hash"] = self.password_hash
        return data


class Address(Base):
    __tablename__ = "addresses"

    address_id = Column(String(50), primary_key=True)
    customer_id = Column(String(50), ForeignKey("customers.customer_id", ondelete="CASCADE"), nullable=False)
    full_name = Column(String(100), nullable=False)
    phone = Column(String(20), nullable=False)
    address_line = Column(String(255), nullable=False)
    city = Column(String(100), nullable=False)
    state = Column(String(100), nullable=False)
    postal_code = Column(String(20), nullable=False)
    address_type = Column(String(20), default="Home", nullable=False)
    is_default = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    customer = relationship("Customer", back_populates="addresses")

    def to_dict(self):
        return {
            "address_id": self.address_id,
            "customer_id": self.customer_id,
            "full_name": self.full_name,
            "phone": self.phone,
            "address_line": self.address_line,
            "city": self.city,
            "state": self.state,
            "postal_code": self.postal_code,
            "address_type": self.address_type,
            "is_default": bool(self.is_default),
            "formatted": f"{self.address_line}, {self.city}, {self.state} - {self.postal_code}"
        }


class Category(Base):
    __tablename__ = "categories"

    category_id = Column(String(50), primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    slug = Column(String(100), unique=True, nullable=False)
    description = Column(Text)
    icon = Column(String(100), default="bi-tag")
    image = Column(String(255))

    def to_dict(self):
        return {
            "category_id": self.category_id,
            "name": self.name,
            "slug": self.slug,
            "description": self.description,
            "icon": self.icon,
            "image": self.image
        }


class Product(Base):
    __tablename__ = "products"

    product_id = Column(String(50), primary_key=True)
    product_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String(100), nullable=False)
    subcategory = Column(String(100), nullable=False)
    brand = Column(String(100), nullable=False)
    price = Column(Numeric(10, 2), nullable=False)
    discount = Column(Numeric(5, 2), default=0.00, nullable=False)
    final_price = Column(Numeric(10, 2), nullable=False)
    stock_quantity = Column(Integer, default=0, nullable=False)
    rating = Column(Numeric(3, 2), default=0.00, nullable=False)
    review_count = Column(Integer, default=0, nullable=False)
    seller = Column(String(100), default="ShopSphere Official", nullable=False)
    image = Column(String(500), nullable=False)
    status = Column(String(20), default="ACTIVE", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    reviews = relationship("Review", back_populates="product", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "product_id": self.product_id,
            "product_name": self.product_name,
            "description": self.description,
            "category": self.category,
            "subcategory": self.subcategory,
            "brand": self.brand,
            "price": float(self.price),
            "discount": float(self.discount),
            "final_price": float(self.final_price),
            "stock_quantity": self.stock_quantity,
            "in_stock": self.stock_quantity > 0,
            "rating": float(self.rating),
            "review_count": self.review_count,
            "seller": self.seller,
            "image": self.image,
            "status": self.status,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else None
        }


class Cart(Base):
    __tablename__ = "cart"

    cart_id = Column(String(50), primary_key=True)
    customer_id = Column(String(50), ForeignKey("customers.customer_id", ondelete="CASCADE"), unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    customer = relationship("Customer", back_populates="cart")
    items = relationship("CartItem", back_populates="cart", cascade="all, delete-orphan")

    def to_dict(self):
        items_list = [item.to_dict() for item in self.items]
        subtotal = sum(item["total_price"] for item in items_list)
        return {
            "cart_id": self.cart_id,
            "customer_id": self.customer_id,
            "items": items_list,
            "total_items": sum(item["quantity"] for item in items_list),
            "subtotal": round(subtotal, 2)
        }


class CartItem(Base):
    __tablename__ = "cart_items"

    item_id = Column(String(50), primary_key=True)
    cart_id = Column(String(50), ForeignKey("cart.cart_id", ondelete="CASCADE"), nullable=False)
    product_id = Column(String(50), ForeignKey("products.product_id", ondelete="CASCADE"), nullable=False)
    quantity = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    cart = relationship("Cart", back_populates="items")
    product = relationship("Product")

    def to_dict(self):
        unit_price = float(self.product.final_price) if self.product else 0.0
        return {
            "item_id": self.item_id,
            "cart_id": self.cart_id,
            "product_id": self.product_id,
            "product_name": self.product.product_name if self.product else "",
            "quantity": self.quantity,
            "unit_price": unit_price,
            "total_price": round(unit_price * self.quantity, 2),
            "image": self.product.image if self.product else "",
            "stock_quantity": self.product.stock_quantity if self.product else 0,
            "brand": self.product.brand if self.product else ""
        }


class Order(Base):
    __tablename__ = "orders"

    order_id = Column(String(50), primary_key=True)
    customer_id = Column(String(50), ForeignKey("customers.customer_id"), nullable=False)
    order_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    subtotal = Column(Numeric(10, 2), nullable=False)
    discount = Column(Numeric(10, 2), default=0.00, nullable=False)
    total_amount = Column(Numeric(10, 2), nullable=False)
    payment_id = Column(String(50))
    delivery_id = Column(String(50))
    order_status = Column(String(30), default="PLACED", nullable=False)
    cancellation_status = Column(String(30), default="NONE", nullable=False)
    refund_status = Column(String(30), default="NONE", nullable=False)
    shipping_address_id = Column(String(50))
    shipping_address_text = Column(Text)

    customer = relationship("Customer", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    payment = relationship("Payment", back_populates="order", uselist=False, cascade="all, delete-orphan")
    delivery = relationship("Delivery", back_populates="order", uselist=False, cascade="all, delete-orphan")
    returns = relationship("Return", back_populates="order", cascade="all, delete-orphan")
    refunds = relationship("Refund", back_populates="order", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "order_id": self.order_id,
            "customer_id": self.customer_id,
            "customer_name": self.customer.name if self.customer else "",
            "order_date": self.order_date.strftime("%Y-%m-%d %H:%M:%S") if self.order_date else None,
            "subtotal": float(self.subtotal),
            "discount": float(self.discount),
            "total_amount": float(self.total_amount),
            "order_status": self.order_status,
            "cancellation_status": self.cancellation_status,
            "refund_status": self.refund_status,
            "payment_id": self.payment_id,
            "delivery_id": self.delivery_id,
            "shipping_address_id": self.shipping_address_id,
            "shipping_address_text": self.shipping_address_text,
            "items": [item.to_dict() for item in self.items],
            "item_count": sum(item.quantity for item in self.items),
            "payment": self.payment.to_dict() if self.payment else None,
            "delivery": self.delivery.to_dict() if self.delivery else None
        }


class OrderItem(Base):
    __tablename__ = "order_items"

    item_id = Column(String(50), primary_key=True)
    order_id = Column(String(50), ForeignKey("orders.order_id", ondelete="CASCADE"), nullable=False)
    product_id = Column(String(50), nullable=False)
    product_name = Column(String(255), nullable=False)
    quantity = Column(Integer, default=1, nullable=False)
    unit_price = Column(Numeric(10, 2), nullable=False)
    total_price = Column(Numeric(10, 2), nullable=False)
    image = Column(String(500))

    order = relationship("Order", back_populates="items")

    def to_dict(self):
        return {
            "item_id": self.item_id,
            "order_id": self.order_id,
            "product_id": self.product_id,
            "product_name": self.product_name,
            "quantity": self.quantity,
            "unit_price": float(self.unit_price),
            "total_price": float(self.total_price),
            "image": self.image
        }


class Payment(Base):
    __tablename__ = "payments"

    payment_id = Column(String(50), primary_key=True)
    order_id = Column(String(50), ForeignKey("orders.order_id", ondelete="CASCADE"), nullable=False)
    payment_method = Column(String(50), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    payment_status = Column(String(30), default="COMPLETED", nullable=False)
    transaction_id = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    order = relationship("Order", back_populates="payment")

    def to_dict(self):
        return {
            "payment_id": self.payment_id,
            "order_id": self.order_id,
            "payment_method": self.payment_method,
            "amount": float(self.amount),
            "payment_status": self.payment_status,
            "transaction_id": self.transaction_id,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else None
        }


class Delivery(Base):
    __tablename__ = "deliveries"

    delivery_id = Column(String(50), primary_key=True)
    order_id = Column(String(50), ForeignKey("orders.order_id", ondelete="CASCADE"), nullable=False)
    tracking_number = Column(String(100), unique=True, nullable=False)
    carrier = Column(String(100), default="SphereLogistics", nullable=False)
    delivery_status = Column(String(30), default="PENDING", nullable=False)
    estimated_delivery = Column(DateTime)
    current_location = Column(String(150))
    shipped_at = Column(DateTime)
    delivered_at = Column(DateTime)

    order = relationship("Order", back_populates="delivery")

    def to_dict(self):
        return {
            "delivery_id": self.delivery_id,
            "order_id": self.order_id,
            "tracking_number": self.tracking_number,
            "carrier": self.carrier,
            "delivery_status": self.delivery_status,
            "estimated_delivery": self.estimated_delivery.strftime("%Y-%m-%d %H:%M:%S") if self.estimated_delivery else None,
            "current_location": self.current_location,
            "shipped_at": self.shipped_at.strftime("%Y-%m-%d %H:%M:%S") if self.shipped_at else None,
            "delivered_at": self.delivered_at.strftime("%Y-%m-%d %H:%M:%S") if self.delivered_at else None
        }


class Return(Base):
    __tablename__ = "returns"

    return_id = Column(String(50), primary_key=True)
    order_id = Column(String(50), ForeignKey("orders.order_id", ondelete="CASCADE"), nullable=False)
    customer_id = Column(String(50), ForeignKey("customers.customer_id"), nullable=False)
    reason = Column(String(255), nullable=False)
    return_status = Column(String(30), default="REQUESTED", nullable=False)
    requested_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    order = relationship("Order", back_populates="returns")
    customer = relationship("Customer", back_populates="returns")

    def to_dict(self):
        return {
            "return_id": self.return_id,
            "order_id": self.order_id,
            "customer_id": self.customer_id,
            "customer_name": self.customer.name if self.customer else "",
            "reason": self.reason,
            "return_status": self.return_status,
            "requested_at": self.requested_at.strftime("%Y-%m-%d %H:%M:%S") if self.requested_at else None,
            "updated_at": self.updated_at.strftime("%Y-%m-%d %H:%M:%S") if self.updated_at else None
        }


class Refund(Base):
    __tablename__ = "refunds"

    refund_id = Column(String(50), primary_key=True)
    order_id = Column(String(50), ForeignKey("orders.order_id", ondelete="CASCADE"), nullable=False)
    payment_id = Column(String(50))
    amount = Column(Numeric(10, 2), nullable=False)
    refund_status = Column(String(30), default="REQUESTED", nullable=False)
    processed_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    order = relationship("Order", back_populates="refunds")

    def to_dict(self):
        return {
            "refund_id": self.refund_id,
            "order_id": self.order_id,
            "payment_id": self.payment_id,
            "amount": float(self.amount),
            "refund_status": self.refund_status,
            "processed_at": self.processed_at.strftime("%Y-%m-%d %H:%M:%S") if self.processed_at else None
        }


class Review(Base):
    __tablename__ = "reviews"

    review_id = Column(String(50), primary_key=True)
    product_id = Column(String(50), ForeignKey("products.product_id", ondelete="CASCADE"), nullable=False)
    customer_id = Column(String(50), ForeignKey("customers.customer_id"))
    customer_name = Column(String(100), nullable=False)
    rating = Column(Integer, default=5, nullable=False)
    comment = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    product = relationship("Product", back_populates="reviews")

    def to_dict(self):
        return {
            "review_id": self.review_id,
            "product_id": self.product_id,
            "customer_id": self.customer_id,
            "customer_name": self.customer_name,
            "rating": self.rating,
            "comment": self.comment,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else None
        }


class AuditLog(Base):
    __tablename__ = "audit_logs"

    log_id = Column(String(50), primary_key=True)
    action = Column(String(100), nullable=False)
    agent_id = Column(String(100))
    customer_id = Column(String(50))
    tool_name = Column(String(100))
    arguments_json = Column(Text)
    policy_decision = Column(String(50))
    policy_reason = Column(Text)
    execution_status = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            "log_id": self.log_id,
            "action": self.action,
            "agent_id": self.agent_id,
            "customer_id": self.customer_id,
            "tool_name": self.tool_name,
            "arguments_json": self.arguments_json,
            "policy_decision": self.policy_decision,
            "policy_reason": self.policy_reason,
            "execution_status": self.execution_status,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else None
        }


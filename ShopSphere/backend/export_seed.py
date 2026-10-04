import os
from backend.database import SessionLocal
from backend.models import (
    Customer, Address, Category, Product, Order, OrderItem, Payment, Delivery, Return, Refund
)

def export_seed():
    session = SessionLocal()
    lines = [
        "-- ShopSphere SQL Seed Data",
        "-- Auto-generated for direct MySQL import",
        "USE shopsphere_db;\n"
    ]

    # Customers
    lines.append("-- 1. Customers")
    for c in session.query(Customer).all():
        lines.append(f"INSERT INTO customers (customer_id, name, email, phone, password_hash, account_status, created_at) "
                     f"VALUES ('{c.customer_id}', '{c.name}', '{c.email}', '{c.phone}', '{c.password_hash}', '{c.account_status}', '{c.created_at}');")

    # Addresses
    lines.append("\n-- 2. Addresses")
    for a in session.query(Address).all():
        is_def = 1 if a.is_default else 0
        lines.append(f"INSERT INTO addresses (address_id, customer_id, full_name, phone, address_line, city, state, postal_code, address_type, is_default, created_at) "
                     f"VALUES ('{a.address_id}', '{a.customer_id}', '{a.full_name}', '{a.phone}', '{a.address_line}', '{a.city}', '{a.state}', '{a.postal_code}', '{a.address_type}', {is_def}, '{a.created_at}');")

    # Categories
    lines.append("\n-- 3. Categories")
    for cat in session.query(Category).all():
        lines.append(f"INSERT INTO categories (category_id, name, slug, description, icon, image) "
                     f"VALUES ('{cat.category_id}', '{cat.name}', '{cat.slug}', '{cat.description}', '{cat.icon}', '{cat.image}');")

    # Products
    lines.append("\n-- 4. Products")
    for p in session.query(Product).all():
        desc = p.description.replace("'", "''")
        pname = p.product_name.replace("'", "''")
        lines.append(f"INSERT INTO products (product_id, product_name, description, category, subcategory, brand, price, discount, final_price, stock_quantity, rating, review_count, seller, image, status, created_at) "
                     f"VALUES ('{p.product_id}', '{pname}', '{desc}', '{p.category}', '{p.subcategory}', '{p.brand}', {p.price}, {p.discount}, {p.final_price}, {p.stock_quantity}, {p.rating}, {p.review_count}, '{p.seller}', '{p.image}', '{p.status}', '{p.created_at}');")

    # Orders
    lines.append("\n-- 5. Orders")
    for o in session.query(Order).all():
        lines.append(f"INSERT INTO orders (order_id, customer_id, order_date, subtotal, discount, total_amount, payment_id, delivery_id, order_status, cancellation_status, refund_status, shipping_address_id, shipping_address_text) "
                     f"VALUES ('{o.order_id}', '{o.customer_id}', '{o.order_date}', {o.subtotal}, {o.discount}, {o.total_amount}, '{o.payment_id}', '{o.delivery_id}', '{o.order_status}', '{o.cancellation_status}', '{o.refund_status}', '{o.shipping_address_id}', '{o.shipping_address_text}');")

    # Order Items
    lines.append("\n-- 6. Order Items")
    for oi in session.query(OrderItem).all():
        pname = oi.product_name.replace("'", "''")
        lines.append(f"INSERT INTO order_items (item_id, order_id, product_id, product_name, quantity, unit_price, total_price, image) "
                     f"VALUES ('{oi.item_id}', '{oi.order_id}', '{oi.product_id}', '{pname}', {oi.quantity}, {oi.unit_price}, {oi.total_price}, '{oi.image}');")

    # Payments
    lines.append("\n-- 7. Payments")
    for py in session.query(Payment).all():
        lines.append(f"INSERT INTO payments (payment_id, order_id, payment_method, amount, payment_status, transaction_id, created_at) "
                     f"VALUES ('{py.payment_id}', '{py.order_id}', '{py.payment_method}', {py.amount}, '{py.payment_status}', '{py.transaction_id}', '{py.created_at}');")

    # Deliveries
    lines.append("\n-- 8. Deliveries")
    for d in session.query(Delivery).all():
        shipped = f"'{d.shipped_at}'" if d.shipped_at else "NULL"
        delivered = f"'{d.delivered_at}'" if d.delivered_at else "NULL"
        lines.append(f"INSERT INTO deliveries (delivery_id, order_id, tracking_number, carrier, delivery_status, estimated_delivery, current_location, shipped_at, delivered_at) "
                     f"VALUES ('{d.delivery_id}', '{d.order_id}', '{d.tracking_number}', '{d.carrier}', '{d.delivery_status}', '{d.estimated_delivery}', '{d.current_location}', {shipped}, {delivered});")

    # Returns
    lines.append("\n-- 9. Returns")
    for r in session.query(Return).all():
        lines.append(f"INSERT INTO returns (return_id, order_id, customer_id, reason, return_status, requested_at, updated_at) "
                     f"VALUES ('{r.return_id}', '{r.order_id}', '{r.customer_id}', '{r.reason}', '{r.return_status}', '{r.requested_at}', '{r.updated_at}');")

    # Refunds
    lines.append("\n-- 10. Refunds")
    for rf in session.query(Refund).all():
        lines.append(f"INSERT INTO refunds (refund_id, order_id, payment_id, amount, refund_status, processed_at) "
                     f"VALUES ('{rf.refund_id}', '{rf.order_id}', '{rf.payment_id}', {rf.amount}, '{rf.refund_status}', '{rf.processed_at}');")

    out_file = os.path.join(os.path.dirname(__file__), "..", "database", "seed.sql")
    with open(out_file, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"Exported {len(lines)} lines to database/seed.sql")
    session.close()

if __name__ == "__main__":
    export_seed()


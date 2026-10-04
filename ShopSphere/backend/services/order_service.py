import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy import desc, func
from backend.database import SessionLocal
from backend.models import (
    Order, OrderItem, Payment, Delivery, Return, Refund, Product, Address, Cart, CartItem, Customer
)

class OrderService:
    @staticmethod
    def create_order(customer_id, address_id, payment_method="Credit Card", custom_items=None):
        session = SessionLocal()
        try:
            # 1. Fetch address
            address = session.query(Address).filter(
                Address.address_id == address_id,
                Address.customer_id == customer_id
            ).first()
            if not address:
                # Fallback to any default address of user
                address = session.query(Address).filter(Address.customer_id == customer_id, Address.is_default == True).first()
            if not address:
                address = session.query(Address).filter(Address.customer_id == customer_id).first()

            shipping_text = address.formatted if address else "Standard Default Delivery Address, ShopSphere Network"
            shipping_addr_id = address.address_id if address else "ADDR_DEFAULT"

            # 2. Gather items
            items_to_order = []
            if custom_items:
                for ci in custom_items:
                    prod = session.query(Product).filter(Product.product_id == ci["product_id"]).first()
                    if prod and prod.stock_quantity >= ci["quantity"]:
                        items_to_order.append({
                            "product": prod,
                            "quantity": int(ci["quantity"]),
                            "unit_price": float(prod.final_price),
                            "total_price": float(prod.final_price) * int(ci["quantity"])
                        })
            else:
                cart = session.query(Cart).filter(Cart.customer_id == customer_id).first()
                if not cart or not cart.items:
                    return {"success": False, "message": "Your cart is empty."}

                for item in cart.items:
                    if item.product.stock_quantity < item.quantity:
                        return {"success": False, "message": f"Product '{item.product.product_name}' only has {item.product.stock_quantity} units available."}
                    items_to_order.append({
                        "product": item.product,
                        "quantity": item.quantity,
                        "unit_price": float(item.product.final_price),
                        "total_price": float(item.product.final_price) * item.quantity
                    })

            if not items_to_order:
                return {"success": False, "message": "No valid products to order."}

            subtotal = sum(i["unit_price"] * i["quantity"] for i in items_to_order)
            discount = 0.0
            total_amount = subtotal - discount

            order_count = session.query(Order).count()
            order_id = f"ORD{order_count + 1001}"
            now = datetime.utcnow()

            # 3. Create Order
            order = Order(
                order_id=order_id,
                customer_id=customer_id,
                order_date=now,
                subtotal=Decimal(str(subtotal)),
                discount=Decimal(str(discount)),
                total_amount=Decimal(str(total_amount)),
                payment_id=f"PAY{order_count + 1001}",
                delivery_id=f"DEL{order_count + 1001}",
                order_status="PLACED",
                cancellation_status="NONE",
                refund_status="NONE",
                shipping_address_id=shipping_addr_id,
                shipping_address_text=shipping_text
            )
            session.add(order)
            session.flush()

            # 4. Create Order Items & Decrement Stock
            for idx, item in enumerate(items_to_order, start=1):
                oi = OrderItem(
                    item_id=f"OITM{order_id[3:]}{idx:02d}",
                    order_id=order_id,
                    product_id=item["product"].product_id,
                    product_name=item["product"].product_name,
                    quantity=item["quantity"],
                    unit_price=Decimal(str(item["unit_price"])),
                    total_price=Decimal(str(item["total_price"])),
                    image=item["product"].image
                )
                session.add(oi)
                # Decrement stock
                item["product"].stock_quantity = max(0, item["product"].stock_quantity - item["quantity"])

            # 5. Create Payment record
            payment = Payment(
                payment_id=f"PAY{order_count + 1001}",
                order_id=order_id,
                payment_method=payment_method,
                amount=Decimal(str(total_amount)),
                payment_status="COMPLETED" if payment_method != "Cash on Delivery" else "PENDING",
                transaction_id=f"TXN{uuid.uuid4().hex[:12].upper()}",
                created_at=now
            )
            session.add(payment)

            # 6. Create Delivery record
            tracking_num = f"TRK{uuid.uuid4().hex[:8].upper()}"
            delivery = Delivery(
                delivery_id=f"DEL{order_count + 1001}",
                order_id=order_id,
                tracking_number=tracking_num,
                carrier="SphereExpress",
                delivery_status="PENDING",
                estimated_delivery=now + timedelta(days=3),
                current_location="Origin Fulfillment Center",
                shipped_at=None,
                delivered_at=None
            )
            session.add(delivery)

            # 7. Clear cart
            cart = session.query(Cart).filter(Cart.customer_id == customer_id).first()
            if cart:
                session.query(CartItem).filter(CartItem.cart_id == cart.cart_id).delete()

            session.commit()
            return {
                "success": True,
                "message": "Order placed successfully!",
                "order_id": order_id,
                "order": order.to_dict()
            }
        except Exception as e:
            session.rollback()
            return {"success": False, "message": str(e)}
        finally:
            session.close()

    @staticmethod
    def get_order_by_id(order_id, customer_id=None):
        session = SessionLocal()
        try:
            query = session.query(Order).filter(Order.order_id == order_id)
            if customer_id:
                query = query.filter(Order.customer_id == customer_id)
            order = query.first()
            if not order:
                return None
            data = order.to_dict()
            # Attach return info if exists
            ret = session.query(Return).filter(Return.order_id == order_id).first()
            data["return_request"] = ret.to_dict() if ret else None
            # Attach refund info if exists
            ref = session.query(Refund).filter(Refund.order_id == order_id).first()
            data["refund_record"] = ref.to_dict() if ref else None
            return data
        finally:
            session.close()

    @staticmethod
    def get_orders_for_customer(customer_id, status_filter=None):
        session = SessionLocal()
        try:
            query = session.query(Order).filter(Order.customer_id == customer_id)
            if status_filter and status_filter.upper() != "ALL":
                query = query.filter(Order.order_status == status_filter.upper())
            orders = query.order_by(desc(Order.order_date)).all()
            return [o.to_dict() for o in orders]
        finally:
            session.close()

    @staticmethod
    def get_order_status(order_id):
        session = SessionLocal()
        try:
            order = session.query(Order).filter(Order.order_id == order_id).first()
            if not order:
                return {"found": False, "message": f"Order {order_id} not found."}
            return {
                "found": True,
                "order_id": order.order_id,
                "order_status": order.order_status,
                "cancellation_status": order.cancellation_status,
                "refund_status": order.refund_status,
                "total_amount": float(order.total_amount),
                "order_date": order.order_date.strftime("%Y-%m-%d %H:%M:%S") if order.order_date else None,
                "delivery_status": order.delivery.delivery_status if order.delivery else "UNKNOWN"
            }
        finally:
            session.close()

    @staticmethod
    def cancel_order(order_id, customer_id=None, reason="Cancelled by customer"):
        session = SessionLocal()
        try:
            query = session.query(Order).filter(Order.order_id == order_id)
            if customer_id:
                query = query.filter(Order.customer_id == customer_id)
            order = query.first()
            if not order:
                return {"success": False, "message": f"Order {order_id} not found or access denied."}

            # Cancellation rules:
            # PLACED -> cancellable
            # CONFIRMED -> cancellable
            # PACKED -> restricted
            # SHIPPED / OUT_FOR_DELIVERY / DELIVERED -> not cancellable
            non_cancellable = ["SHIPPED", "OUT_FOR_DELIVERY", "DELIVERED", "CANCELLED", "RETURN_REQUESTED", "RETURNED", "REFUNDED"]
            if order.order_status in non_cancellable:
                return {
                    "success": False,
                    "message": f"Order cannot be cancelled because its current status is '{order.order_status}'. Cancellation is only permitted before shipment."
                }

            if order.order_status == "PACKED":
                return {
                    "success": False,
                    "message": "Order is already PACKED at the warehouse. Automated cancellation is restricted. Please contact customer support for manual assistance."
                }

            # Perform cancellation
            order.order_status = "CANCELLED"
            order.cancellation_status = "CANCELLED_BY_CUSTOMER"

            # Update delivery status
            if order.delivery:
                order.delivery.delivery_status = "CANCELLED"

            # Restore stock
            for item in order.items:
                prod = session.query(Product).filter(Product.product_id == item.product_id).first()
                if prod:
                    prod.stock_quantity += item.quantity

            # If payment was completed, schedule refund
            if order.payment and order.payment.payment_status == "COMPLETED":
                order.refund_status = "PENDING"
                refund = Refund(
                    refund_id=f"REF{uuid.uuid4().hex[:8].upper()}",
                    order_id=order.order_id,
                    payment_id=order.payment.payment_id,
                    amount=order.total_amount,
                    refund_status="PENDING",
                    processed_at=datetime.utcnow()
                )
                session.add(refund)

            session.commit()
            return {
                "success": True,
                "order_id": order.order_id,
                "order_status": "CANCELLED",
                "message": f"Order {order.order_id} has been successfully cancelled. Refund of ₹{float(order.total_amount):,.2f} has been initiated."
            }
        except Exception as e:
            session.rollback()
            return {"success": False, "message": str(e)}
        finally:
            session.close()

    @staticmethod
    def get_delivery_status(order_id):
        session = SessionLocal()
        try:
            delivery = session.query(Delivery).filter(Delivery.order_id == order_id).first()
            if not delivery:
                return {"found": False, "message": f"Delivery record for order {order_id} not found."}
            return {
                "found": True,
                "delivery": delivery.to_dict()
            }
        finally:
            session.close()

    @staticmethod
    def get_tracking_details(order_id):
        session = SessionLocal()
        try:
            order = session.query(Order).filter(Order.order_id == order_id).first()
            if not order or not order.delivery:
                return {"found": False, "message": f"Tracking details for order {order_id} not found."}

            delivery = order.delivery
            # Generate realistic tracking checkpoints
            checkpoints = [
                {"stage": "Order Placed", "completed": True, "date": order.order_date.strftime("%Y-%m-%d %H:%M:%S") if order.order_date else "N/A"},
                {"stage": "Confirmed", "completed": order.order_status not in ["PLACED", "CANCELLED"], "date": (order.order_date + timedelta(hours=2)).strftime("%Y-%m-%d %H:%M:%S") if order.order_date else "N/A"},
                {"stage": "Packed", "completed": order.order_status in ["PACKED", "SHIPPED", "OUT_FOR_DELIVERY", "DELIVERED", "RETURN_REQUESTED", "RETURNED", "REFUNDED"], "date": (order.order_date + timedelta(hours=8)).strftime("%Y-%m-%d %H:%M:%S") if order.order_date else "N/A"},
                {"stage": "Shipped", "completed": order.order_status in ["SHIPPED", "OUT_FOR_DELIVERY", "DELIVERED", "RETURN_REQUESTED", "RETURNED", "REFUNDED"], "date": delivery.shipped_at.strftime("%Y-%m-%d %H:%M:%S") if delivery.shipped_at else "In progress"},
                {"stage": "Out for Delivery", "completed": order.order_status in ["OUT_FOR_DELIVERY", "DELIVERED", "RETURN_REQUESTED", "RETURNED", "REFUNDED"], "date": "On delivery vehicle" if order.order_status == "OUT_FOR_DELIVERY" else ("Delivered" if order.order_status == "DELIVERED" else "Pending")},
                {"stage": "Delivered", "completed": order.order_status in ["DELIVERED", "RETURN_REQUESTED", "RETURNED", "REFUNDED"], "date": delivery.delivered_at.strftime("%Y-%m-%d %H:%M:%S") if delivery.delivered_at else "Expected soon"}
            ]

            return {
                "found": True,
                "order_id": order.order_id,
                "order_status": order.order_status,
                "carrier": delivery.carrier,
                "tracking_number": delivery.tracking_number,
                "delivery_status": delivery.delivery_status,
                "current_location": delivery.current_location,
                "estimated_delivery": delivery.estimated_delivery.strftime("%Y-%m-%d %H:%M:%S") if delivery.estimated_delivery else None,
                "checkpoints": checkpoints
            }
        finally:
            session.close()

    @staticmethod
    def update_delivery_address(order_id, address_id, customer_id=None):
        session = SessionLocal()
        try:
            query = session.query(Order).filter(Order.order_id == order_id)
            if customer_id:
                query = query.filter(Order.customer_id == customer_id)
            order = query.first()
            if not order:
                return {"success": False, "message": f"Order {order_id} not found."}

            if order.order_status not in ["PLACED", "CONFIRMED"]:
                return {
                    "success": False,
                    "message": f"Delivery address cannot be modified once order is '{order.order_status}'. It can only be changed while PLACED or CONFIRMED."
                }

            address = session.query(Address).filter(Address.address_id == address_id).first()
            if not address:
                return {"success": False, "message": f"Address {address_id} not found."}

            order.shipping_address_id = address.address_id
            order.shipping_address_text = address.formatted
            session.commit()
            return {
                "success": True,
                "order_id": order_id,
                "new_address": address.formatted,
                "message": "Delivery address updated successfully."
            }
        except Exception as e:
            session.rollback()
            return {"success": False, "message": str(e)}
        finally:
            session.close()

    @staticmethod
    def get_payment_status(order_id):
        session = SessionLocal()
        try:
            payment = session.query(Payment).filter(Payment.order_id == order_id).first()
            if not payment:
                return {"found": False, "message": f"Payment record for order {order_id} not found."}
            return {
                "found": True,
                "payment": payment.to_dict()
            }
        finally:
            session.close()

    @staticmethod
    def process_refund(order_id, amount=None):
        session = SessionLocal()
        try:
            order = session.query(Order).filter(Order.order_id == order_id).first()
            if not order:
                return {"success": False, "message": f"Order {order_id} not found."}

            if order.refund_status == "PROCESSED":
                return {"success": False, "message": f"Order {order_id} has already been refunded in full."}

            refund_amt = Decimal(str(amount)) if amount is not None else order.total_amount
            if refund_amt > order.total_amount:
                return {"success": False, "message": f"Refund amount ₹{float(refund_amt)} cannot exceed order total ₹{float(order.total_amount)}."}

            existing_ref = session.query(Refund).filter(Refund.order_id == order_id).first()
            if existing_ref:
                existing_ref.refund_status = "PROCESSED"
                existing_ref.amount = refund_amt
                existing_ref.processed_at = datetime.utcnow()
                refund_id = existing_ref.refund_id
            else:
                refund_id = f"REF{uuid.uuid4().hex[:8].upper()}"
                new_ref = Refund(
                    refund_id=refund_id,
                    order_id=order_id,
                    payment_id=order.payment_id,
                    amount=refund_amt,
                    refund_status="PROCESSED",
                    processed_at=datetime.utcnow()
                )
                session.add(new_ref)

            order.refund_status = "PROCESSED"
            order.order_status = "REFUNDED"
            if order.payment:
                order.payment.payment_status = "REFUNDED"

            session.commit()
            return {
                "success": True,
                "refund_id": refund_id,
                "order_id": order_id,
                "amount": float(refund_amt),
                "refund_status": "PROCESSED",
                "message": f"Refund of ₹{float(refund_amt):,.2f} processed successfully for order {order_id}."
            }
        except Exception as e:
            session.rollback()
            return {"success": False, "message": str(e)}
        finally:
            session.close()

    @staticmethod
    def cancel_payment(order_id):
        session = SessionLocal()
        try:
            payment = session.query(Payment).filter(Payment.order_id == order_id).first()
            if not payment:
                return {"success": False, "message": f"Payment for order {order_id} not found."}

            payment.payment_status = "CANCELLED"
            session.commit()
            return {
                "success": True,
                "order_id": order_id,
                "payment_id": payment.payment_id,
                "payment_status": "CANCELLED",
                "message": f"Payment {payment.payment_id} for order {order_id} cancelled."
            }
        finally:
            session.close()

    @staticmethod
    def request_return(order_id, reason, customer_id=None):
        session = SessionLocal()
        try:
            query = session.query(Order).filter(Order.order_id == order_id)
            if customer_id:
                query = query.filter(Order.customer_id == customer_id)
            order = query.first()
            if not order:
                return {"success": False, "message": f"Order {order_id} not found."}

            if order.order_status not in ["DELIVERED"]:
                return {
                    "success": False,
                    "message": f"Returns can only be requested for orders that have been DELIVERED. Current status: '{order.order_status}'."
                }

            # Check if return already exists
            existing_ret = session.query(Return).filter(Return.order_id == order_id).first()
            if existing_ret:
                return {
                    "success": False,
                    "message": f"Return request already exists for order {order_id} with status '{existing_ret.return_status}'."
                }

            ret_id = f"RET{uuid.uuid4().hex[:8].upper()}"
            ret = Return(
                return_id=ret_id,
                order_id=order_id,
                customer_id=order.customer_id,
                reason=reason,
                return_status="REQUESTED",
                requested_at=datetime.utcnow()
            )
            session.add(ret)
            order.order_status = "RETURN_REQUESTED"
            order.refund_status = "REQUESTED"

            session.commit()
            return {
                "success": True,
                "return_id": ret_id,
                "order_id": order_id,
                "return_status": "REQUESTED",
                "message": f"Return request registered for order {order_id}. Pickup will be arranged within 48 hours."
            }
        except Exception as e:
            session.rollback()
            return {"success": False, "message": str(e)}
        finally:
            session.close()

    @staticmethod
    def check_return_status(order_id):
        session = SessionLocal()
        try:
            ret = session.query(Return).filter(Return.order_id == order_id).first()
            if not ret:
                return {"found": False, "message": f"No return request found for order {order_id}."}
            return {
                "found": True,
                "return_details": ret.to_dict()
            }
        finally:
            session.close()

    @staticmethod
    def approve_return(return_id):
        session = SessionLocal()
        try:
            ret = session.query(Return).filter(Return.return_id == return_id).first()
            if not ret:
                return {"success": False, "message": f"Return request {return_id} not found."}

            ret.return_status = "APPROVED"
            if ret.order:
                ret.order.order_status = "RETURNED"
                # Trigger automatic refund
                OrderService.process_refund(ret.order_id)

            session.commit()
            return {
                "success": True,
                "return_id": return_id,
                "return_status": "APPROVED",
                "message": f"Return {return_id} approved. Pickup scheduled and refund processing initiated."
            }
        finally:
            session.close()

    @staticmethod
    def get_all_orders_admin(status=None, page=1, per_page=20):
        session = SessionLocal()
        try:
            query = session.query(Order)
            if status and status.upper() != "ALL":
                query = query.filter(Order.order_status == status.upper())
            total = query.count()
            orders = query.order_by(desc(Order.order_date)).offset((page - 1) * per_page).limit(per_page).all()
            return {
                "orders": [o.to_dict() for o in orders],
                "total": total,
                "page": page,
                "per_page": per_page,
                "total_pages": (total + per_page - 1) // per_page
            }
        finally:
            session.close()

    @staticmethod
    def update_order_status_admin(order_id, new_status):
        session = SessionLocal()
        try:
            order = session.query(Order).filter(Order.order_id == order_id).first()
            if not order:
                return {"success": False, "message": f"Order {order_id} not found."}

            valid_statuses = ["PLACED", "CONFIRMED", "PACKED", "SHIPPED", "OUT_FOR_DELIVERY", "DELIVERED", "CANCELLED", "RETURN_REQUESTED", "RETURNED", "REFUNDED"]
            if new_status not in valid_statuses:
                return {"success": False, "message": f"Invalid status {new_status}."}

            order.order_status = new_status
            if order.delivery:
                if new_status == "SHIPPED" and not order.delivery.shipped_at:
                    order.delivery.shipped_at = datetime.utcnow()
                    order.delivery.delivery_status = "SHIPPED"
                    order.delivery.current_location = "Regional Distribution Facility"
                elif new_status == "OUT_FOR_DELIVERY":
                    order.delivery.delivery_status = "OUT_FOR_DELIVERY"
                    order.delivery.current_location = "Out with Delivery Agent"
                elif new_status == "DELIVERED" and not order.delivery.delivered_at:
                    order.delivery.delivered_at = datetime.utcnow()
                    order.delivery.delivery_status = "DELIVERED"
                    order.delivery.current_location = "Delivered to Customer"
                elif new_status == "CANCELLED":
                    order.delivery.delivery_status = "CANCELLED"

            session.commit()
            return {"success": True, "order": order.to_dict(), "message": f"Status updated to {new_status}."}
        finally:
            session.close()

    @staticmethod
    def get_admin_metrics():
        session = SessionLocal()
        try:
            total_products = session.query(Product).count()
            total_customers = session.query(Customer).count()
            total_orders = session.query(Order).count()
            total_revenue = session.query(func.sum(Order.total_amount)).filter(Order.order_status != "CANCELLED").scalar() or 0.0
            pending_orders = session.query(Order).filter(Order.order_status.in_(["PLACED", "CONFIRMED", "PACKED"])).count()
            pending_returns = session.query(Return).filter(Return.return_status == "REQUESTED").count()
            pending_refunds = session.query(Refund).filter(Refund.refund_status.in_(["REQUESTED", "PENDING"])).count()

            return {
                "total_products": total_products,
                "total_customers": total_customers,
                "total_orders": total_orders,
                "total_revenue": float(total_revenue),
                "pending_orders": pending_orders,
                "pending_returns": pending_returns,
                "pending_refunds": pending_refunds
            }
        finally:
            session.close()


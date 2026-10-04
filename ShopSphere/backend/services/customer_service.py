import uuid
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from backend.database import SessionLocal
from backend.models import Customer, Address, Order, Review

class CustomerService:
    @staticmethod
    def register_customer(name, email, phone, password):
        session = SessionLocal()
        try:
            # Check if email already exists
            existing = session.query(Customer).filter(Customer.email == email.lower().strip()).first()
            if existing:
                return {"success": False, "message": "Email already registered."}

            cid = f"CUS{session.query(Customer).count() + 1001}"
            customer = Customer(
                customer_id=cid,
                name=name.strip(),
                email=email.lower().strip(),
                phone=phone.strip(),
                password_hash=generate_password_hash(password),
                account_status="ACTIVE",
                created_at=datetime.utcnow()
            )
            session.add(customer)
            session.commit()
            return {"success": True, "customer": customer.to_dict()}
        except Exception as e:
            session.rollback()
            return {"success": False, "message": str(e)}
        finally:
            session.close()

    @staticmethod
    def authenticate_customer(email, password):
        session = SessionLocal()
        try:
            customer = session.query(Customer).filter(Customer.email == email.lower().strip()).first()
            if not customer:
                return {"success": False, "message": "Invalid email or password."}

            if not check_password_hash(customer.password_hash, password):
                return {"success": False, "message": "Invalid email or password."}

            if customer.account_status != "ACTIVE":
                return {"success": False, "message": f"Account is {customer.account_status}. Please contact support."}

            return {"success": True, "customer": customer.to_dict()}
        finally:
            session.close()

    @staticmethod
    def get_customer_profile(customer_id):
        session = SessionLocal()
        try:
            customer = session.query(Customer).filter(Customer.customer_id == customer_id).first()
            if not customer:
                return None
            data = customer.to_dict()
            data["order_count"] = session.query(Order).filter(Order.customer_id == customer_id).count()
            data["address_count"] = session.query(Address).filter(Address.customer_id == customer_id).count()
            return data
        finally:
            session.close()

    @staticmethod
    def update_customer_profile(customer_id, fields):
        session = SessionLocal()
        try:
            customer = session.query(Customer).filter(Customer.customer_id == customer_id).first()
            if not customer:
                return {"success": False, "message": f"Customer {customer_id} not found."}

            allowed_fields = ["name", "phone"]
            updated = {}
            for field in allowed_fields:
                if field in fields and fields[field]:
                    setattr(customer, field, fields[field])
                    updated[field] = fields[field]

            session.commit()
            return {
                "success": True,
                "customer": customer.to_dict(),
                "updated_fields": updated,
                "message": "Profile updated successfully."
            }
        except Exception as e:
            session.rollback()
            return {"success": False, "message": str(e)}
        finally:
            session.close()

    @staticmethod
    def get_customer_addresses(customer_id):
        session = SessionLocal()
        try:
            addresses = session.query(Address).filter(Address.customer_id == customer_id).all()
            return [a.to_dict() for a in addresses]
        finally:
            session.close()

    @staticmethod
    def add_customer_address(customer_id, address_data):
        session = SessionLocal()
        try:
            customer = session.query(Customer).filter(Customer.customer_id == customer_id).first()
            if not customer:
                return {"success": False, "message": "Customer not found."}

            is_default = bool(address_data.get("is_default", False))
            # If default, remove default from others
            if is_default:
                session.query(Address).filter(Address.customer_id == customer_id).update({"is_default": False})

            aid = f"ADDR{session.query(Address).count() + 1001}"
            addr = Address(
                address_id=aid,
                customer_id=customer_id,
                full_name=address_data.get("full_name", customer.name),
                phone=address_data.get("phone", customer.phone),
                address_line=address_data.get("address_line", ""),
                city=address_data.get("city", ""),
                state=address_data.get("state", ""),
                postal_code=address_data.get("postal_code", ""),
                address_type=address_data.get("address_type", "Home"),
                is_default=is_default or session.query(Address).filter(Address.customer_id == customer_id).count() == 0,
                created_at=datetime.utcnow()
            )
            session.add(addr)
            session.commit()
            return {"success": True, "address": addr.to_dict(), "message": "Address added successfully."}
        except Exception as e:
            session.rollback()
            return {"success": False, "message": str(e)}
        finally:
            session.close()

    @staticmethod
    def update_customer_address(customer_id, address_id, address_data):
        session = SessionLocal()
        try:
            addr = session.query(Address).filter(
                Address.address_id == address_id,
                Address.customer_id == customer_id
            ).first()
            if not addr:
                return {"success": False, "message": "Address not found."}

            if address_data.get("is_default"):
                session.query(Address).filter(Address.customer_id == customer_id).update({"is_default": False})
                addr.is_default = True

            for field in ["full_name", "phone", "address_line", "city", "state", "postal_code", "address_type"]:
                if field in address_data and address_data[field] is not None:
                    setattr(addr, field, address_data[field])

            session.commit()
            return {"success": True, "address": addr.to_dict(), "message": "Address updated successfully."}
        except Exception as e:
            session.rollback()
            return {"success": False, "message": str(e)}
        finally:
            session.close()

    @staticmethod
    def delete_customer_address(customer_id, address_id):
        session = SessionLocal()
        try:
            addr = session.query(Address).filter(
                Address.address_id == address_id,
                Address.customer_id == customer_id
            ).first()
            if not addr:
                return {"success": False, "message": "Address not found."}

            session.delete(addr)
            session.commit()
            return {"success": True, "message": "Address deleted successfully."}
        except Exception as e:
            session.rollback()
            return {"success": False, "message": str(e)}
        finally:
            session.close()

    @staticmethod
    def set_default_address(customer_id, address_id):
        session = SessionLocal()
        try:
            addr = session.query(Address).filter(
                Address.address_id == address_id,
                Address.customer_id == customer_id
            ).first()
            if not addr:
                return {"success": False, "message": "Address not found."}

            session.query(Address).filter(Address.customer_id == customer_id).update({"is_default": False})
            addr.is_default = True
            session.commit()
            return {"success": True, "message": "Default address updated.", "address": addr.to_dict()}
        finally:
            session.close()

    # Sensitive operations
    @staticmethod
    def get_customer_pii(customer_id):
        """HIGH risk operation: returns full customer Personally Identifiable Information."""
        session = SessionLocal()
        try:
            customer = session.query(Customer).filter(Customer.customer_id == customer_id).first()
            if not customer:
                return {"success": False, "message": f"Customer {customer_id} not found."}

            addresses = session.query(Address).filter(Address.customer_id == customer_id).all()
            orders = session.query(Order).filter(Order.customer_id == customer_id).all()
            return {
                "success": True,
                "customer_id": customer.customer_id,
                "name": customer.name,
                "email": customer.email,
                "phone": customer.phone,
                "account_status": customer.account_status,
                "created_at": customer.created_at.strftime("%Y-%m-%d %H:%M:%S") if customer.created_at else None,
                "addresses": [a.to_dict() for a in addresses],
                "total_orders": len(orders),
                "total_spend": sum(float(o.total_amount) for o in orders)
            }
        finally:
            session.close()

    @staticmethod
    def export_customer_data(customer_id):
        """CRITICAL risk operation: exports entire data package."""
        session = SessionLocal()
        try:
            customer = session.query(Customer).filter(Customer.customer_id == customer_id).first()
            if not customer:
                return {"success": False, "message": f"Customer {customer_id} not found."}

            addresses = session.query(Address).filter(Address.customer_id == customer_id).all()
            orders = session.query(Order).filter(Order.customer_id == customer_id).all()
            reviews = session.query(Review).filter(Review.customer_id == customer_id).all()
            return {
                "success": True,
                "export_id": f"EXP-{uuid.uuid4().hex[:8].upper()}",
                "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
                "customer": customer.to_dict(),
                "addresses": [a.to_dict() for a in addresses],
                "orders": [o.to_dict() for o in orders],
                "reviews": [r.to_dict() for r in reviews]
            }
        finally:
            session.close()

    @staticmethod
    def delete_customer_account(customer_id):
        """CRITICAL risk operation: deactivates customer account."""
        session = SessionLocal()
        try:
            customer = session.query(Customer).filter(Customer.customer_id == customer_id).first()
            if not customer:
                return {"success": False, "message": f"Customer {customer_id} not found."}

            customer.account_status = "DEACTIVATED"
            session.commit()
            return {
                "success": True,
                "customer_id": customer_id,
                "account_status": "DEACTIVATED",
                "message": f"Customer account {customer_id} has been deactivated."
            }
        except Exception as e:
            session.rollback()
            return {"success": False, "message": str(e)}
        finally:
            session.close()

    @staticmethod
    def get_all_customers_admin():
        session = SessionLocal()
        try:
            customers = session.query(Customer).all()
            result = []
            for c in customers:
                cd = c.to_dict()
                cd["total_orders"] = session.query(Order).filter(Order.customer_id == c.customer_id).count()
                result.append(cd)
            return result
        finally:
            session.close()


import json
import uuid
from datetime import datetime
from backend.services import policy_service
from backend.services.product_service import ProductService
from backend.services.customer_service import CustomerService
from backend.services.order_service import OrderService
from backend.database import SessionLocal
from backend.models import AuditLog

class ToolRegistry:
    """
    Centralized Tool Registry for ShopSphere.
    Encapsulates all 23 authorized tools with metadata, risk levels, and schemas.
    Enforces the security rule: Chatbot -> Tool Registry -> Policy Service (AegisAI) -> E-commerce API -> DB.
    """

    TOOLS = {
        # 1. Product Tools (LOW)
        "search_products": {
            "name": "search_products",
            "description": "Searches the product catalog for products matching a query or category.",
            "category": "PRODUCT",
            "risk_level": "LOW",
            "endpoint": "/api/products/search",
            "method": "GET",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search term (e.g., 'wireless headphones', 'laptops')"},
                    "category": {"type": "string", "description": "Optional category filter"}
                },
                "required": ["query"]
            },
            "handler": lambda args, ctx: ProductService.search_products(args.get("query", ""), args.get("category"))
        },
        "get_product_details": {
            "name": "get_product_details",
            "description": "Retrieves comprehensive specifications, price, reviews, and stock for a product.",
            "category": "PRODUCT",
            "risk_level": "LOW",
            "endpoint": "/api/products/{product_id}",
            "method": "GET",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_id": {"type": "string", "description": "The product ID (e.g. PRD1001)"}
                },
                "required": ["product_id"]
            },
            "handler": lambda args, ctx: ProductService.get_product_by_id(args.get("product_id"))
        },
        "check_product_stock": {
            "name": "check_product_stock",
            "description": "Checks current warehouse inventory and stock availability for a product.",
            "category": "PRODUCT",
            "risk_level": "LOW",
            "endpoint": "/api/products/{product_id}/stock",
            "method": "GET",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_id": {"type": "string", "description": "The product ID (e.g. PRD1001)"}
                },
                "required": ["product_id"]
            },
            "handler": lambda args, ctx: ProductService.check_product_stock(args.get("product_id"))
        },

        # 2. Customer Tools
        "get_customer_profile": {
            "name": "get_customer_profile",
            "description": "Fetches the customer's account profile information.",
            "category": "CUSTOMER",
            "risk_level": "MEDIUM",
            "endpoint": "/api/customers/{customer_id}/profile",
            "method": "GET",
            "parameters": {
                "type": "object",
                "properties": {
                    "customer_id": {"type": "string", "description": "The customer ID (e.g. CUS1001)"}
                },
                "required": ["customer_id"]
            },
            "handler": lambda args, ctx: CustomerService.get_customer_profile(args.get("customer_id") or ctx.get("customer_id"))
        },
        "update_customer_profile": {
            "name": "update_customer_profile",
            "description": "Updates non-sensitive customer profile fields like name or phone number.",
            "category": "CUSTOMER",
            "risk_level": "MEDIUM",
            "endpoint": "/api/customers/{customer_id}/profile",
            "method": "PUT",
            "parameters": {
                "type": "object",
                "properties": {
                    "customer_id": {"type": "string", "description": "The customer ID"},
                    "fields": {"type": "object", "description": "Key-value dictionary of fields to update (name, phone)"}
                },
                "required": ["customer_id", "fields"]
            },
            "handler": lambda args, ctx: CustomerService.update_customer_profile(args.get("customer_id") or ctx.get("customer_id"), args.get("fields", {}))
        },
        "get_customer_addresses": {
            "name": "get_customer_addresses",
            "description": "Retrieves all saved shipping and billing addresses for a customer.",
            "category": "CUSTOMER",
            "risk_level": "MEDIUM",
            "endpoint": "/api/customers/{customer_id}/addresses",
            "method": "GET",
            "parameters": {
                "type": "object",
                "properties": {
                    "customer_id": {"type": "string", "description": "The customer ID"}
                },
                "required": ["customer_id"]
            },
            "handler": lambda args, ctx: CustomerService.get_customer_addresses(args.get("customer_id") or ctx.get("customer_id"))
        },
        "add_customer_address": {
            "name": "add_customer_address",
            "description": "Adds a new delivery address to the customer's account.",
            "category": "CUSTOMER",
            "risk_level": "MEDIUM",
            "endpoint": "/api/customers/{customer_id}/addresses",
            "method": "POST",
            "parameters": {
                "type": "object",
                "properties": {
                    "customer_id": {"type": "string", "description": "The customer ID"},
                    "address": {"type": "object", "description": "Address details (address_line, city, state, postal_code, address_type)"}
                },
                "required": ["customer_id", "address"]
            },
            "handler": lambda args, ctx: CustomerService.add_customer_address(args.get("customer_id") or ctx.get("customer_id"), args.get("address", {}))
        },

        # 3. Order Tools
        "get_order": {
            "name": "get_order",
            "description": "Retrieves comprehensive details of a specific order including items and pricing.",
            "category": "ORDER",
            "risk_level": "MEDIUM",
            "endpoint": "/api/orders/{order_id}",
            "method": "GET",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {"type": "string", "description": "The order ID (e.g. ORD1001)"}
                },
                "required": ["order_id"]
            },
            "handler": lambda args, ctx: OrderService.get_order_by_id(args.get("order_id"), ctx.get("customer_id"))
        },
        "get_order_history": {
            "name": "get_order_history",
            "description": "Retrieves the list of past orders placed by the customer.",
            "category": "ORDER",
            "risk_level": "MEDIUM",
            "endpoint": "/api/customers/{customer_id}/orders",
            "method": "GET",
            "parameters": {
                "type": "object",
                "properties": {
                    "customer_id": {"type": "string", "description": "The customer ID"}
                },
                "required": ["customer_id"]
            },
            "handler": lambda args, ctx: OrderService.get_orders_for_customer(args.get("customer_id") or ctx.get("customer_id"))
        },
        "get_order_status": {
            "name": "get_order_status",
            "description": "Checks the current order status, shipment status, and cancellation status.",
            "category": "ORDER",
            "risk_level": "LOW",
            "endpoint": "/api/orders/{order_id}/status",
            "method": "GET",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {"type": "string", "description": "The order ID (e.g. ORD1001)"}
                },
                "required": ["order_id"]
            },
            "handler": lambda args, ctx: OrderService.get_order_status(args.get("order_id"))
        },
        "cancel_order": {
            "name": "cancel_order",
            "description": "Requests cancellation of an order before it has been shipped.",
            "category": "ORDER",
            "risk_level": "HIGH",
            "endpoint": "/api/orders/{order_id}/cancel",
            "method": "POST",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {"type": "string", "description": "The order ID to cancel"}
                },
                "required": ["order_id"]
            },
            "handler": lambda args, ctx: OrderService.cancel_order(args.get("order_id"), ctx.get("customer_id"))
        },

        # 4. Delivery Tools
        "get_delivery_status": {
            "name": "get_delivery_status",
            "description": "Gets current courier delivery status for an order.",
            "category": "DELIVERY",
            "risk_level": "LOW",
            "endpoint": "/api/delivery/{order_id}/status",
            "method": "GET",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {"type": "string", "description": "The order ID"}
                },
                "required": ["order_id"]
            },
            "handler": lambda args, ctx: OrderService.get_delivery_status(args.get("order_id"))
        },
        "get_tracking_details": {
            "name": "get_tracking_details",
            "description": "Fetches live tracking checkpoints, courier name, and estimated delivery date.",
            "category": "DELIVERY",
            "risk_level": "LOW",
            "endpoint": "/api/delivery/{order_id}/tracking",
            "method": "GET",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {"type": "string", "description": "The order ID"}
                },
                "required": ["order_id"]
            },
            "handler": lambda args, ctx: OrderService.get_tracking_details(args.get("order_id"))
        },
        "update_delivery_address": {
            "name": "update_delivery_address",
            "description": "Changes destination delivery address for an unfulfilled order.",
            "category": "DELIVERY",
            "risk_level": "HIGH",
            "endpoint": "/api/orders/{order_id}/address",
            "method": "PUT",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {"type": "string", "description": "The order ID"},
                    "address_id": {"type": "string", "description": "The new address ID"}
                },
                "required": ["order_id", "address_id"]
            },
            "handler": lambda args, ctx: OrderService.update_delivery_address(args.get("order_id"), args.get("address_id"), ctx.get("customer_id"))
        },

        # 5. Payment Tools
        "get_payment_status": {
            "name": "get_payment_status",
            "description": "Checks payment method, transaction status, and payment confirmation for an order.",
            "category": "PAYMENT",
            "risk_level": "MEDIUM",
            "endpoint": "/api/orders/{order_id}/payment",
            "method": "GET",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {"type": "string", "description": "The order ID"}
                },
                "required": ["order_id"]
            },
            "handler": lambda args, ctx: OrderService.get_payment_status(args.get("order_id"))
        },
        "process_refund": {
            "name": "process_refund",
            "description": "Processes a refund for a cancelled or returned order.",
            "category": "PAYMENT",
            "risk_level": "HIGH",
            "endpoint": "/api/orders/{order_id}/refund",
            "method": "POST",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {"type": "string", "description": "The order ID"},
                    "amount": {"type": "number", "description": "Refund amount (optional, defaults to order total)"}
                },
                "required": ["order_id"]
            },
            "handler": lambda args, ctx: OrderService.process_refund(args.get("order_id"), args.get("amount"))
        },
        "cancel_payment": {
            "name": "cancel_payment",
            "description": "Cancels a pending payment transaction.",
            "category": "PAYMENT",
            "risk_level": "HIGH",
            "endpoint": "/api/orders/{order_id}/payment/cancel",
            "method": "POST",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {"type": "string", "description": "The order ID"}
                },
                "required": ["order_id"]
            },
            "handler": lambda args, ctx: OrderService.cancel_payment(args.get("order_id"))
        },

        # 6. Return Tools
        "request_return": {
            "name": "request_return",
            "description": "Initiates a return request for a delivered product with a specific reason.",
            "category": "RETURN",
            "risk_level": "MEDIUM",
            "endpoint": "/api/orders/{order_id}/returns",
            "method": "POST",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {"type": "string", "description": "The order ID to return"},
                    "reason": {"type": "string", "description": "Return reason: Damaged product, Wrong product, Product not as described, Size issue, Changed mind, Other"}
                },
                "required": ["order_id", "reason"]
            },
            "handler": lambda args, ctx: OrderService.request_return(args.get("order_id"), args.get("reason", "Other"), ctx.get("customer_id"))
        },
        "check_return_status": {
            "name": "check_return_status",
            "description": "Checks the status of an existing return request for an order.",
            "category": "RETURN",
            "risk_level": "LOW",
            "endpoint": "/api/orders/{order_id}/returns/status",
            "method": "GET",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {"type": "string", "description": "The order ID"}
                },
                "required": ["order_id"]
            },
            "handler": lambda args, ctx: OrderService.check_return_status(args.get("order_id"))
        },
        "approve_return": {
            "name": "approve_return",
            "description": "Approves a return request and schedules pickup (Admin/Support action).",
            "category": "RETURN",
            "risk_level": "HIGH",
            "endpoint": "/api/returns/{return_id}/approve",
            "method": "POST",
            "parameters": {
                "type": "object",
                "properties": {
                    "return_id": {"type": "string", "description": "The return ID (e.g. RET1001)"}
                },
                "required": ["return_id"]
            },
            "handler": lambda args, ctx: OrderService.approve_return(args.get("return_id"))
        },

        # 7. Sensitive Operations (HIGH & CRITICAL)
        "get_customer_pii": {
            "name": "get_customer_pii",
            "description": "Retrieves comprehensive Personally Identifiable Information for customer verification.",
            "category": "SENSITIVE",
            "risk_level": "HIGH",
            "endpoint": "/api/customers/{customer_id}/pii",
            "method": "GET",
            "parameters": {
                "type": "object",
                "properties": {
                    "customer_id": {"type": "string", "description": "The customer ID"}
                },
                "required": ["customer_id"]
            },
            "handler": lambda args, ctx: CustomerService.get_customer_pii(args.get("customer_id") or ctx.get("customer_id"))
        },
        "export_customer_data": {
            "name": "export_customer_data",
            "description": "Generates a full GDPR/data portability export bundle for a customer.",
            "category": "SENSITIVE",
            "risk_level": "CRITICAL",
            "endpoint": "/api/customers/{customer_id}/export",
            "method": "POST",
            "parameters": {
                "type": "object",
                "properties": {
                    "customer_id": {"type": "string", "description": "The customer ID"}
                },
                "required": ["customer_id"]
            },
            "handler": lambda args, ctx: CustomerService.export_customer_data(args.get("customer_id") or ctx.get("customer_id"))
        },
        "delete_customer_account": {
            "name": "delete_customer_account",
            "description": "Permanently deactivates and schedules customer account deletion.",
            "category": "SENSITIVE",
            "risk_level": "CRITICAL",
            "endpoint": "/api/customers/{customer_id}/delete",
            "method": "DELETE",
            "parameters": {
                "type": "object",
                "properties": {
                    "customer_id": {"type": "string", "description": "The customer ID to delete"}
                },
                "required": ["customer_id"]
            },
            "handler": lambda args, ctx: CustomerService.delete_customer_account(args.get("customer_id") or ctx.get("customer_id"))
        }
    }

    @classmethod
    def get_tool_metadata(cls, tool_name=None):
        """Returns metadata for a specific tool or all 23 registered tools."""
        if tool_name:
            tool = cls.TOOLS.get(tool_name)
            if not tool:
                return None
            return {
                "name": tool["name"],
                "description": tool["description"],
                "category": tool["category"],
                "risk_level": tool["risk_level"],
                "endpoint": tool["endpoint"],
                "method": tool["method"],
                "parameters": tool["parameters"]
            }
        return [
            {
                "name": t["name"],
                "description": t["description"],
                "category": t["category"],
                "risk_level": t["risk_level"],
                "endpoint": t["endpoint"],
                "method": t["method"],
                "parameters": t["parameters"]
            }
            for t in cls.TOOLS.values()
        ]

    @classmethod
    def execute_tool(cls, tool_name, arguments, context=None):
        """
        Executes a tool with strict external policy interception:
        ShopSphere proposes -> AegisAI decides -> ShopSphere executes only after receiving decision.
        """
        context = context or {}
        customer_id = context.get("customer_id", "CUS_GUEST")
        session_id = context.get("session_id", f"SESS_{uuid.uuid4().hex[:8]}")
        user_message = context.get("user_message", "")

        tool = cls.TOOLS.get(tool_name)
        if not tool:
            return {
                "success": False,
                "executed": False,
                "error": f"Tool '{tool_name}' is not registered in Tool Registry.",
                "policy_decision": "BLOCK"
            }

        # 1. ShopSphere proposes the structured tool action
        is_verified = context.get("is_verified")
        if is_verified is None:
            is_verified = bool(customer_id and customer_id != "CUS_GUEST")

        proposal_payload = {
            "agent_id": "customer-service-agent",
            "customer_id": customer_id,
            "session_id": session_id,
            "conversation_id": session_id,
            "tool_name": tool_name,
            "arguments": arguments,
            "risk_level": tool["risk_level"],
            "context": {
                "user_message": user_message,
                "risk_level": tool["risk_level"],
                "category": tool["category"],
                "is_verified": is_verified,
                "current_order_id": context.get("current_order_id"),
                "order_status": context.get("order_status")
            }
        }

        # 2. AegisAI evaluates permission
        policy_response = policy_service.evaluate_tool_request(proposal_payload)
        decision = policy_response.get("decision", "BLOCK").upper()
        risk_level = policy_response.get("risk_level", tool["risk_level"])
        reason = policy_response.get("reason", "No reason provided.")

        execution_status = "NOT_EXECUTED"
        result_data = None
        executed_arguments = arguments

        # 3. ShopSphere executes ONLY after receiving the decision
        # Task 4 Invariant: Execute using ONLY the arguments in AegisAI's returned decision object
        if decision == "ALLOW":
            approved_args = policy_response.get("arguments") if (policy_response.get("arguments") is not None) else arguments
            executed_arguments = approved_args
            try:
                result_data = tool["handler"](approved_args, context)
                execution_status = "SUCCESS"
            except Exception as e:
                execution_status = f"ERROR: {str(e)}"
                result_data = {"error": str(e)}

        elif decision == "MODIFY":
            # Use modified arguments provided strictly by AegisAI decision object
            modified_args = policy_response.get("modified_arguments") if (policy_response.get("modified_arguments") is not None) else policy_response.get("arguments", arguments)
            executed_arguments = modified_args
            try:
                result_data = tool["handler"](modified_args, context)
                execution_status = "SUCCESS_MODIFIED"
            except Exception as e:
                execution_status = f"ERROR: {str(e)}"
                result_data = {"error": str(e)}

        elif decision == "ESCALATE":
            execution_status = "ESCALATED_PENDING_APPROVAL"
            result_data = {
                "message": f"This operation requires human supervisor or manager approval. Reason: {reason}",
                "escalated": True
            }

        elif decision == "BLOCK":
            execution_status = "BLOCKED_BY_POLICY"
            result_data = {
                "message": f"Action blocked by AegisAI security policy. Reason: {reason}",
                "blocked": True
            }

        else:
            execution_status = f"UNKNOWN_DECISION_{decision}"
            result_data = {"message": f"Unknown policy decision: {decision}"}

        # 4. Record in Audit Log
        try:
            cls._log_audit(
                action=f"TOOL_CALL_{tool_name.upper()}",
                agent_id="customer-service-agent",
                customer_id=customer_id,
                tool_name=tool_name,
                arguments=executed_arguments,
                policy_decision=decision,
                policy_reason=reason,
                execution_status=execution_status
            )
        except Exception as log_err:
            print(f"[ToolRegistry Audit Warning] Failed to save audit log: {log_err}")

        # Return standardized envelope containing execution result and AegisAI inspection metadata
        return {
            "success": execution_status in ("SUCCESS", "SUCCESS_MODIFIED"),
            "executed": execution_status in ("SUCCESS", "SUCCESS_MODIFIED"),
            "execution_status": execution_status,
            "tool_name": tool_name,
            "tool_metadata": {
                "category": tool["category"],
                "risk_level": tool["risk_level"],
                "endpoint": tool["endpoint"],
                "method": tool["method"]
            },
            "arguments": executed_arguments,
            "policy_service": {
                "decision": decision,
                "risk_level": risk_level,
                "reason": reason,
                "policy_id": policy_response.get("policy_id")
            },
            "data": result_data
        }

    @staticmethod
    def _log_audit(action, agent_id, customer_id, tool_name, arguments, policy_decision, policy_reason, execution_status):
        session = SessionLocal()
        try:
            # Sanitize arguments so sensitive keys like passwords or card numbers are never stored
            sanitized_args = {}
            if isinstance(arguments, dict):
                for k, v in arguments.items():
                    if any(secret in k.lower() for secret in ["password", "token", "secret", "cvv", "card"]):
                        sanitized_args[k] = "******"
                    else:
                        sanitized_args[k] = v
            else:
                sanitized_args = {"raw": str(arguments)}

            log = AuditLog(
                log_id=f"LOG{uuid.uuid4().hex[:8].upper()}",
                action=action,
                agent_id=agent_id,
                customer_id=customer_id,
                tool_name=tool_name,
                arguments_json=json.dumps(sanitized_args),
                policy_decision=policy_decision,
                policy_reason=policy_reason,
                execution_status=execution_status,
                created_at=datetime.utcnow()
            )
            session.add(log)
            session.commit()
        finally:
            session.close()


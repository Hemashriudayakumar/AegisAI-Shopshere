import json
from backend.agent.llm_client import LLMClient
from backend.tools.registry import ToolRegistry

class CustomerServiceAgent:
    """
    AI Customer-Service Agent for ShopSphere.
    Coordinates between the user's intent, the Tool Registry, and response generation.
    Strictly follows the propose-decide-execute contract with AegisAI via ToolRegistry.
    """

    @classmethod
    def handle_message(cls, user_message, customer_id="CUS1001", session_id="SESSION_DEFAULT", current_order_id=None):
        context = {
            "customer_id": customer_id,
            "session_id": session_id,
            "current_order_id": current_order_id,
            "user_message": user_message
        }

        # 1. Determine tool proposal via LLM / Intent Engine
        tool_name, arguments_or_reply = LLMClient.process_query(user_message, context)

        if not tool_name:
            reply_text = arguments_or_reply if isinstance(arguments_or_reply, str) and arguments_or_reply else "I'm your ShopSphere assistant! How can I help you today? You can ask me to track orders, search for products, check stock, cancel orders, or request returns."
            return {
                "reply": reply_text,
                "developer_metadata": None
            }

        arguments = arguments_or_reply if isinstance(arguments_or_reply, dict) else {}

        # Safety Guard: Ensure order-dependent tools never execute or forward null/None order_id
        order_dependent_tools = [
            "get_order", "get_order_status", "get_tracking_details", "get_delivery_status",
            "cancel_order", "process_refund", "cancel_payment", "request_return",
            "check_return_status", "update_delivery_address", "get_payment_status"
        ]
        if tool_name in order_dependent_tools:
            oid = arguments.get("order_id")
            if not oid or str(oid).strip().lower() in ("none", "null", ""):
                return {
                    "reply": "To assist you with this request, please provide your order ID (e.g. ORD1001).",
                    "developer_metadata": None
                }

        # 2. Propose action through the Tool Registry (which triggers AegisAI interception)
        execution_result = ToolRegistry.execute_tool(tool_name, arguments, context)

        # 3. Generate natural, helpful response based on execution result & AegisAI decision
        reply = cls._synthesize_response(user_message, tool_name, execution_result)

        # 4. Assemble developer metadata for the Developer Mode inspector
        developer_metadata = {
            "tool_name": tool_name,
            "arguments": execution_result.get("arguments", arguments),
            "tool_metadata": execution_result.get("tool_metadata", {}),
            "policy_service": execution_result.get("policy_service", {}),
            "execution_status": execution_result.get("execution_status"),
            "executed": execution_result.get("executed", False)
        }

        return {
            "reply": reply,
            "developer_metadata": developer_metadata
        }

    @classmethod
    def _synthesize_response(cls, user_message, tool_name, execution_result):
        data = execution_result.get("data", {})
        policy = execution_result.get("policy_service", {})
        decision = policy.get("decision", "ALLOW")

        # 1. Handle AegisAI Interception Decisions (BLOCK, ESCALATE)
        if decision == "BLOCK":
            reason = policy.get("reason", "This action violates security policy.")
            return f"⚠️ **Security Policy Interception**: We could not complete your request.\n\n**Reason:** {reason}\n\nPlease contact our senior helpdesk if you believe this is an error."

        if decision == "ESCALATE":
            reason = policy.get("reason", "Manager approval required.")
            return f"🛡️ **Elevated Approval Required**: Your request involves a sensitive operation.\n\n**Notice:** {reason}\n\nOur customer support supervisor has been notified and will review this action shortly."

        # 2. Handle Tool Execution Errors
        if not execution_result.get("executed"):
            error_msg = data.get("message") or data.get("error") or "Unknown error occurred."
            return f"I encountered an issue processing your request: {error_msg}"

        # 3. Handle Successful Execution by Tool Type
        if tool_name == "search_products":
            products = data if isinstance(data, list) else data.get("products", [])
            if not products:
                return "I couldn't find any products matching your search. Try searching for 'laptop', 'smartphone', or 'headphones'."
            
            lines = [f"I found **{len(products)} products** for you:\n"]
            for p in products[:5]:
                lines.append(
                    f"- **[{p['product_name']}](/products/{p['product_id']})** - ₹{p['final_price']:,.2f} "
                    f"⭐ {p['rating']} ({p['review_count']} reviews) | *{p['brand']}*"
                )
            if len(products) > 5:
                lines.append(f"\n*...and {len(products) - 5} more products available in our catalogue.*")
            return "\n".join(lines)

        elif tool_name == "check_product_stock":
            if not data.get("found"):
                return data.get("message", "Product stock information unavailable.")
            status_text = "🟢 **In Stock**" if data.get("in_stock") else "🔴 **Out of Stock**"
            return (
                f"{status_text}: **{data.get('product_name')}** currently has **{data.get('stock_quantity')} units** "
                f"available in our fulfillment center."
            )

        elif tool_name == "get_order_status":
            if not data.get("found"):
                return data.get("message", "Order not found.")
            return (
                f"📦 **Order Status for {data.get('order_id')}**:\n\n"
                f"- **Current Status:** `{data.get('order_status')}`\n"
                f"- **Delivery Stage:** `{data.get('delivery_status')}`\n"
                f"- **Order Total:** ₹{data.get('total_amount'):,.2f}\n"
                f"- **Order Date:** {data.get('order_date')}\n"
                f"\n[View Order Details](/orders/{data.get('order_id')}) | [Track Delivery](/orders/{data.get('order_id')}/track)"
            )

        elif tool_name == "get_tracking_details":
            if not data.get("found"):
                return data.get("message", "Tracking details not found.")
            checkpoints = data.get("checkpoints", [])
            latest_stage = data.get("delivery_status", "In Transit")
            lines = [
                f"🚚 **Tracking Information for {data.get('order_id')}**:\n",
                f"- **Courier:** {data.get('carrier')} (Tracking #{data.get('tracking_number')})",
                f"- **Current Location:** {data.get('current_location')}",
                f"- **Estimated Delivery:** {data.get('estimated_delivery') or 'Updating...'}\n",
                "**Progress Timeline:**"
            ]
            for cp in checkpoints:
                icon = "✅" if cp.get("completed") else "⏳"
                lines.append(f"{icon} **{cp.get('stage')}** - {cp.get('date')}")
            return "\n".join(lines)

        elif tool_name == "get_order_history":
            orders = data if isinstance(data, list) else []
            if not orders:
                return "You haven't placed any orders yet. Start exploring our deals!"
            lines = ["📋 **Here are your recent orders**:\n"]
            for o in orders[:5]:
                lines.append(
                    f"- **Order #{o['order_id']}** ({o['order_date']}) - ₹{o['total_amount']:,.2f} "
                    f"| Status: `{o['order_status']}` | [Track](/orders/{o['order_id']}/track)"
                )
            return "\n".join(lines)

        elif tool_name == "cancel_order":
            if data.get("success"):
                return f"✅ **Order Cancelled**: {data.get('message')}"
            else:
                return f"❌ **Cancellation Denied**: {data.get('message')}"

        elif tool_name == "process_refund":
            if data.get("success"):
                return f"💰 **Refund Processed**: {data.get('message')} (Refund ID: `{data.get('refund_id')}`)."
            else:
                return f"⚠️ **Refund Error**: {data.get('message')}"

        elif tool_name == "request_return":
            if data.get("success"):
                return f"🔄 **Return Requested**: {data.get('message')} (Return ID: `{data.get('return_id')}`)."
            else:
                return f"⚠️ **Return Not Eligible**: {data.get('message')}"

        elif tool_name == "get_payment_status":
            pmt = data.get("payment", {})
            return (
                f"💳 **Payment Details for Order**:\n\n"
                f"- **Payment Method:** {pmt.get('payment_method')}\n"
                f"- **Amount Paid:** ₹{pmt.get('amount', 0):,.2f}\n"
                f"- **Payment Status:** `{pmt.get('payment_status')}`\n"
                f"- **Transaction ID:** `{pmt.get('transaction_id')}`"
            )

        elif tool_name == "get_customer_addresses":
            addresses = data if isinstance(data, list) else []
            if not addresses:
                return "You don't have any saved addresses yet. You can add one in your [Address Management](/addresses)."
            lines = ["📍 **Your Saved Delivery Addresses**:\n"]
            for a in addresses:
                def_tag = " (Default)" if a.get("is_default") else ""
                lines.append(f"- **{a.get('full_name')}** [{a.get('address_type')}]{def_tag}: {a.get('formatted')}")
            lines.append("\nTo change an order's delivery address, go to [My Orders](/orders).")
            return "\n".join(lines)

        elif tool_name == "get_customer_profile":
            return (
                f"👤 **Customer Profile**:\n\n"
                f"- **Name:** {data.get('name')}\n"
                f"- **Email:** {data.get('email')}\n"
                f"- **Phone:** {data.get('phone')}\n"
                f"- **Account Status:** `{data.get('account_status')}`\n"
                f"- **Total Orders:** {data.get('order_count')}"
            )

        elif tool_name == "get_customer_pii":
            return (
                f"🔐 **PII Record Extracted (HIGH RISK)**:\n\n"
                f"- **Name:** {data.get('name')}\n"
                f"- **Email:** {data.get('email')}\n"
                f"- **Phone:** {data.get('phone')}\n"
                f"- **Total Spend:** ₹{data.get('total_spend', 0):,.2f}"
            )

        return f"✅ **Request Processed**: {json.dumps(data)}"


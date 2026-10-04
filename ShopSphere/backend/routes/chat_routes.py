from flask import Blueprint, request, jsonify, session
from backend.agent.customer_agent import CustomerServiceAgent
from backend.tools.registry import ToolRegistry
from backend.database import SessionLocal
from backend.models import AuditLog

chat_bp = Blueprint("chat", __name__, url_prefix="/api/chat")

@chat_bp.route("", methods=["POST"])
def chat():
    data = request.get_json() or {}
    message = data.get("message", "").strip()
    current_order_id = data.get("current_order_id")
    session_id = data.get("session_id", session.get("session_id", "SESS_WEB_DEFAULT"))

    if not message:
        return jsonify({"success": False, "message": "Message content cannot be empty."}), 400

    customer_id = session.get("customer_id", "CUS1001")

    response_data = CustomerServiceAgent.handle_message(
        user_message=message,
        customer_id=customer_id,
        session_id=session_id,
        current_order_id=current_order_id
    )

    return jsonify({"success": True, **response_data})

@chat_bp.route("/tools", methods=["GET"])
def get_tools():
    """Returns metadata schema for all 23 registered tools in the Tool Registry."""
    tools = ToolRegistry.get_tool_metadata()
    return jsonify({"success": True, "count": len(tools), "tools": tools})

@chat_bp.route("/execute-tool", methods=["POST"])
def direct_execute_tool():
    """
    Developer Mode endpoint to directly propose and test tool execution through AegisAI.
    Useful for testing specific tools and verifying ALLOW, BLOCK, and ESCALATE policies.
    """
    data = request.get_json() or {}
    tool_name = data.get("tool_name")
    arguments = data.get("arguments", {})
    context = data.get("context", {})
    customer_id = session.get("customer_id", "CUS1001")
    context.setdefault("customer_id", customer_id)

    if not tool_name:
        return jsonify({"success": False, "message": "tool_name is required."}), 400

    result = ToolRegistry.execute_tool(tool_name, arguments, context)
    return jsonify(result)

@chat_bp.route("/audit-logs", methods=["GET"])
def get_audit_logs():
    """Fetches recent security and policy interception logs for developer mode."""
    limit = int(request.args.get("limit", 25))
    session_db = SessionLocal()
    try:
        logs = session_db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit).all()
        return jsonify({"success": True, "logs": [l.to_dict() for l in logs]})
    finally:
        session_db.close()


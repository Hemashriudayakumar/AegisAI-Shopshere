import os
import json
import requests

# External Policy / Security Service (AegisAI) Configuration
POLICY_SERVICE_URL = os.getenv("POLICY_SERVICE_URL", "http://localhost:8000")
MOCK_POLICY_SERVICE = os.getenv("MOCK_POLICY_SERVICE", "false").lower() in ("true", "1", "yes")

def evaluate_tool_request(request_payload):
    """
    Client interface for the external security & policy service (AegisAI).
    ShopSphere proposes an action -> AegisAI decides permission -> ShopSphere executes only after receiving decision.
    """
    tool_name = request_payload.get("tool_name")
    arguments = request_payload.get("arguments", {})
    customer_id = request_payload.get("customer_id")
    context = request_payload.get("context", {})
    risk_level = (context.get("risk_level") or request_payload.get("risk_level") or "MEDIUM").upper()

    # 1. If Mock Mode is active (for standalone/offline fallback)
    if MOCK_POLICY_SERVICE:
        if tool_name in ("delete_customer_account", "export_customer_data", "approve_return"):
            return {
                "decision": "ESCALATE",
                "risk_level": "CRITICAL" if "account" in tool_name or "data" in tool_name else "HIGH",
                "policy_id": "DATA_EXPORT_001" if "data" in tool_name else ("ACCOUNT_DELETION_001" if "account" in tool_name else "RETURN_APPROVAL_001"),
                "reason": f"Mock Mode: Action '{tool_name}' requires elevated approval."
            }
        elif tool_name in ("process_refund", "issue_refund"):
            amount = float(arguments.get("amount", 0) or 0)
            if amount > 500:
                return {
                    "decision": "BLOCK",
                    "risk_level": "HIGH",
                    "policy_id": "REFUND_LIMIT_001",
                    "reason": f"Mock Policy: Refund of ₹{amount:,.2f} exceeds standard maximum policy threshold of ₹500."
                }
            return {
                "decision": "ALLOW",
                "risk_level": "HIGH",
                "policy_id": "REFUND_LIMIT_001",
                "reason": "Mock Policy Service: Refund request validated and within authorized limit."
            }
        else:
            return {
                "decision": "ALLOW",
                "risk_level": risk_level,
                "policy_id": "STANDARD_ALLOW_001",
                "reason": f"Mock Policy Service: Operation '{tool_name}' permitted."
            }

    # 2. Live AegisAI External Service Mode
    endpoint = f"{POLICY_SERVICE_URL.rstrip('/')}/evaluate"

    normalized_payload = {
        "agent_id": request_payload.get("agent_id", "customer-service-agent"),
        "customer_id": customer_id or "CUS1001",
        "session_id": request_payload.get("session_id") or request_payload.get("conversation_id"),
        "conversation_id": request_payload.get("conversation_id") or request_payload.get("session_id"),
        "tool_name": tool_name,
        "arguments": arguments,
        "risk_level": risk_level,
        "context": context,
        "is_verified": context.get("is_verified") if isinstance(context, dict) else None,
        "manager_approved": context.get("manager_approved", False) if isinstance(context, dict) else False,
        "user_message": context.get("user_message", "") if isinstance(context, dict) else "",
    }

    try:
        response = requests.post(
            endpoint,
            json=normalized_payload,
            headers={"Content-Type": "application/json"},
            timeout=5.0
        )
        if response.status_code == 200:
            return response.json()
        else:
            # Handle non-200 responses with fail-closed / fail-open rules
            if risk_level == "LOW":
                return {
                    "decision": "ALLOW",
                    "risk_level": "LOW",
                    "policy_id": "FAIL_OPEN_LOW_RISK",
                    "reason": f"AegisAI returned HTTP {response.status_code}; LOW-risk tool permitted.",
                    "arguments": arguments
                }
            else:
                return {
                    "decision": "BLOCK",
                    "risk_level": risk_level,
                    "policy_id": "FAIL_CLOSED_HTTP_ERR",
                    "reason": f"AegisAI service returned status {response.status_code}: {response.text}",
                    "safe_response": "Our policy verification service is temporarily unavailable. For your security, this request cannot be completed right now."
                }
    except requests.exceptions.RequestException as e:
        # Task 3: Fail-Closed Behavior on Network/Timeout Failure
        # LOW-risk tools: fail open (proceed without a decision)
        if risk_level == "LOW":
            return {
                "decision": "ALLOW",
                "risk_level": "LOW",
                "policy_id": "FAIL_OPEN_LOW_RISK",
                "reason": f"AegisAI unreachable ({str(e)}); LOW-risk tool failed open.",
                "arguments": arguments
            }
        else:
            # MEDIUM, HIGH, and CRITICAL-risk tools: fail closed (BLOCK)
            return {
                "decision": "BLOCK",
                "risk_level": risk_level,
                "policy_id": "FAIL_CLOSED_SERVICE_UNAVAILABLE",
                "reason": f"External Policy Service (AegisAI) unreachable at {endpoint}: {str(e)}. Transaction blocked for security.",
                "safe_response": "Our policy verification service is temporarily unavailable. For your security, this request cannot be completed right now."
            }

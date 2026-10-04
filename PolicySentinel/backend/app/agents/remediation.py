import logging
from typing import Any, Dict, Optional, Tuple
from app.agents.llm_provider import check_ollama_alive
from app.config import settings

logger = logging.getLogger(__name__)

REMEDIATION_TEMPLATES: Dict[str, str] = {
    "REFUND_LIMIT_001": "I can help raise a refund request. Since the amount is above ₹{limit}, it requires approval from our support team.",
    "CUSTOMER_VERIFICATION_001": "To assist you with this request, I need to verify your identity first. Could you please provide your order ID?",
    "DELIVERY_VERIFICATION_001": "Let me check the verified delivery date for your order. I will get back to you shortly.",
    "PII_PROTECTION_001": "I cannot process or share sensitive personal information for security reasons. Please contact our support team for assistance.",
    "HIGH_RISK_ESCALATION_001": "I understand this is a serious concern. I have escalated your concern immediately to our specialized senior support team.",
    "DUPLICATE_REFUND_001": "A refund has already been issued for order {order_id}. Our policy permits only one refund per order.",
    "REPEATED_COMPLAINT_001": "I see you have experienced multiple unresolved issues with this order. I am escalating your case directly to a senior supervisor for immediate review.",
    "STANDARD_ALLOW_001": "How else may I assist you with your order today?"
}

def remediate_response_template(
    policy_id: str,
    original_response: str,
    context: Optional[Dict[str, Any]] = None,
    policy_decision: Optional[Dict[str, Any]] = None
) -> str:
    """Generates a safe, policy-compliant alternative response using deterministic templates."""
    template = REMEDIATION_TEMPLATES.get(policy_id)
    if not template:
        if policy_decision and policy_decision.get("safe_response"):
            return policy_decision["safe_response"]
        return "I need to escalate this request to our support team for further assistance."

    limit = 500
    if context and context.get("approval_limit"):
        limit = context["approval_limit"]
    elif policy_decision and policy_decision.get("evidence", {}).get("approval_limit"):
        limit = policy_decision["evidence"]["approval_limit"]

    order_id = "this order"
    if policy_decision and policy_decision.get("evidence", {}).get("order_id"):
        order_id = policy_decision["evidence"]["order_id"]
    elif context and context.get("order_id"):
        order_id = context["order_id"]

    try:
        return template.format(limit=int(limit), order_id=order_id)
    except Exception:
        return template

def remediate_response_llm(
    original_response: str,
    policy_violation: Dict[str, Any],
    context: Optional[Dict[str, Any]] = None,
    base_url: Optional[str] = None
) -> Optional[str]:
    """Uses Qwen model to rewrite the response when Ollama is available."""
    url = base_url or settings.OLLAMA_BASE_URL
    if not check_ollama_alive(url):
        return None

    try:
        import httpx
        policy_id = policy_violation.get("policy_id", "POLICY_VIOLATION")
        reason = policy_violation.get("reason", "Violation detected")
        
        prompt = f"""You are a customer-support response remediation agent.

Original response:
"{original_response}"

Policy violation:
Policy: {policy_id}
Reason: {reason}

Generate a safe, polite, policy-compliant alternative response that:
1. Does not make unauthorized promises or reveal sensitive data.
2. Explains the limitation politely.
3. Offers appropriate next steps.

Safe response:"""

        payload = {
            "model": settings.OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.0}
        }
        res = httpx.post(f"{url.rstrip('/')}/api/generate", json=payload, timeout=3.0)
        if res.status_code == 200:
            rewritten = res.json().get("response", "").strip()
            if rewritten:
                return rewritten
    except Exception as e:
        logger.info(f"LLM remediation skipped ({e}), falling back to template.")

    return None

def remediate_response(
    policy_decision: Dict[str, Any],
    original_response: str,
    context: Optional[Dict[str, Any]] = None,
    prefer_llm: bool = False
) -> Tuple[str, str]:
    """Remediates a response returning (corrected_response, remediation_type)."""
    policy_id = policy_decision.get("policy_id", "UNKNOWN_POLICY")

    if prefer_llm:
        llm_corrected = remediate_response_llm(original_response, policy_decision, context)
        if llm_corrected:
            return llm_corrected, "LLM"

    template_corrected = remediate_response_template(policy_id, original_response, context, policy_decision)
    return template_corrected, "TEMPLATE"

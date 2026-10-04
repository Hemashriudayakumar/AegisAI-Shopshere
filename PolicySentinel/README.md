# AegisAI: A Customer-Service AI Policy Enforcement Gateway

AegisAI is an enterprise-grade AI Policy Enforcement Gateway designed to monitor, intercept, and govern AI customer-support agents before:
1. Their generated responses are presented to customers.
2. Their proposed actions are delegated to operations agents.
3. Underlying business tools are executed.

---

## Architecture & Multi-Agent Workflow

```
Customer Message
       ↓
  [Input Guard]
       ↓
[Agent A: Customer-Support Agent (Qwen3-8B)]
       ↓ (Proposes response & optional business action)
[AegisAI Gateway (Deterministic Engine & Priority Pipeline)]
       ↓
   Decision:
   ├── ALLOW    → [Agent B: Operations Agent] → [Tool Interceptor] → [Mock Tool Execution]
   ├── MODIFY   → [Remediation Agent]
   ├── BLOCK    → [Safe Response Generation]
   └── ESCALATE → [Human Escalation Queue & Supervisor Notification]
       ↓
  [Audit Store (PostgreSQL / SQLite)]
       ↓
Final Safe Customer Response
```

### Critical Security Guarantees
- **Proposal-Only Principle**: Agent A can only propose actions in structured JSON. Agent A has zero direct execution permissions on tools.
- **Strict Authorization Envelope**: Operations Agent B only receives an exact, immutable authorization envelope containing the allowed tool, parameters, and decision ID.
- **Pre-Execution Tool Interception**: The `ToolInterceptor` verifies tool name and every argument against the cryptographic authorization envelope immediately prior to invocation. If arguments are tampered with or the envelope is missing, execution is immediately blocked.
- **Fail-Closed & Audit-First**: Every interaction and gateway evaluation is permanently recorded in the immutable audit log. High-risk violations immediately generate reviewable security incidents.

---

## Built-In Policies

| Policy ID | Severity | Rule Description | Default Safe Response / Outcome |
| :--- | :--- | :--- | :--- |
| `REFUND_LIMIT_001` | HIGH | Refunds exceeding ₹500 require explicit manager authorization. | *"This refund requires approval from our support team."* (Action blocked, incident created) |
| `CUSTOMER_VERIFICATION_001` | HIGH | Customer identity must be verified before accessing order details or financial operations. | *"Please verify your identity with your registered phone number or email before we can access order details or process transactions."* |
| `DELIVERY_VERIFICATION_001` | MEDIUM | The chatbot cannot promise specific delivery dates unless confirmed by a verified order lookup. | *"I can check your estimated delivery date once you provide your verified order ID."* (Remediated) |
| `PII_PROTECTION_001` | CRITICAL | Credit card numbers, CVVs, passwords, full phone numbers, and cross-customer data are blocked. | *"For your security, sensitive personal information cannot be shared in this channel."* |
| `HIGH_RISK_ESCALATION_001` | CRITICAL | Fraud complaints, legal threats, and consumer court mentions are immediately escalated. | *"I have escalated your concern immediately to our senior safety and legal compliance team. A supervisor will contact you directly."* |

---

## Standard Data Contract

```json
{
  "request_id": "REQ-A1B2C3",
  "conversation_id": "CONV-501",
  "policy_version": "v1.0",
  "decision": "BLOCK",
  "severity": "HIGH",
  "policy_id": "REFUND_LIMIT_001",
  "reason": "Refund amount of ₹3,000.00 exceeds automatic threshold of ₹500.00 and lacks manager authorization.",
  "evidence": {
    "refund_amount": 3000,
    "approval_limit": 500,
    "manager_approved": false,
    "order_id": "ORD-101"
  },
  "proposed_action": {
    "tool_name": "issue_refund",
    "arguments": {
      "order_id": "ORD-101",
      "amount": 3000
    }
  },
  "approved_action": null,
  "safe_response": "This refund requires approval from our support team.",
  "requires_human_review": true,
  "tool_executed": false,
  "final_response": "This refund requires approval from our support team.",
  "agent_a_response": "I can certainly help you process a refund of ₹3000 for order ORD-101.",
  "agent_b_called": false,
  "incident_id": "INC-99F12A"
}
```

---

## Tech Stack

- **Backend**: Python, FastAPI, Pydantic v2, SQLAlchemy 2.x, Alembic, PostgreSQL / SQLite
- **AI & Workflow**: Qwen3-8B (Ollama / `langchain-ollama`), LangGraph StateGraph
- **Frontend**: React, TypeScript, Vite, Tailwind CSS
- **Testing**: Pytest, HTTPX, TestClient
- **Containerization**: Docker, Docker Compose

---

## Quick Start & Setup

### 1. Run Automated Backend Tests
```bash
cd backend
python -m pytest -v
```

### 2. Run Backend Locally
```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

### 3. Run Frontend Locally
```bash
cd frontend
npm install
npm run dev
```
Open `http://localhost:5173` in your browser.

### 4. Run via Docker Compose
```bash
docker-compose up --build
```

---

## Core API Endpoints

- `POST /api/chat`: Run full LangGraph StateGraph pipeline on customer message.
- `GET /api/audits`: Fetch immutable audit trail with filtering and pagination.
- `GET /api/audits/{event_id}`: Retrieve full audit event details.
- `GET /api/incidents`: Retrieve security and policy incident queue.
- `GET /api/policies`: Retrieve registered policies and active versions.
- `POST /api/policies`: Draft a new policy definition.
- `PUT /api/policies/{policy_id}`: Create a new policy version.
- `POST /api/approvals/{decision_id}/approve`: Manager one-click approval.
- `POST /api/approvals/{decision_id}/reject`: Manager one-click rejection.
- `GET /api/health`: Service health and active policy count.

---

## Verification & Acceptance Demonstration

1. **₹3,000 Refund Request (Without Manager Approval)**:
   - Gateway Decision: `BLOCK` (`REFUND_LIMIT_001`)
   - Agent B: Not called
   - Refund Tool: Not executed
   - Incident & Audit: Created and visible in dashboard
2. **₹400 Refund Request (Verified Customer)**:
   - Gateway Decision: `ALLOW` (`REFUND_LIMIT_001`)
   - Agent B: Called with Authorization Envelope
   - Refund Tool: Executed successfully (`REF-XXXXX` issued)
3. **Unverified Sensitive Access**:
   - Gateway Decision: `BLOCK` (`CUSTOMER_VERIFICATION_001`)
   - Tool: Not executed
4. **Unverified Delivery Promise**:
   - Gateway Decision: `MODIFY` (`DELIVERY_VERIFICATION_001`)
   - Chatbot response rewritten with safe lookup prompt
5. **Fraud / Legal Threat**:
   - Gateway Decision: `ESCALATE` (`HIGH_RISK_ESCALATION_001`)
   - High-severity incident queued for human review
6. **Tool Interceptor Argument Tampering**:
   - Gateway Decision: `BLOCK`
   - Tool Interceptor intercepts and halts modified parameters

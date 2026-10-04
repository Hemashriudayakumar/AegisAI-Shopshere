# ShopSphere - Modern E-Commerce Platform & AI Customer-Support Chatbot

ShopSphere is a complete, modern mock e-commerce web application featuring a rich shopping experience, order lifecycle management, an admin operations hub, and an integrated AI customer-service chatbot.

---

## 🏛️ System Architecture

ShopSphere strictly separates customer support from backend data access. **The AI Chatbot NEVER accesses the MySQL database directly.**

```
+-------------------------------------------------------------------------------+
|                                Browser / Frontend                             |
|    HTML5 + Bootstrap 5 + Vanilla JavaScript + Modern Responsive Components    |
+-------------------------------------------------------------------------------+
         | (HTTP / REST APIs)                                 | (Chat UI / Fetch)
         v                                                    v
+-----------------------------+                    +----------------------------+
|     Flask REST API &        |                    |   AI Customer-Service      |
|    Blueprint Controllers    |                    |          Agent             |
|   (Auth, Products, Cart,    |                    |  (Ollama/Qwen3 Provider    |
|    Orders, Admin, Returns)  |                    |   + Intent Fallback)       |
+-----------------------------+                    +----------------------------+
         |                                                    |
         |                                                    v (Structured Tool Proposal)
         |                                         +----------------------------+
         |                                         |       Tool Registry        |
         |                                         |   (23 Registered Tools     |
         |                                         |    + Metadata & Schemas)   |
         |                                         +----------------------------+
         |                                                    |
         |                                                    v (POST /evaluate)
         |                                         +----------------------------+
         |                                         | External Security Service  |
         |                                         |         (AegisAI)          |
         |                                         | [ALLOW / BLOCK / ESCALATE] |
         |                                         +----------------------------+
         |                                                    | (Executes ONLY if ALLOW/MODIFY)
         v                                                    v
+-------------------------------------------------------------------------------+
|                         Internal Business Service Layer                       |
|          (ProductService, OrderService, ReturnService, CustomerService)       |
+-------------------------------------------------------------------------------+
                                         |
                                         v
+-------------------------------------------------------------------------------+
|                       SQLAlchemy ORM Models & Session                         |
+-------------------------------------------------------------------------------+
                                         |
                                         v
+-------------------------------------------------------------------------------+
|                       MySQL Database (shopsphere_db)                          |
+-------------------------------------------------------------------------------+
```

---

## 🛡️ External Security / Policy Service Integration (AegisAI)

An independent external security and policy service is developed separately by another team member (**AegisAI**).

> **Contract:**
> 1. **ShopSphere Proposes**: When the chatbot determines an action, the Tool Registry formats a structured action proposal and calls `POST {POLICY_SERVICE_URL}/evaluate`.
> 2. **AegisAI Decides**: AegisAI determines whether the action is permitted and responds with `ALLOW`, `BLOCK`, `ESCALATE`, or `MODIFY`.
> 3. **ShopSphere Executes Only After Receiving Decision**:
>    - `ALLOW`: Executes the tool.
>    - `MODIFY`: Executes with modified arguments returned by AegisAI.
>    - `BLOCK`: Halts execution and returns the policy rejection reason to the customer.
>    - `ESCALATE`: Halts execution and notifies the customer that manager approval is required.

### Configuration
In `.env`:
```env
# URL for the external AegisAI service
POLICY_SERVICE_URL=http://localhost:8001

# Set to 'true' during development when AegisAI is not running
# Set to 'false' to route live evaluations to POLICY_SERVICE_URL
MOCK_POLICY_SERVICE=true
```

---

## 🧰 Centralized Tool Registry (23 Tools)

All chatbot interactions are mapped through `backend/tools/registry.py`:

| Category | Tool Name | Risk Level | HTTP Method & Endpoint |
|---|---|---|---|
| **PRODUCT** | `search_products` | `LOW` | `GET /api/products/search` |
| **PRODUCT** | `get_product_details` | `LOW` | `GET /api/products/{id}` |
| **PRODUCT** | `check_product_stock` | `LOW` | `GET /api/products/{id}/stock` |
| **CUSTOMER** | `get_customer_profile` | `MEDIUM` | `GET /api/customers/{id}/profile` |
| **CUSTOMER** | `update_customer_profile` | `MEDIUM` | `PUT /api/customers/{id}/profile` |
| **CUSTOMER** | `get_customer_addresses` | `MEDIUM` | `GET /api/customers/{id}/addresses` |
| **CUSTOMER** | `add_customer_address` | `MEDIUM` | `POST /api/customers/{id}/addresses` |
| **ORDER** | `get_order` | `MEDIUM` | `GET /api/orders/{id}` |
| **ORDER** | `get_order_history` | `MEDIUM` | `GET /api/customers/{id}/orders` |
| **ORDER** | `get_order_status` | `LOW` | `GET /api/orders/{id}/status` |
| **ORDER** | `cancel_order` | `HIGH` | `POST /api/orders/{id}/cancel` |
| **DELIVERY** | `get_delivery_status` | `LOW` | `GET /api/delivery/{id}/status` |
| **DELIVERY** | `get_tracking_details` | `LOW` | `GET /api/delivery/{id}/tracking` |
| **DELIVERY** | `update_delivery_address` | `HIGH` | `PUT /api/orders/{id}/address` |
| **PAYMENT** | `get_payment_status` | `MEDIUM` | `GET /api/orders/{id}/payment` |
| **PAYMENT** | `process_refund` | `HIGH` | `POST /api/orders/{id}/refund` |
| **PAYMENT** | `cancel_payment` | `HIGH` | `POST /api/orders/{id}/payment/cancel` |
| **RETURN** | `request_return` | `MEDIUM` | `POST /api/orders/{id}/returns` |
| **RETURN** | `check_return_status` | `LOW` | `GET /api/orders/{id}/returns/status` |
| **RETURN** | `approve_return` | `HIGH` | `POST /api/returns/{id}/approve` |
| **SENSITIVE** | `get_customer_pii` | `HIGH` | `GET /api/customers/{id}/pii` |
| **SENSITIVE** | `export_customer_data` | `CRITICAL` | `POST /api/customers/{id}/export` |
| **SENSITIVE** | `delete_customer_account` | `CRITICAL` | `DELETE /api/customers/{id}/delete` |

---

## ⚡ Quickstart & Setup

### 1. Prerequisites
- Python 3.10+
- MySQL Server 8.0 running locally on port 3306

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Initialize & Seed MySQL Database
```bash
python -m backend.init_db
```
This automatically ensures the database `shopsphere_db` exists, generates all tables via SQLAlchemy, and seeds:
- 5+ Demo Customers
- 6 Categories
- 57 Realistic Products
- 22 Seeded Orders across all lifecycle states (PLACED, CONFIRMED, PACKED, SHIPPED, OUT_FOR_DELIVERY, DELIVERED, CANCELLED, RETURN_REQUESTED, REFUNDED)
- Payments, Deliveries, Returns, and Refunds

### 4. Run Automated Test Suite
```bash
python -m unittest tests/test_apis.py
```

### 5. Start the Web Server
```bash
python -m backend.app
```
Open your browser at **`http://127.0.0.1:5000`**.

---

## 👥 Demo Accounts

For effortless evaluation, all demo accounts share the password: `password123`.

| Customer ID | Name | Email | Persona / Seeded Data |
|---|---|---|---|
| `CUS1001` | Rahul Sharma (Default) | `rahul@example.com` | Has 10 seeded orders across PLACED, SHIPPED, DELIVERED, high-value |
| `CUS1002` | Priya Patel | `priya@example.com` | Has placed, shipped, delivered, and returned orders |
| `CUS1003` | Amit Verma | `amit@example.com` | Has books and electronics orders |
| `CUS1004` | Sneha Reddy | `sneha@example.com` | Has beauty and fitness orders |
| `CUS1005` | Vikram Singh | `vikram@example.com` | Has camping outdoor gear orders |

*Tip: Use the **Account Menu** in the top navigation bar to switch between demo accounts in 1 click without retyping passwords.*

---

## 🤖 AI Chatbot Features & Developer Mode

Click the floating chat bubble on any page to open the AI Assistant.

### Supported Queries
- *"Show me laptops under ₹50,000."*
- *"Where is my order?"*
- *"What is the status of ORD1001?"*
- *"Can I return this product?"*
- *"I want a refund."*
- *"Cancel my order."*
- *"Change my delivery address."*
- *"Show my recent orders."*
- *"How much did I pay for my order?"*
- *"Is this product in stock?"*

### Developer Mode Toggle
Turn on the **Dev Mode** switch in the chat header to view the live inspection panel below each AI response:
- Tool Invoked
- Parameters / Arguments JSON
- Risk Level (`LOW` / `MEDIUM` / `HIGH` / `CRITICAL`)
- AegisAI Evaluation Decision (`ALLOW` / `BLOCK` / `ESCALATE` / `MODIFY`)
- Reason & Policy ID
- Execution Status & Audit Log confirmation


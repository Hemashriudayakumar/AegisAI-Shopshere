-- ShopSphere Database Schema
-- Compatible with MySQL 8.0

CREATE DATABASE IF NOT EXISTS shopsphere_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE shopsphere_db;

-- 1. Customers
CREATE TABLE IF NOT EXISTS customers (
    customer_id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    phone VARCHAR(20) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    account_status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- 2. Addresses
CREATE TABLE IF NOT EXISTS addresses (
    address_id VARCHAR(50) PRIMARY KEY,
    customer_id VARCHAR(50) NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    phone VARCHAR(20) NOT NULL,
    address_line VARCHAR(255) NOT NULL,
    city VARCHAR(100) NOT NULL,
    state VARCHAR(100) NOT NULL,
    postal_code VARCHAR(20) NOT NULL,
    address_type VARCHAR(20) NOT NULL DEFAULT 'Home',
    is_default BOOLEAN NOT NULL DEFAULT FALSE,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_addresses_customer FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- 3. Categories
CREATE TABLE IF NOT EXISTS categories (
    category_id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    slug VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    icon VARCHAR(100) DEFAULT 'bi-tag',
    image VARCHAR(255)
) ENGINE=InnoDB;

-- 4. Products
CREATE TABLE IF NOT EXISTS products (
    product_id VARCHAR(50) PRIMARY KEY,
    product_name VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    category VARCHAR(100) NOT NULL,
    subcategory VARCHAR(100) NOT NULL,
    brand VARCHAR(100) NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    discount DECIMAL(5, 2) NOT NULL DEFAULT 0.00,
    final_price DECIMAL(10, 2) NOT NULL,
    stock_quantity INT NOT NULL DEFAULT 0,
    rating DECIMAL(3, 2) NOT NULL DEFAULT 0.00,
    review_count INT NOT NULL DEFAULT 0,
    seller VARCHAR(100) NOT NULL DEFAULT 'ShopSphere Official',
    image VARCHAR(500) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- 5. Shopping Cart
CREATE TABLE IF NOT EXISTS cart (
    cart_id VARCHAR(50) PRIMARY KEY,
    customer_id VARCHAR(50) UNIQUE NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_cart_customer FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- 6. Cart Items
CREATE TABLE IF NOT EXISTS cart_items (
    item_id VARCHAR(50) PRIMARY KEY,
    cart_id VARCHAR(50) NOT NULL,
    product_id VARCHAR(50) NOT NULL,
    quantity INT NOT NULL DEFAULT 1,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_cart_items_cart FOREIGN KEY (cart_id) REFERENCES cart(cart_id) ON DELETE CASCADE,
    CONSTRAINT fk_cart_items_product FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- 7. Orders
CREATE TABLE IF NOT EXISTS orders (
    order_id VARCHAR(50) PRIMARY KEY,
    customer_id VARCHAR(50) NOT NULL,
    order_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    subtotal DECIMAL(10, 2) NOT NULL,
    discount DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    total_amount DECIMAL(10, 2) NOT NULL,
    payment_id VARCHAR(50),
    delivery_id VARCHAR(50),
    order_status VARCHAR(30) NOT NULL DEFAULT 'PLACED',
    cancellation_status VARCHAR(30) NOT NULL DEFAULT 'NONE',
    refund_status VARCHAR(30) NOT NULL DEFAULT 'NONE',
    shipping_address_id VARCHAR(50),
    shipping_address_text TEXT,
    CONSTRAINT fk_orders_customer FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
) ENGINE=InnoDB;

-- 8. Order Items
CREATE TABLE IF NOT EXISTS order_items (
    item_id VARCHAR(50) PRIMARY KEY,
    order_id VARCHAR(50) NOT NULL,
    product_id VARCHAR(50) NOT NULL,
    product_name VARCHAR(255) NOT NULL,
    quantity INT NOT NULL DEFAULT 1,
    unit_price DECIMAL(10, 2) NOT NULL,
    total_price DECIMAL(10, 2) NOT NULL,
    image VARCHAR(500),
    CONSTRAINT fk_order_items_order FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- 9. Payments
CREATE TABLE IF NOT EXISTS payments (
    payment_id VARCHAR(50) PRIMARY KEY,
    order_id VARCHAR(50) NOT NULL,
    payment_method VARCHAR(50) NOT NULL,
    amount DECIMAL(10, 2) NOT NULL,
    payment_status VARCHAR(30) NOT NULL DEFAULT 'COMPLETED',
    transaction_id VARCHAR(100) NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_payments_order FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- 10. Deliveries
CREATE TABLE IF NOT EXISTS deliveries (
    delivery_id VARCHAR(50) PRIMARY KEY,
    order_id VARCHAR(50) NOT NULL,
    tracking_number VARCHAR(100) NOT NULL UNIQUE,
    carrier VARCHAR(100) NOT NULL DEFAULT 'SphereLogistics',
    delivery_status VARCHAR(30) NOT NULL DEFAULT 'PENDING',
    estimated_delivery DATETIME,
    current_location VARCHAR(150),
    shipped_at DATETIME,
    delivered_at DATETIME,
    CONSTRAINT fk_deliveries_order FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- 11. Returns
CREATE TABLE IF NOT EXISTS returns (
    return_id VARCHAR(50) PRIMARY KEY,
    order_id VARCHAR(50) NOT NULL,
    customer_id VARCHAR(50) NOT NULL,
    reason VARCHAR(255) NOT NULL,
    return_status VARCHAR(30) NOT NULL DEFAULT 'REQUESTED',
    requested_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_returns_order FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE CASCADE,
    CONSTRAINT fk_returns_customer FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
) ENGINE=InnoDB;

-- 12. Refunds
CREATE TABLE IF NOT EXISTS refunds (
    refund_id VARCHAR(50) PRIMARY KEY,
    order_id VARCHAR(50) NOT NULL,
    payment_id VARCHAR(50),
    amount DECIMAL(10, 2) NOT NULL,
    refund_status VARCHAR(30) NOT NULL DEFAULT 'REQUESTED',
    processed_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_refunds_order FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- 13. Reviews
CREATE TABLE IF NOT EXISTS reviews (
    review_id VARCHAR(50) PRIMARY KEY,
    product_id VARCHAR(50) NOT NULL,
    customer_id VARCHAR(50),
    customer_name VARCHAR(100) NOT NULL,
    rating INT NOT NULL DEFAULT 5,
    comment TEXT,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_reviews_product FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- 14. Audit Logs (Interceptions, Actions, Policy Decisions)
CREATE TABLE IF NOT EXISTS audit_logs (
    log_id VARCHAR(50) PRIMARY KEY,
    action VARCHAR(100) NOT NULL,
    agent_id VARCHAR(100),
    customer_id VARCHAR(50),
    tool_name VARCHAR(100),
    arguments_json TEXT,
    policy_decision VARCHAR(50),
    policy_reason TEXT,
    execution_status VARCHAR(50),
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;


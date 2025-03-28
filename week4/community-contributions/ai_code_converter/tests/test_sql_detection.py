"""Test module for SQL language detection."""

import sys
import os

# Add the src directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from ai_code_converter.core.language_detection import LanguageDetector


def test_sql_detection():
    """Test the SQL language detection functionality."""
    detector = LanguageDetector()
    
    # Sample SQL code
    sql_code = """
-- Create database
CREATE DATABASE ecommerce;

-- Use the database
USE ecommerce;

-- Create tables
CREATE TABLE customers (
    customer_id INT PRIMARY KEY AUTO_INCREMENT,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

CREATE TABLE categories (
    category_id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    parent_id INT,
    FOREIGN KEY (parent_id) REFERENCES categories(category_id)
);

CREATE TABLE products (
    product_id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    price DECIMAL(10, 2) NOT NULL,
    stock_quantity INT DEFAULT 0,
    category_id INT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (category_id) REFERENCES categories(category_id)
);

CREATE TABLE orders (
    order_id INT PRIMARY KEY AUTO_INCREMENT,
    customer_id INT NOT NULL,
    order_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    status ENUM('pending', 'processing', 'shipped', 'delivered', 'cancelled') DEFAULT 'pending',
    total_amount DECIMAL(10, 2) NOT NULL,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

CREATE TABLE order_items (
    order_item_id INT PRIMARY KEY AUTO_INCREMENT,
    order_id INT NOT NULL,
    product_id INT NOT NULL,
    quantity INT NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(order_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);

-- Insert sample data
INSERT INTO categories (name, description)
VALUES ('Electronics', 'Electronic devices and gadgets'),
       ('Clothing', 'Apparel and accessories'),
       ('Books', 'Books and publications');

INSERT INTO products (name, description, price, stock_quantity, category_id)
VALUES ('Smartphone', 'Latest smartphone with advanced features', 699.99, 100, 1),
       ('Laptop', 'High-performance laptop for professionals', 1299.99, 50, 1),
       ('T-shirt', 'Cotton t-shirt in various colors', 19.99, 200, 2),
       ('Jeans', 'Classic denim jeans', 49.99, 150, 2),
       ('Programming Book', 'Learn programming from experts', 39.99, 75, 3);

-- Simple queries
SELECT * FROM products WHERE price > 50.00;

SELECT p.name, p.price, c.name AS category
FROM products p
JOIN categories c ON p.category_id = c.category_id
WHERE p.stock_quantity > 0
ORDER BY p.price DESC;

-- Aggregate functions
SELECT 
    c.name AS category,
    COUNT(p.product_id) AS product_count,
    AVG(p.price) AS average_price,
    MIN(p.price) AS min_price,
    MAX(p.price) AS max_price
FROM products p
JOIN categories c ON p.category_id = c.category_id
GROUP BY c.name
HAVING COUNT(p.product_id) > 1;

-- Transactions
BEGIN TRANSACTION;

UPDATE products
SET stock_quantity = stock_quantity - 1
WHERE product_id = 1;

INSERT INTO orders (customer_id, total_amount)
VALUES (1, 699.99);

INSERT INTO order_items (order_id, product_id, quantity, price)
VALUES (LAST_INSERT_ID(), 1, 1, 699.99);

COMMIT;

-- Views
CREATE VIEW product_details AS
SELECT 
    p.product_id,
    p.name,
    p.description,
    p.price,
    p.stock_quantity,
    c.name AS category
FROM products p
JOIN categories c ON p.category_id = c.category_id;

-- Stored procedure
DELIMITER //
CREATE PROCEDURE get_product_inventory()
BEGIN
    SELECT 
        p.name,
        p.stock_quantity,
        CASE
            WHEN p.stock_quantity = 0 THEN 'Out of Stock'
            WHEN p.stock_quantity < 10 THEN 'Low Stock'
            WHEN p.stock_quantity < 50 THEN 'Medium Stock'
            ELSE 'Well Stocked'
        END AS stock_status
    FROM products p
    ORDER BY p.stock_quantity;
END //
DELIMITER ;

-- Triggers
DELIMITER //
CREATE TRIGGER after_order_insert
AFTER INSERT ON orders
FOR EACH ROW
BEGIN
    INSERT INTO order_history (order_id, customer_id, status, action)
    VALUES (NEW.order_id, NEW.customer_id, NEW.status, 'created');
END //
DELIMITER ;

-- Indexes
CREATE INDEX idx_product_price ON products(price);
CREATE INDEX idx_order_customer ON orders(customer_id);

-- Subqueries
SELECT c.name, c.email
FROM customers c
WHERE c.customer_id IN (
    SELECT DISTINCT o.customer_id
    FROM orders o
    JOIN order_items oi ON o.order_id = oi.order_id
    JOIN products p ON oi.product_id = p.product_id
    WHERE p.category_id = 1
);

-- Common Table Expressions (CTE)
WITH high_value_orders AS (
    SELECT 
        o.order_id,
        o.customer_id,
        o.total_amount
    FROM orders o
    WHERE o.total_amount > 500
)
SELECT 
    c.first_name,
    c.last_name,
    COUNT(hvo.order_id) AS high_value_order_count
FROM customers c
JOIN high_value_orders hvo ON c.customer_id = hvo.customer_id
GROUP BY c.customer_id;
"""
    
    # Test the detection
    assert detector.detect_sql(sql_code) == True
    assert detector.detect_language(sql_code) == "SQL"
    
    # Check validation
    valid, _ = detector.validate_language(sql_code, "SQL")
    assert valid == True


if __name__ == "__main__":
    test_sql_detection()
    print("All SQL detection tests passed!")

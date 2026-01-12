-- SQL Test File 1: Database Schema
-- Expected: Extract table definitions and queries

CREATE TABLE customers (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE orders (
    id INT PRIMARY KEY AUTO_INCREMENT,
    customer_id INT REFERENCES customers(id),
    total DECIMAL(10, 2),
    status VARCHAR(20) DEFAULT 'pending',
    order_date DATE
);

-- Abfrage: Umsatz pro Kunde
SELECT 
    c.name AS kunde,
    COUNT(o.id) AS bestellungen,
    SUM(o.total) AS gesamtumsatz
FROM customers c
LEFT JOIN orders o ON c.id = o.customer_id
GROUP BY c.id, c.name
HAVING SUM(o.total) > 1000
ORDER BY gesamtumsatz DESC;

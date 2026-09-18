CREATE TABLE IF NOT EXISTS customers (
    customer_id VARCHAR(50) PRIMARY KEY,
    customer_name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE
);

CREATE TABLE IF NOT EXISTS products (
    product_id VARCHAR(50) PRIMARY KEY,
    product_name VARCHAR(150) NOT NULL,
    category VARCHAR(50),
    price NUMERIC(10, 2) CHECK (price >= 0)
);

CREATE TABLE IF NOT EXISTS orders (
    order_id VARCHAR(50) PRIMARY KEY,
    customer_id VARCHAR(50) REFERENCES customers(customer_id),
    product_id VARCHAR(50) REFERENCES products(product_id),
    quantity INT CHECK (quantity > 0),
    total_amount NUMERIC(10, 2),
    order_date TIMESTAMP NOT NULL,
    shipping_status VARCHAR(20) DEFAULT 'Pending'
);

CREATE INDEX IF NOT EXISTS idx_orders_order_date ON orders(order_date);

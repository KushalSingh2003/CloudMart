CREATE TABLE IF NOT EXISTS Category (
    category_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
INSERT INTO Category (name, description) VALUES
('Electronics', 'Electronic devices and accessories'),
('Computers', 'Laptops, desktops and computer accessories'),
('Mobile Phones', 'Smartphones and mobile phone accessories'),
('Home Appliances', 'Appliances and devices for home use'),
('Gaming', 'Gaming consoles, accessories and peripherals'),
('Networking', 'Routers, switches and networking equipment'),
('Audio', 'Headphones, speakers and audio equipment'),
('Cameras', 'Cameras and photography accessories');

CREATE TABLE IF NOT EXISTS Customers (
    user_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    phone VARCHAR(20),
    Role ENUM('customer', 'Admin') NOT NULL DEFAULT 'customer',
    token VARCHAR(512),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    
);
INSERT INTO Customers (name, email, phone, Role, token) VALUES
('Rahul Sharma', 'rahul@example.com', '9876543210', 'CUSTOMER', 'customer-token-001'),
('Priya Singh', 'priya@example.com', '9876543211', 'CUSTOMER', 'customer-token-002'),
('Amit Kumar', 'amit@example.com', '9876543212', 'CUSTOMER', 'customer-token-003'),
('Neha Verma', 'neha@example.com', '9876543213', 'CUSTOMER', 'customer-token-004'),
('Admin User', 'admin@example.com', '9876543214', 'ADMIN', 'admin-token-001');
CREATE TABLE IF NOT EXISTS Products (
    product_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    price DECIMAL(10,2) NOT NULL,
    stock INT NOT NULL DEFAULT 0,
    status VARCHAR(50) NOT NULL,
    category_id BIGINT NOT NULL,
    min_stock_quantity INT NOT NULL DEFAULT 1,
    max_stock_quantity INT NOT NULL DEFAULT 100,
    max_order_quantity INT NOT NULL DEFAULT 10,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_product_category
        FOREIGN KEY (category_id)
        REFERENCES Category(category_id)
);
INSERT INTO Products
(name, description, price, stock, status, category_id,
 min_stock_quantity, max_stock_quantity, max_order_quantity)
VALUES
('Wireless Mouse',
 'Ergonomic wireless mouse with USB receiver',
 799.00, 25, 'ACTIVE', 1, 5, 100, 5),

('Mechanical Keyboard',
 'RGB mechanical keyboard for gaming and productivity',
 2499.00, 15, 'ACTIVE', 2, 5, 100, 5),

('iPhone 15',
 'Apple iPhone 15 smartphone',
 69999.00, 10, 'ACTIVE', 3, 2, 50, 2),

('Samsung 55 Inch Smart TV',
 '4K Ultra HD Smart LED television',
 54999.00, 8, 'ACTIVE', 4, 2, 30, 2),

('Gaming Headset',
 'Wireless gaming headset with microphone',
 2999.00, 20, 'ACTIVE', 5, 5, 50, 3),

('WiFi Router',
 'Dual-band wireless router',
 1899.00, 30, 'ACTIVE', 6, 5, 100, 5),

('Bluetooth Speaker',
 'Portable Bluetooth speaker with deep bass',
 1599.00, 18, 'ACTIVE', 7, 5, 50, 3),

('Canon Digital Camera',
 'Digital camera for photography',
 45999.00, 5, 'ACTIVE', 8, 2, 20, 1);

CREATE TABLE IF NOT EXISTS Orders (
    order_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    total_amount DECIMAL(10,2) NOT NULL,
    status VARCHAR(50) NOT NULL,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    changed_at TIMESTAMP NULL,
    cancelled_at TIMESTAMP NULL,
    cancel_reason VARCHAR(500),

    CONSTRAINT fk_order_customer
        FOREIGN KEY (user_id)
        REFERENCES Customers(user_id)
);

CREATE TABLE IF NOT EXISTS Orders_Items (
    order_item_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    order_id BIGINT NOT NULL,
    product_id BIGINT NOT NULL,
    product_name VARCHAR(255) NOT NULL,
    quantity INT NOT NULL,
    price DECIMAL(10,2) NOT NULL,

    CONSTRAINT fk_order_item_order
        FOREIGN KEY (order_id)
        REFERENCES Orders(order_id),

    CONSTRAINT fk_order_item_product
        FOREIGN KEY (product_id)
        REFERENCES Products(product_id)
);

CREATE TABLE IF NOT EXISTS Orders_History (
    order_history_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    order_id BIGINT NOT NULL,
    user_id BIGINT,
    total_amount DECIMAL(10,2),
    status VARCHAR(50),
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    archived_at TIMESTAMP NULL,
    cancelled_at TIMESTAMP NULL,
    cancelled_reason VARCHAR(500),

    CONSTRAINT fk_history_order
        FOREIGN KEY (order_id)
        REFERENCES Orders(order_id),

    CONSTRAINT fk_history_customer
        FOREIGN KEY (user_id)
        REFERENCES Customers(user_id)
);
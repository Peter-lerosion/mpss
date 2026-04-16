-- ============================================
-- Authentication System Update
-- ============================================

USE mpss;

CREATE TABLE IF NOT EXISTS users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    hashed_password VARCHAR(255) NOT NULL,
    role ENUM('owner', 'vendor') NOT NULL DEFAULT 'vendor',
    vendor_id VARCHAR(10),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (vendor_id) REFERENCES vendors(vendor_id) ON DELETE SET NULL
);

-- Optional: Create a default owner user (password: owner123 - hashed later)
-- INSERT INTO users (username, hashed_password, role) VALUES ('admin', '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGGa31yy', 'owner');

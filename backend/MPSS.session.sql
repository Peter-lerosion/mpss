-- ============================================
-- Motor Part Shop Software (MPSS) - Schema
-- ============================================

CREATE DATABASE IF NOT EXISTS mpss;
USE mpss;

-- Vendors Table
CREATE TABLE IF NOT EXISTS vendors (
    vendor_id VARCHAR(10) PRIMARY KEY,
    vendor_name VARCHAR(100) NOT NULL,
    contact_person VARCHAR(100),
    phone VARCHAR(20),
    email VARCHAR(100),
    address TEXT,
    city VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Parts Table
CREATE TABLE IF NOT EXISTS parts (
    part_id VARCHAR(20) PRIMARY KEY,
    part_name VARCHAR(150) NOT NULL,
    vehicle_type VARCHAR(50) NOT NULL,
    manufacturer VARCHAR(100) NOT NULL,
    vendor_id VARCHAR(10),
    price DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    current_stock INT NOT NULL DEFAULT 0,
    rack_number VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (vendor_id) REFERENCES vendors(vendor_id) ON DELETE SET NULL
);

-- Sales Table
CREATE TABLE IF NOT EXISTS sales (
    sale_id INT AUTO_INCREMENT PRIMARY KEY,
    part_id VARCHAR(20) NOT NULL,
    quantity INT NOT NULL,
    unit_price DECIMAL(10, 2) NOT NULL,
    total_price DECIMAL(10, 2) NOT NULL,
    sale_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (part_id) REFERENCES parts(part_id) ON DELETE RESTRICT
);

-- Orders Table
CREATE TABLE IF NOT EXISTS orders (
    order_id INT AUTO_INCREMENT PRIMARY KEY,
    part_id VARCHAR(20) NOT NULL,
    vendor_id VARCHAR(10),
    quantity_ordered INT NOT NULL,
    unit_cost DECIMAL(10, 2),
    total_cost DECIMAL(10, 2),
    order_date DATE NOT NULL,
    status ENUM('pending', 'sent', 'received', 'cancelled') DEFAULT 'pending',
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (part_id) REFERENCES parts(part_id) ON DELETE RESTRICT,
    FOREIGN KEY (vendor_id) REFERENCES vendors(vendor_id) ON DELETE SET NULL
);

-- ============================================
-- Sample Data
-- ============================================

INSERT INTO vendors VALUES
('V001','AutoParts Kenya Ltd','John Kamau','+254 722 111 222','info@autopartske.co.ke','Industrial Area, Nairobi','Nairobi',NOW()),
('V002','Nakumatt Motors','Grace Wanjiru','+254 733 444 555','grace@nakumattmotors.co.ke','Mombasa Road, Athi River','Athi River',NOW()),
('V003','Toyota Kenya Spares','David Mwangi','+254 711 888 999','spares@toyotakenya.co.ke','Lusaka Road, Industrial','Nairobi',NOW()),
('V004','Nissan Parts Hub','Sarah Ochieng','+254 700 222 333','orders@nissanpartshub.co.ke','Ngong Road, Karen','Nairobi',NOW()),
('V005','Universal Spares','Peter Njoroge','+254 755 666 777','peter@universalspares.co.ke','Thika Road, Ruaraka','Nairobi',NOW());

INSERT INTO parts VALUES
('P001','Engine Oil Filter','Toyota','Denso','V003',850.00,45,'A1',NOW(),NOW()),
('P002','Brake Pads - Front','Toyota','Akebono','V001',3200.00,12,'B2',NOW(),NOW()),
('P003','Alternator Belt','Nissan','Gates','V004',1200.00,8,'A3',NOW(),NOW()),
('P004','Air Filter','Toyota','Toyota OEM','V003',650.00,30,'A2',NOW(),NOW()),
('P005','Spark Plugs (Set of 4)','Toyota','NGK','V001',1800.00,22,'C1',NOW(),NOW()),
('P006','Shock Absorber - Front','Nissan','KYB','V004',8500.00,6,'D3',NOW(),NOW()),
('P007','Fuel Pump','Toyota','Denso','V003',12000.00,4,'E1',NOW(),NOW()),
('P008','Timing Belt Kit','Toyota','Toyota OEM','V003',6500.00,9,'E2',NOW(),NOW()),
('P009','Clutch Plate','Nissan','Exedy','V002',7200.00,5,'F1',NOW(),NOW()),
('P010','Radiator Hose','Toyota','Gates','V001',950.00,18,'B4',NOW(),NOW()),
('P011','Water Pump','Toyota','GMB','V005',4200.00,7,'E3',NOW(),NOW()),
('P012','Wheel Bearing','Nissan','NSK','V004',3800.00,10,'D2',NOW(),NOW()),
('P013','Battery (12V 60Ah)','Universal','Chloride Exide','V002',12500.00,15,'G1',NOW(),NOW()),
('P014','Wiper Blades (Pair)','Universal','Bosch','V001',800.00,25,'H1',NOW(),NOW()),
('P015','Power Steering Pump','Toyota','Toyota OEM','V003',18000.00,3,'F2',NOW(),NOW());

-- Sample sales over last 30 days
INSERT INTO sales (part_id, quantity, unit_price, total_price, sale_date) VALUES
('P001',5,850.00,4250.00,CURDATE()-INTERVAL 1 DAY),
('P004',3,650.00,1950.00,CURDATE()-INTERVAL 1 DAY),
('P005',2,1800.00,3600.00,CURDATE()-INTERVAL 1 DAY),
('P002',1,3200.00,3200.00,CURDATE()-INTERVAL 2 DAY),
('P001',4,850.00,3400.00,CURDATE()-INTERVAL 2 DAY),
('P014',3,800.00,2400.00,CURDATE()-INTERVAL 2 DAY),
('P010',2,950.00,1900.00,CURDATE()-INTERVAL 3 DAY),
('P001',6,850.00,5100.00,CURDATE()-INTERVAL 3 DAY),
('P005',3,1800.00,5400.00,CURDATE()-INTERVAL 3 DAY),
('P004',4,650.00,2600.00,CURDATE()-INTERVAL 4 DAY),
('P013',1,12500.00,12500.00,CURDATE()-INTERVAL 4 DAY),
('P003',2,1200.00,2400.00,CURDATE()-INTERVAL 5 DAY),
('P001',3,850.00,2550.00,CURDATE()-INTERVAL 5 DAY),
('P008',1,6500.00,6500.00,CURDATE()-INTERVAL 5 DAY),
('P006',1,8500.00,8500.00,CURDATE()-INTERVAL 6 DAY),
('P002',2,3200.00,6400.00,CURDATE()-INTERVAL 6 DAY),
('P001',5,850.00,4250.00,CURDATE()-INTERVAL 7 DAY),
('P004',2,650.00,1300.00,CURDATE()-INTERVAL 7 DAY),
('P005',1,1800.00,1800.00,CURDATE()-INTERVAL 8 DAY),
('P011',1,4200.00,4200.00,CURDATE()-INTERVAL 8 DAY),
('P001',4,850.00,3400.00,CURDATE()-INTERVAL 9 DAY),
('P014',2,800.00,1600.00,CURDATE()-INTERVAL 9 DAY),
('P003',1,1200.00,1200.00,CURDATE()-INTERVAL 10 DAY),
('P001',3,850.00,2550.00,CURDATE()-INTERVAL 11 DAY),
('P004',5,650.00,3250.00,CURDATE()-INTERVAL 12 DAY),
('P007',1,12000.00,12000.00,CURDATE()-INTERVAL 13 DAY),
('P001',6,850.00,5100.00,CURDATE()-INTERVAL 14 DAY),
('P005',4,1800.00,7200.00,CURDATE()-INTERVAL 14 DAY),
('P002',1,3200.00,3200.00,CURDATE()-INTERVAL 15 DAY),
('P001',4,850.00,3400.00,CURDATE()-INTERVAL 16 DAY);

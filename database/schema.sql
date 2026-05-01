-- =====================================================
-- Poultry Management System - Database Schema
-- Compatible with MySQL / PostgreSQL / SQLite
-- (Tables are auto-created by SQLAlchemy; this file
--  is provided for reference and manual setup)
-- =====================================================

-- USERS
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(80) UNIQUE NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    role VARCHAR(20) DEFAULT 'worker',
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- BIRD BATCHES
CREATE TABLE IF NOT EXISTS bird_batches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(120) NOT NULL,
    breed VARCHAR(80),
    initial_count INTEGER NOT NULL,
    current_count INTEGER NOT NULL,
    arrival_date TIMESTAMP,
    stage VARCHAR(40),
    notes TEXT,
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- MORTALITY
CREATE TABLE IF NOT EXISTS mortality_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    batch_id INTEGER NOT NULL,
    count INTEGER NOT NULL,
    cause VARCHAR(120),
    notes TEXT,
    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (batch_id) REFERENCES bird_batches(id)
);

-- EGG COLLECTION
CREATE TABLE IF NOT EXISTS egg_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    batch_id INTEGER,
    total_eggs INTEGER NOT NULL,
    broken_eggs INTEGER DEFAULT 0,
    good_eggs INTEGER NOT NULL,
    notes TEXT,
    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (batch_id) REFERENCES bird_batches(id)
);

-- EGG STORAGE
CREATE TABLE IF NOT EXISTS egg_storage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    total_collected INTEGER DEFAULT 0,
    total_sold INTEGER DEFAULT 0,
    in_storage INTEGER DEFAULT 0,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- EGG SALES
CREATE TABLE IF NOT EXISTS egg_sales (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    quantity INTEGER NOT NULL,
    unit_price DECIMAL(10,2) NOT NULL,
    total_amount DECIMAL(10,2) NOT NULL,
    customer VARCHAR(120),
    notes TEXT,
    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- FEED PURCHASES
CREATE TABLE IF NOT EXISTS feed_purchases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    feed_type VARCHAR(80) NOT NULL,
    quantity_kg DECIMAL(10,2) NOT NULL,
    unit_price DECIMAL(10,2) NOT NULL,
    total_cost DECIMAL(10,2) NOT NULL,
    supplier VARCHAR(120),
    notes TEXT,
    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- FEED CONSUMPTION
CREATE TABLE IF NOT EXISTS feed_consumption (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    feed_type VARCHAR(80) NOT NULL,
    quantity_kg DECIMAL(10,2) NOT NULL,
    batch_id INTEGER,
    notes TEXT,
    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (batch_id) REFERENCES bird_batches(id)
);

-- FEED INVENTORY
CREATE TABLE IF NOT EXISTS feed_inventory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    feed_type VARCHAR(80) UNIQUE NOT NULL,
    current_stock DECIMAL(10,2) DEFAULT 0,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- HEALTH RECORDS (DISEASES)
CREATE TABLE IF NOT EXISTS health_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    batch_id INTEGER NOT NULL,
    disease VARCHAR(120) NOT NULL,
    symptoms TEXT,
    affected_count INTEGER DEFAULT 0,
    treatment TEXT,
    notes TEXT,
    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (batch_id) REFERENCES bird_batches(id)
);

-- VACCINATIONS
CREATE TABLE IF NOT EXISTS vaccinations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    batch_id INTEGER NOT NULL,
    vaccine_name VARCHAR(120) NOT NULL,
    dose VARCHAR(80),
    bird_count INTEGER DEFAULT 0,
    next_due_date TIMESTAMP,
    notes TEXT,
    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (batch_id) REFERENCES bird_batches(id)
);

-- FILE RECORDS
CREATE TABLE IF NOT EXISTS file_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename VARCHAR(255) NOT NULL,
    original_name VARCHAR(255) NOT NULL,
    filepath VARCHAR(500) NOT NULL,
    mime_type VARCHAR(120),
    size INTEGER,
    category VARCHAR(60) DEFAULT 'general',
    description TEXT,
    uploaded_by INTEGER,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (uploaded_by) REFERENCES users(id)
);

-- ALERTS
CREATE TABLE IF NOT EXISTS alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    alert_type VARCHAR(60) NOT NULL,
    title VARCHAR(200) NOT NULL,
    message TEXT NOT NULL,
    severity VARCHAR(20) DEFAULT 'info',
    is_resolved BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP
);

-- CAMERA DETECTIONS
CREATE TABLE IF NOT EXISTS camera_detections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source VARCHAR(40) DEFAULT 'image',
    live_birds INTEGER DEFAULT 0,
    dead_birds INTEGER DEFAULT 0,
    eggs INTEGER DEFAULT 0,
    image_path VARCHAR(500),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_egg_records_date ON egg_records(date);
CREATE INDEX IF NOT EXISTS idx_mortality_date ON mortality_records(date);
CREATE INDEX IF NOT EXISTS idx_egg_sales_date ON egg_sales(date);
CREATE INDEX IF NOT EXISTS idx_feed_purchases_date ON feed_purchases(date);
CREATE INDEX IF NOT EXISTS idx_feed_consumption_date ON feed_consumption(date);
CREATE INDEX IF NOT EXISTS idx_alerts_resolved ON alerts(is_resolved);

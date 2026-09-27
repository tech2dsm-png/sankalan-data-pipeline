-- ============================================================
-- SCHEMA
-- ============================================================

CREATE SCHEMA IF NOT EXISTS analytics;
SET search_path TO analytics;

-- ============================================================
-- DIMENSION TABLES
-- ============================================================

-- 1. Device Dimension (Browser, OS, Device Type)
CREATE TABLE IF NOT EXISTS dim_device (
    device_id SERIAL PRIMARY KEY,
    device_type VARCHAR(50) NOT NULL,  -- 'mobile', 'desktop', 'tablet'
    browser VARCHAR(50),               -- 'chrome', 'firefox', 'safari', 'edge'
    browser_version VARCHAR(50),       -- '122.0.0.0'
    os VARCHAR(50),                    -- 'windows', 'macos', 'android', 'ios'
    os_version VARCHAR(50),            -- '11', '14.5'
    is_mobile BOOLEAN DEFAULT FALSE,
    screen_resolution VARCHAR(20),     -- '1920x1080'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Page Dimension
CREATE TABLE IF NOT EXISTS dim_page (
    page_id SERIAL PRIMARY KEY,
    page_url VARCHAR(500) UNIQUE NOT NULL,
    page_category VARCHAR(100),
    page_title VARCHAR(200),
    page_type VARCHAR(50),             -- 'blog', 'product', 'landing'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. User Dimension (with Location)
CREATE TABLE IF NOT EXISTS dim_user (
    user_id SERIAL PRIMARY KEY,
    user_external_id VARCHAR(100) UNIQUE,
    user_type VARCHAR(20) DEFAULT 'new',  -- 'new', 'returning', 'loyal'
    
    -- Location Information
    country VARCHAR(100),
    city VARCHAR(100),
    region VARCHAR(100),
    latitude DECIMAL(10,8),
    longitude DECIMAL(11,8),
    timezone VARCHAR(50),
    postal_code VARCHAR(20),
    
    -- User Preferences
    preferred_language VARCHAR(10),
    device_preference VARCHAR(20),     -- 'mobile', 'desktop'
    
    first_session_id VARCHAR(100),
    first_visit_at TIMESTAMP,
    last_visit_at TIMESTAMP,
    total_visits INT DEFAULT 0,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. Session Dimension
CREATE TABLE IF NOT EXISTS dim_session (
    session_id VARCHAR(100) PRIMARY KEY,
    user_id INTEGER REFERENCES dim_user(user_id),
    session_start TIMESTAMP,
    session_end TIMESTAMP,
    session_duration_seconds INT,
    traffic_source VARCHAR(50),        -- 'google', 'direct', 'social', 'email'
    traffic_medium VARCHAR(50),        -- 'organic', 'cpc', 'referral'
    traffic_campaign VARCHAR(100),
    referrer_url VARCHAR(500),
    landing_page VARCHAR(500),
    entry_timestamp TIMESTAMP,
    exit_timestamp TIMESTAMP,
    is_new_user BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- FACT TABLE (Events)
-- ============================================================

CREATE TABLE IF NOT EXISTS fact_page_views (
    event_id BIGSERIAL PRIMARY KEY,
    
    -- Foreign Keys to Dimensions
    session_id VARCHAR(100) REFERENCES dim_session(session_id),
    user_id INTEGER REFERENCES dim_user(user_id),
    page_id INTEGER REFERENCES dim_page(page_id),
    device_id INTEGER REFERENCES dim_device(device_id),
    
    -- Event Data
    event_timestamp TIMESTAMP,
    event_type VARCHAR(20),            -- 'page_view', 'click', 'scroll', 'conversion'
    
    -- Performance Metrics
    load_time_ms INTEGER,
    time_on_page_seconds INTEGER,
    scroll_depth_pct INTEGER,
    
    -- Traffic Information
    traffic_source VARCHAR(50),
    traffic_medium VARCHAR(50),
    referrer_url VARCHAR(500),
    
    -- Raw Data (for reference and enrichment)
    ip_address VARCHAR(45),
    user_agent TEXT,
    full_url VARCHAR(500),
    
    -- Conversion Data
    is_bounce BOOLEAN DEFAULT FALSE,
    is_conversion BOOLEAN DEFAULT FALSE,
    conversion_value DECIMAL(10,2),
    conversion_type VARCHAR(50),       -- 'purchase', 'signup', 'download'
    
    -- Session Information
    is_new_session BOOLEAN DEFAULT FALSE,
    page_sequence INT,                 -- Order in session
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- INDEXES (For Performance)
-- ============================================================

-- Fact Table Indexes
CREATE INDEX idx_fact_timestamp ON fact_page_views(event_timestamp);
CREATE INDEX idx_fact_session ON fact_page_views(session_id);
CREATE INDEX idx_fact_user ON fact_page_views(user_id);
CREATE INDEX idx_fact_page ON fact_page_views(page_id);
CREATE INDEX idx_fact_device ON fact_page_views(device_id);
CREATE INDEX idx_fact_event_type ON fact_page_views(event_type);
CREATE INDEX idx_fact_bounce ON fact_page_views(is_bounce);
CREATE INDEX idx_fact_conversion ON fact_page_views(is_conversion);

-- Dimension Table Indexes
CREATE INDEX idx_device_type ON dim_device(device_type);
CREATE INDEX idx_device_browser ON dim_device(browser);
CREATE INDEX idx_user_external ON dim_user(user_external_id);
CREATE INDEX idx_user_location ON dim_user(country, city);
CREATE INDEX idx_page_url ON dim_page(page_url);
CREATE INDEX idx_session_user ON dim_session(user_id);
CREATE INDEX idx_session_source ON dim_session(traffic_source);

-- ============================================================
-- MATERIALIZED VIEWS (For Dashboard Performance)
-- ============================================================

-- 1. Bounce Rate by Minute
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_bounce_rate AS
SELECT 
    DATE_TRUNC('minute', event_timestamp) AS minute,
    COUNT(DISTINCT session_id) AS total_sessions,
    COUNT(DISTINCT CASE WHEN is_bounce THEN session_id END) AS bounced_sessions,
    ROUND(
        (COUNT(DISTINCT CASE WHEN is_bounce THEN session_id END) * 100.0) / 
        NULLIF(COUNT(DISTINCT session_id), 0), 2
    ) AS bounce_rate
FROM fact_page_views
WHERE event_timestamp > NOW() - INTERVAL '1 hour'
GROUP BY DATE_TRUNC('minute', event_timestamp);

-- 2. Top Pages
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_top_pages AS
SELECT 
    p.page_url,
    p.page_category,
    COUNT(*) AS views,
    COUNT(DISTINCT f.session_id) AS unique_sessions,
    AVG(f.time_on_page_seconds) AS avg_time_on_page,
    COUNT(DISTINCT f.user_id) AS unique_users
FROM fact_page_views f
JOIN dim_page p ON f.page_id = p.page_id
WHERE f.event_timestamp > NOW() - INTERVAL '1 hour'
GROUP BY p.page_url, p.page_category
ORDER BY views DESC
LIMIT 20;

-- 3. Device Breakdown
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_device_breakdown AS
SELECT 
    d.device_type,
    d.browser,
    d.os,
    COUNT(*) AS events,
    COUNT(DISTINCT f.session_id) AS unique_sessions,
    COUNT(DISTINCT f.user_id) AS unique_users
FROM fact_page_views f
JOIN dim_device d ON f.device_id = d.device_id
WHERE f.event_timestamp > NOW() - INTERVAL '1 hour'
GROUP BY d.device_type, d.browser, d.os;

-- 4. Location Breakdown
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_location_breakdown AS
SELECT 
    u.country,
    u.city,
    u.region,
    COUNT(*) AS events,
    COUNT(DISTINCT f.session_id) AS unique_sessions,
    COUNT(DISTINCT f.user_id) AS unique_users
FROM fact_page_views f
JOIN dim_user u ON f.user_id = u.user_id
WHERE f.event_timestamp > NOW() - INTERVAL '1 hour'
  AND u.country IS NOT NULL
GROUP BY u.country, u.city, u.region
ORDER BY events DESC
LIMIT 20;

-- 5. Traffic Source Performance
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_traffic_sources AS
SELECT 
    f.traffic_source,
    f.traffic_medium,
    COUNT(*) AS events,
    COUNT(DISTINCT f.session_id) AS unique_sessions,
    COUNT(DISTINCT f.user_id) AS unique_users,
    SUM(CASE WHEN f.is_conversion THEN 1 ELSE 0 END) AS conversions,
    SUM(f.conversion_value) AS total_revenue
FROM fact_page_views f
WHERE f.event_timestamp > NOW() - INTERVAL '1 hour'
GROUP BY f.traffic_source, f.traffic_medium
ORDER BY events DESC;

-- ============================================================
-- FUNCTION: Refresh All Materialized Views
-- ============================================================

CREATE OR REPLACE FUNCTION refresh_materialized_views()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_bounce_rate;
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_top_pages;
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_device_breakdown;
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_location_breakdown;
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_traffic_sources;
END;
$$ LANGUAGE plpgsql;

-- ============================================================
-- SAMPLE DATA FOR TESTING
-- ============================================================

-- Sample Devices
INSERT INTO dim_device (device_type, browser, browser_version, os, os_version, is_mobile, screen_resolution) VALUES
    ('desktop', 'chrome', '122.0.0.0', 'windows', '11', false, '1920x1080'),
    ('desktop', 'firefox', '123.0.0.0', 'macos', '14.5', false, '2560x1440'),
    ('mobile', 'chrome', '122.0.0.0', 'android', '14', true, '1080x2400'),
    ('tablet', 'safari', '17.0.0.0', 'ios', '17.4', true, '1640x2360'),
    ('desktop', 'edge', '122.0.0.0', 'windows', '10', false, '1366x768'),
    ('mobile', 'firefox', '123.0.0.0', 'android', '13', true, '1080x2400');

-- Sample Pages
INSERT INTO dim_page (page_url, page_category, page_title, page_type) VALUES
    ('/', 'home', 'Sankalan Tech - Home', 'landing'),
    ('/Tutorials/C/', 'tutorials', 'C Language Tutorial', 'blog'),
    ('/Tutorials/C/even-number-c-language', 'tutorials', 'Even Numbers in C', 'blog'),
    ('/about', 'about', 'About Sankalan Tech', 'static'),
    ('/contact', 'contact', 'Contact Us', 'static'),
    ('/products', 'products', 'Products', 'product'),
    ('/blog', 'blog', 'Blog', 'blog');

-- Sample Users with Location
INSERT INTO dim_user (user_external_id, user_type, country, city, region, timezone, first_visit_at) VALUES
    ('user_test_001', 'new', 'India', 'Pune', 'Maharashtra', 'Asia/Kolkata', NOW() - INTERVAL '1 day'),
    ('user_test_002', 'returning', 'India', 'Mumbai', 'Maharashtra', 'Asia/Kolkata', NOW() - INTERVAL '2 hours'),
    ('user_test_003', 'new', 'United States', 'New York', 'NY', 'America/New_York', NOW() - INTERVAL '30 minutes'),
    ('user_test_004', 'returning', 'United Kingdom', 'London', 'England', 'Europe/London', NOW() - INTERVAL '15 minutes'),
    ('user_test_005', 'loyal', 'India', 'Bangalore', 'Karnataka', 'Asia/Kolkata', NOW() - INTERVAL '7 days');

-- Sample Sessions
INSERT INTO dim_session (session_id, user_id, session_start, traffic_source, traffic_medium, referrer_url, landing_page, is_new_user) VALUES
    ('sess_test_001', 1, NOW() - INTERVAL '1 hour', 'google', 'organic', 'https://google.com/search?q=c+programming', '/Tutorials/C/', true),
    ('sess_test_002', 2, NOW() - INTERVAL '30 minutes', 'direct', 'none', NULL, '/', false),
    ('sess_test_003', 3, NOW() - INTERVAL '10 minutes', 'social', 'referral', 'https://twitter.com', '/blog', true),
    ('sess_test_004', 4, NOW() - INTERVAL '5 minutes', 'email', 'referral', 'https://mail.google.com', '/products', false),
    ('sess_test_005', 5, NOW() - INTERVAL '2 hours', 'google', 'organic', 'https://google.com/search?q=programming', '/', false);

-- Sample Fact Events (for testing)
INSERT INTO fact_page_views (
    session_id, user_id, page_id, device_id, 
    event_timestamp, event_type, load_time_ms, time_on_page_seconds, scroll_depth_pct,
    traffic_source, referrer_url, ip_address, user_agent, is_bounce
)
SELECT 
    'sess_test_001'::VARCHAR,
    1,
    2,
    1,
    NOW() - INTERVAL '55 minutes' + (INTERVAL '1 minute' * generate_series(0, 9)),
    CASE (random() * 3)::INT 
        WHEN 0 THEN 'page_view' 
        WHEN 1 THEN 'click' 
        ELSE 'scroll' 
    END,
    (200 + random() * 2800)::INT,
    (5 + random() * 115)::INT,
    (20 + random() * 80)::INT,
    'google',
    'https://google.com/search?q=c+programming',
    '203.0.113.45',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    random() < 0.3
FROM generate_series(1, 10);

-- ============================================================
-- VERIFICATION QUERIES
-- ============================================================

-- Check all tables
DO $$
DECLARE
    table_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO table_count 
    FROM information_schema.tables 
    WHERE table_schema = 'analytics' 
    AND table_type = 'BASE TABLE';
    
    RAISE NOTICE ' Created % tables', table_count;
END $$;

-- Check materialized views
DO $$
DECLARE
    mv_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO mv_count 
    FROM pg_matviews 
    WHERE schemaname = 'analytics';
    
    RAISE NOTICE '✅ Created % materialized views', mv_count;
END $$;
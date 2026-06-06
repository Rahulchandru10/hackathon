-- Initial Database Schema for Project Sentinel (PostgreSQL)

-- Users & Roles
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL CHECK (role IN ('Analyst', 'Senior Analyst', 'Compliance Manager', 'MLRO', 'Admin')),
    email VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Cases Table
CREATE TABLE IF NOT EXISTS cases (
    id VARCHAR(100) PRIMARY KEY, -- standard UUID or custom Case ID
    entity_name VARCHAR(255) NOT NULL,
    entity_type VARCHAR(50) CHECK (entity_type IN ('Company', 'Individual', 'Unknown')),
    country VARCHAR(100),
    industry VARCHAR(100),
    website VARCHAR(255),
    registration_number VARCHAR(100),
    aliases TEXT[], -- Array of strings
    parent_company VARCHAR(255),
    subsidiaries TEXT[],
    directors TEXT[],
    shareholders TEXT[],
    beneficial_owners TEXT[],
    status VARCHAR(50) NOT NULL CHECK (status IN ('OPEN', 'UNDER_REVIEW', 'APPROVED', 'REJECTED', 'CLOSED')),
    risk_score INT DEFAULT 0 CHECK (risk_score >= 0 AND risk_score <= 100),
    risk_breakdown JSONB DEFAULT '{}'::jsonb,
    recommendation VARCHAR(100) CHECK (recommendation IN ('CLEAR', 'MONITOR', 'ENHANCED_DUE_DILIGENCE', 'ESCALATE', 'REJECT', 'REQUIRES_HUMAN_REVIEW')),
    recommendation_justification TEXT,
    regulator_qa_status VARCHAR(50) DEFAULT 'PENDING' CHECK (regulator_qa_status IN ('PENDING', 'PASS', 'FAIL')),
    regulator_qa_deficiencies TEXT[],
    assigned_to INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Adverse Media Articles
CREATE TABLE IF NOT EXISTS articles (
    id VARCHAR(100) PRIMARY KEY,
    case_id VARCHAR(100) REFERENCES cases(id) ON DELETE CASCADE,
    title VARCHAR(500) NOT NULL,
    url TEXT UNIQUE NOT NULL,
    source VARCHAR(255) NOT NULL,
    source_tier INT CHECK (source_tier BETWEEN 1 AND 4),
    credibility_score INT CHECK (credibility_score BETWEEN 0 AND 100),
    publish_date TIMESTAMP WITH TIME ZONE,
    summary TEXT,
    content TEXT,
    language VARCHAR(10) DEFAULT 'en',
    cluster_id VARCHAR(100), -- for duplicate detection clustering
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Extracted Crime Events
CREATE TABLE IF NOT EXISTS events (
    id VARCHAR(100) PRIMARY KEY,
    case_id VARCHAR(100) REFERENCES cases(id) ON DELETE CASCADE,
    article_id VARCHAR(100) REFERENCES articles(id) ON DELETE SET NULL,
    event_type VARCHAR(100) NOT NULL,
    severity INT CHECK (severity BETWEEN 0 AND 100),
    description TEXT,
    detected_date VARCHAR(50),
    location VARCHAR(255),
    entities_involved TEXT[],
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Monitoring Subscriptions
CREATE TABLE IF NOT EXISTS monitoring_subscriptions (
    id SERIAL PRIMARY KEY,
    entity_name VARCHAR(255) NOT NULL,
    entity_type VARCHAR(50),
    country VARCHAR(100),
    industry VARCHAR(100),
    website VARCHAR(255),
    registration_number VARCHAR(100),
    frequency VARCHAR(50) NOT NULL CHECK (frequency IN ('One-time', 'Daily', 'Weekly')),
    created_by INTEGER REFERENCES users(id) ON DELETE CASCADE,
    last_checked TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Alerts Table
CREATE TABLE IF NOT EXISTS alerts (
    id VARCHAR(100) PRIMARY KEY,
    subscription_id INTEGER REFERENCES monitoring_subscriptions(id) ON DELETE CASCADE,
    case_id VARCHAR(100) REFERENCES cases(id) ON DELETE SET NULL,
    alert_type VARCHAR(100) NOT NULL, -- 'New Article', 'Risk Score Change', 'Sanction Match'
    description TEXT NOT NULL,
    severity VARCHAR(50) CHECK (severity IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')),
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Audit Logs Table
CREATE TABLE IF NOT EXISTS audit_logs (
    id SERIAL PRIMARY KEY,
    case_id VARCHAR(100) REFERENCES cases(id) ON DELETE SET NULL,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL,
    details TEXT,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_cases_entity_name ON cases(entity_name);
CREATE INDEX IF NOT EXISTS idx_articles_case_id ON articles(case_id);
CREATE INDEX IF NOT EXISTS idx_events_case_id ON events(case_id);
CREATE INDEX IF NOT EXISTS idx_alerts_subscription_id ON alerts(subscription_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_case_id ON audit_logs(case_id);

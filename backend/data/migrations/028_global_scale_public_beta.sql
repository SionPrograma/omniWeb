-- PHASES 46 - 55: GLOBAL SCALE & PUBLIC BETA BLOCK

-- Phase 46: Global Edge Node Layer
CREATE TABLE IF NOT EXISTS edge_node_metadata (
    node_id TEXT PRIMARY KEY REFERENCES cluster_nodes(node_id),
    region_code TEXT NOT NULL,
    latency_score FLOAT DEFAULT 1.0,
    cache_items_count INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE
);

-- Phase 47: Global Observability System
CREATE TABLE IF NOT EXISTS system_telemetry (
    telemetry_id TEXT PRIMARY KEY,
    node_id TEXT NOT NULL,
    service_name TEXT NOT NULL,
    metric_name TEXT NOT NULL,
    metric_value FLOAT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Phase 48 & 49: QR Entry & Universal Onboarding
CREATE TABLE IF NOT EXISTS registration_tokens (
    token_id TEXT PRIMARY KEY,
    token_string TEXT UNIQUE NOT NULL,
    issuer_id TEXT NOT NULL,
    usages_remaining INTEGER DEFAULT 1,
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS onboarding_analytics (
    user_id TEXT PRIMARY KEY,
    step_reached INTEGER DEFAULT 0,
    selected_language TEXT,
    accessibility_flag BOOLEAN DEFAULT FALSE,
    interest_tags TEXT DEFAULT '[]',
    completed_at DATETIME
);

-- Phase 50: Beta Testing Mode
CREATE TABLE IF NOT EXISTS beta_feedback (
    feedback_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    feature_slug TEXT,
    content TEXT NOT NULL,
    sentiment_score FLOAT,
    metadata TEXT DEFAULT '{}',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Phase 53: Distributed Backup & Archive Layer
CREATE TABLE IF NOT EXISTS archival_snapshots (
    snapshot_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    original_block_ids TEXT NOT NULL, -- List of storage blocks archived
    archive_node_ids TEXT NOT NULL, -- Distributed backup nodes
    total_size_bytes BIGINT NOT NULL,
    checksum TEXT NOT NULL
);

-- Phase 54: Security Audit Trail
CREATE TABLE IF NOT EXISTS security_audit_events (
    event_id TEXT PRIMARY KEY,
    event_type TEXT NOT NULL, -- privilege_escalation, key_validation, pentest
    severity TEXT NOT NULL, -- low, medium, high, critical
    outcome TEXT NOT NULL, -- prevented, suspicious, verified
    details TEXT DEFAULT '{}',
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);

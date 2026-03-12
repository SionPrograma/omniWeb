-- Migration 012: Human Development Network
CREATE TABLE IF NOT EXISTS cognitive_metrics (
    user_id TEXT,
    metric_name TEXT,
    score REAL,
    confidence REAL,
    last_detected DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, metric_name)
);

CREATE TABLE IF NOT EXISTS user_opportunities (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    opp_type TEXT,
    description TEXT,
    required_skills TEXT, -- JSON list
    match_score REAL,
    source TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Note: user_skills and certifications already exist from Phase Z, 
-- but we might add columns or use them as-is.
-- Adding cognitive profile summary table
CREATE TABLE IF NOT EXISTS skill_profiles (
    user_id TEXT PRIMARY KEY,
    top_skills TEXT, -- JSON list
    learning_speed REAL,
    last_analysis DATETIME DEFAULT CURRENT_TIMESTAMP
);

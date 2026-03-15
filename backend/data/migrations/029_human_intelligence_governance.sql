-- Migration 029: Human Intelligence & Governance Expansion

-- user_memory_timeline: Chronicling user milestones
CREATE TABLE IF NOT EXISTS user_memory_timeline (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    milestone_type TEXT NOT NULL, -- e.g., 'account_creation', 'first_login', 'reputation_milestone', 'bug_report', 'onboarding_help'
    description TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    metadata TEXT, -- JSON encoded extra data
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- reputation_graph_edges: Trust system connecting users
CREATE TABLE IF NOT EXISTS reputation_graph_edges (
    id TEXT PRIMARY KEY,
    source_user_id TEXT NOT NULL,
    target_user_id TEXT NOT NULL,
    interaction_type TEXT NOT NULL, -- e.g., 'invitation', 'collaboration', 'assistance', 'moderation'
    trust_score REAL DEFAULT 0.0,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    metadata TEXT, -- JSON encoded extra data
    FOREIGN KEY (source_user_id) REFERENCES users(id),
    FOREIGN KEY (target_user_id) REFERENCES users(id)
);

-- leadership_insights: AI Host recommendations for governance
CREATE TABLE IF NOT EXISTS leadership_insights (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    insight_type TEXT DEFAULT 'leadership_detection', -- leadership_detection, hidden_skill, suspicious_behavior
    message TEXT NOT NULL,
    status TEXT DEFAULT 'pending', -- pending, approved, rejected, implemented
    recommender TEXT DEFAULT 'AI_Host',
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    metadata TEXT, -- JSON encoded extra data
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Indices for performance
CREATE INDEX IF NOT EXISTS idx_timeline_user ON user_memory_timeline(user_id);
CREATE INDEX IF NOT EXISTS idx_reputation_source ON reputation_graph_edges(source_user_id);
CREATE INDEX IF NOT EXISTS idx_reputation_target ON reputation_graph_edges(target_user_id);
CREATE INDEX IF NOT EXISTS idx_leadership_user ON leadership_insights(user_id);

-- Migration 011: Universal Education Engine
CREATE TABLE IF NOT EXISTS user_skills (
    concept TEXT PRIMARY KEY,
    level REAL DEFAULT 0.0,
    experience_points INTEGER DEFAULT 0,
    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS learning_paths (
    id TEXT PRIMARY KEY,
    topic TEXT NOT NULL,
    target_skill_level INTEGER,
    steps TEXT, -- JSON list of LearningStep
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    completed INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS certifications (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    user_id TEXT,
    issue_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    metadata TEXT, -- JSON
    verified INTEGER DEFAULT 1
);

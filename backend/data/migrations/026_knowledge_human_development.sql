-- PHASES 30 - 36: KNOWLEDGE & HUMAN DEVELOPMENT BLOCK

-- Phase 30: Knowledge Storage Layer
CREATE TABLE IF NOT EXISTS knowledge_units (
    unit_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    type TEXT NOT NULL, -- concept, lesson, note, project, reference
    content TEXT,
    semantic_vector VECTOR(1536), -- For indexing and distance scoring
    block_id TEXT REFERENCES storage_blocks(block_id),
    metadata TEXT DEFAULT '{}',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Phase 31: Knowledge Graph Expansion (Global)
CREATE TABLE IF NOT EXISTS knowledge_relationships (
    relation_id TEXT PRIMARY KEY,
    source_unit_id TEXT REFERENCES knowledge_units(unit_id),
    target_unit_id TEXT REFERENCES knowledge_units(unit_id),
    type TEXT NOT NULL, -- link, clusters, dependency, distance
    weight FLOAT DEFAULT 1.0,
    metadata TEXT DEFAULT '{}'
);

-- Phase 32: Adaptive Learning Path Engine
CREATE TABLE IF NOT EXISTS learning_paths (
    path_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    title TEXT NOT NULL,
    target_skill TEXT,
    progression_state TEXT DEFAULT '{}', -- Current nodes completed
    status TEXT DEFAULT 'active', -- active, completed, skipped
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Phase 33: Certification Engine
CREATE TABLE IF NOT EXISTS skill_certifications (
    cert_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    skill_name TEXT NOT NULL,
    level TEXT NOT NULL, -- beginner, intermediate, advanced, master
    verification_hash TEXT NOT NULL, -- Cryptographic signature
    proof_of_knowledge TEXT NOT NULL, -- Link to test/project
    granted_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Phase 34: Opportunity & Work Engine
CREATE TABLE IF NOT EXISTS work_opportunities (
    opp_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    required_skills TEXT DEFAULT '[]',
    reward_type TEXT,
    reward_value FLOAT,
    status TEXT DEFAULT 'open',
    source_type TEXT DEFAULT 'internal', -- internal, freelancer, local
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Phase 35: Universal Communication Engine
CREATE TABLE IF NOT EXISTS comm_sessions (
    session_id TEXT PRIMARY KEY,
    participants TEXT DEFAULT '[]',
    languages TEXT DEFAULT '[]', -- List of languages in session
    transcript_id TEXT REFERENCES storage_blocks(block_id),
    summarization TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Phase 36: Accessibility Interaction Layer
CREATE TABLE IF NOT EXISTS accessibility_profiles (
    user_id TEXT PRIMARY KEY,
    voice_navigation_enabled BOOLEAN DEFAULT FALSE,
    braille_output_mode BOOLEAN DEFAULT FALSE,
    cognitive_simplification_level INTEGER DEFAULT 0, -- 0: Normal, 1: Simple, 2: Ultra-Simple
    sign_language_atlas TEXT DEFAULT '{}',
    preferences TEXT DEFAULT '{}'
);

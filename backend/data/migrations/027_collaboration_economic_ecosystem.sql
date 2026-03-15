-- PHASES 37 - 45: COLLABORATION & ECONOMIC ECOSYSTEM

-- Phase 37: Reputation Engine
CREATE TABLE IF NOT EXISTS reputation_profiles (
    user_id TEXT PRIMARY KEY,
    score FLOAT DEFAULT 100.0,
    contribution_count INTEGER DEFAULT 0,
    peer_validations INTEGER DEFAULT 0,
    certification_bonus FLOAT DEFAULT 0.0,
    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS reputation_history (
    history_id TEXT PRIMARY KEY,
    user_id TEXT REFERENCES reputation_profiles(user_id),
    change_amount FLOAT NOT NULL,
    reason TEXT NOT NULL,
    source_id TEXT, -- Link to project, chip, or cert
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Phase 38: Project Collaboration Engine
CREATE TABLE IF NOT EXISTS collaborative_projects (
    project_id TEXT PRIMARY KEY,
    creator_id TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    status TEXT DEFAULT 'draft', -- draft, active, archived, completed
    metadata TEXT DEFAULT '{}', -- Roles, resources, etc.
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS project_members (
    project_id TEXT REFERENCES collaborative_projects(project_id) ON DELETE CASCADE,
    user_id TEXT NOT NULL,
    role TEXT NOT NULL, -- admin, contributor, viewer
    joined_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (project_id, user_id)
);

-- Phase 39: Creator Labs
CREATE TABLE IF NOT EXISTS creator_labs (
    lab_id TEXT PRIMARY KEY,
    owner_id TEXT NOT NULL,
    title TEXT NOT NULL,
    status TEXT DEFAULT 'experimental',
    workspace_snapshot_id TEXT REFERENCES storage_blocks(block_id),
    is_private BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Phase 40 & 41: Knowledge Market & Skill Economy
CREATE TABLE IF NOT EXISTS ecosystem_listings (
    listing_id TEXT PRIMARY KEY,
    owner_id TEXT NOT NULL,
    type TEXT NOT NULL, -- knowledge_offer, mentorship, skill_service, project_bid
    title TEXT NOT NULL,
    description TEXT,
    price_value FLOAT DEFAULT 0.0,
    price_currency TEXT DEFAULT 'CREDITS',
    status TEXT DEFAULT 'active',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Phase 42: Global Community Layer
CREATE TABLE IF NOT EXISTS global_communities (
    community_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    topic_cluster TEXT,
    member_count INTEGER DEFAULT 0,
    is_official BOOLEAN DEFAULT FALSE,
    metadata TEXT DEFAULT '{}',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Phase 43: Personal AI Mentor (Behavior Learning)
CREATE TABLE IF NOT EXISTS ai_mentor_profiles (
    user_id TEXT PRIMARY KEY,
    learning_style TEXT DEFAULT 'visual',
    focus_areas TEXT DEFAULT '[]',
    productivity_trends TEXT DEFAULT '{}',
    last_suggestion_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Phase 44: Omniverse Gateway (Spatial Mapping)
CREATE TABLE IF NOT EXISTS omniverse_gateways (
    gateway_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    title TEXT NOT NULL,
    spatial_coordinates TEXT NOT NULL, -- {x, y, z, rotation}
    target_workspace_id TEXT,
    metadata TEXT DEFAULT '{}',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

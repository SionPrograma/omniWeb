-- Migration: Swarm Persistence for Shadow Constructors
-- Ensures that technical proposals survive backend restarts.

CREATE TABLE IF NOT EXISTS swarm_proposals (
    shadow_id TEXT PRIMARY KEY,
    mission_id TEXT NOT NULL,
    microtask TEXT,
    target_layer TEXT,
    target_file TEXT,
    state TEXT,
    proposal_json TEXT, -- Serialized ShadowConstructorProposal
    auditor_note TEXT,
    context_json TEXT,  -- Serialized context dict
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_swarm_mission ON swarm_proposals(mission_id);

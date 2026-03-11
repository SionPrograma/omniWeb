-- Migration 008: Knowledge Graph Implementation
-- Version: v0.6.3
-- Goal: Transform long-term memory into relational knowledge.

CREATE TABLE IF NOT EXISTS knowledge_nodes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    node_type TEXT NOT NULL, -- topic, concept, project, workflow, chip, learning_domain, skill, session
    name TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    importance_score REAL DEFAULT 0.0,
    metadata TEXT -- JSON encoded field
);

CREATE TABLE IF NOT EXISTS knowledge_edges (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_node INTEGER NOT NULL,
    target_node INTEGER NOT NULL,
    relationship TEXT NOT NULL, -- USES, RELATES_TO, PART_OF, LEADS_TO, REQUIRES, EVOLVES_TO, STUDIED_WITH
    weight REAL DEFAULT 1.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata TEXT, -- JSON field for edge details
    FOREIGN KEY (source_node) REFERENCES knowledge_nodes(id) ON DELETE CASCADE,
    FOREIGN KEY (target_node) REFERENCES knowledge_nodes(id) ON DELETE CASCADE
);

-- Indices for fast graph traversal and search
CREATE INDEX IF NOT EXISTS idx_knowledge_nodes_name ON knowledge_nodes(name);
CREATE INDEX IF NOT EXISTS idx_knowledge_nodes_type ON knowledge_nodes(node_type);
CREATE INDEX IF NOT EXISTS idx_knowledge_edges_source ON knowledge_edges(source_node);
CREATE INDEX IF NOT EXISTS idx_knowledge_edges_target ON knowledge_edges(target_node);
CREATE INDEX IF NOT EXISTS idx_knowledge_edges_rel ON knowledge_edges(relationship);

-- Create a unique constraint on node name/type to prevent duplicates during graph building
CREATE UNIQUE INDEX IF NOT EXISTS idx_unique_node ON knowledge_nodes(node_type, name);

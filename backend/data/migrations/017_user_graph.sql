-- Migration 017: User Personal Knowledge Graph (Phase 18)
-- Semantic relationships between user personal logbook entries

CREATE TABLE IF NOT EXISTS user_graph_nodes (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    entry_id TEXT, -- Link to user_logbooks(id) if applicable
    node_type TEXT NOT NULL, -- idea, task, note, concept, chip
    content TEXT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    metadata TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (entry_id) REFERENCES user_logbooks(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS user_graph_edges (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    source_node TEXT NOT NULL,
    target_node TEXT NOT NULL,
    relation_type TEXT NOT NULL, -- related_to, derived_from, depends_on, mentions_chip
    confidence_score REAL DEFAULT 1.0,
    metadata TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (source_node) REFERENCES user_graph_nodes(id) ON DELETE CASCADE,
    FOREIGN KEY (target_node) REFERENCES user_graph_nodes(id) ON DELETE CASCADE
);

CREATE INDEX idx_user_graph_nodes_user ON user_graph_nodes(user_id);
CREATE INDEX idx_user_graph_nodes_entry ON user_graph_nodes(entry_id);
CREATE INDEX idx_user_graph_edges_user ON user_graph_edges(user_id);
CREATE INDEX idx_user_graph_edges_source ON user_graph_edges(source_node);
CREATE INDEX idx_user_graph_edges_target ON user_graph_edges(target_node);

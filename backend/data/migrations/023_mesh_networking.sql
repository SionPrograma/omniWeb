-- PHASE 26: MESH NETWORKING LAYER
-- Peer Discovery & Mesh State

CREATE TABLE IF NOT EXISTS cluster_peers (
    node_id TEXT PRIMARY KEY REFERENCES cluster_nodes(node_id),
    peer_address TEXT NOT NULL, -- Direct IP/URL
    peer_region TEXT,
    latency FLOAT DEFAULT 0.0,
    last_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'connected', -- connected, degraded, disconnected
    metadata TEXT DEFAULT '{}'
);

-- Index for quick connectivity checks
CREATE INDEX IF NOT EXISTS idx_peer_status ON cluster_peers(status);
CREATE INDEX IF NOT EXISTS idx_peer_last_seen ON cluster_peers(last_seen);

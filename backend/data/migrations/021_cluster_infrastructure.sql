-- PHASE 24: MULTI-NODE INFRASTRUCTURE
-- Cluster Node Registry

CREATE TABLE IF NOT EXISTS cluster_nodes (
    node_id TEXT PRIMARY KEY,
    node_role TEXT NOT NULL, -- primary, worker, storage, edge
    node_region TEXT NOT NULL,
    node_status TEXT NOT NULL DEFAULT 'offline', -- online, offline, draining, maintenance
    node_secret TEXT, -- encrypted or hashed secret for node auth
    node_url TEXT NOT NULL,
    uptime INTEGER DEFAULT 0,
    last_heartbeat DATETIME DEFAULT CURRENT_TIMESTAMP,
    cpu_usage FLOAT DEFAULT 0.0,
    memory_usage FLOAT DEFAULT 0.0,
    active_chips INTEGER DEFAULT 0,
    latency FLOAT DEFAULT 0.0,
    connected_services TEXT DEFAULT '[]',
    metadata TEXT DEFAULT '{}',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Index for quick status checks
CREATE INDEX IF NOT EXISTS idx_node_status ON cluster_nodes(node_status);
CREATE INDEX IF NOT EXISTS idx_node_last_heartbeat ON cluster_nodes(last_heartbeat);

-- Initial primary node entry
INSERT INTO cluster_nodes (node_id, node_role, node_region, node_status, node_url, connected_services)
VALUES ('primary-node-01', 'primary', 'us-east', 'online', 'http://localhost:8000', '["db", "redis", "ai-host"]')
;;

-- PHASE 29: OMNIWEB DISTRIBUTED STORAGE GRID
-- Chunk-based storage model with redundancy

CREATE TABLE IF NOT EXISTS storage_nodes (
    node_id TEXT PRIMARY KEY REFERENCES cluster_nodes(node_id),
    total_capacity_bytes BIGINT NOT NULL,
    used_space_bytes BIGINT DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    last_health_check DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS storage_blocks (
    block_id TEXT PRIMARY KEY,
    data_type TEXT NOT NULL, -- workspace, logbook, graph, chip_asset, snapshot
    content_hash TEXT NOT NULL,
    size_bytes INTEGER NOT NULL,
    metadata TEXT DEFAULT '{}',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS storage_fragments (
    fragment_id TEXT PRIMARY KEY,
    block_id TEXT REFERENCES storage_blocks(block_id) ON DELETE CASCADE,
    node_id TEXT REFERENCES cluster_nodes(node_id),
    status TEXT DEFAULT 'available', -- available, replicating, corrupt
    fragment_index INTEGER NOT NULL, -- For future erasure coding support
    replicated_to_nodes TEXT DEFAULT '[]', -- List of other nodes holding this fragment
    last_verified DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_fragment_block ON storage_fragments(block_id);
CREATE INDEX IF NOT EXISTS idx_fragment_node ON storage_fragments(node_id);
CREATE INDEX IF NOT EXISTS idx_block_hash ON storage_blocks(content_hash);

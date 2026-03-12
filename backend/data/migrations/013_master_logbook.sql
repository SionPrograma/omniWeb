CREATE TABLE IF NOT EXISTS master_logbook (
    id TEXT PRIMARY KEY,
    type TEXT NOT NULL,
    content TEXT NOT NULL,
    priority TEXT NOT NULL,
    chip_reference TEXT,
    status TEXT NOT NULL,
    author_role TEXT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    metadata TEXT -- JSON string
);

CREATE INDEX IF NOT EXISTS idx_logbook_type ON master_logbook(type);
CREATE INDEX IF NOT EXISTS idx_logbook_status ON master_logbook(status);
CREATE INDEX IF NOT EXISTS idx_logbook_chip ON master_logbook(chip_reference);

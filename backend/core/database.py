import sqlite3
import os
import logging
import asyncio
import json
from backend.core.config import settings

logger = logging.getLogger(__name__)

class DatabaseManager:
    """
    Base SQLite Infrastructure for OmniWeb.
    Provides simple connection management and ensures data directory exists.
    """
    def __init__(self, db_path: str = None):
        self.db_path = db_path or settings.DATABASE_URL
        self._ensure_data_dir()

    def _ensure_data_dir(self):
        """Ensures the directory for the database file exists."""
        data_dir = os.path.dirname(self.db_path)
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
            logger.info(f"Created data directory: {data_dir}")
        
        # --- Phase 0: DB Awareness ---
        try:
            db_files = [f for f in os.listdir(data_dir) if f.endswith(".db")]
            if len(db_files) > 1:
                logger.warning(f"DB AWARENESS: Multiple database files detected in {data_dir}: {db_files}. Using {os.path.basename(self.db_path)} as Source of Truth.")
        except Exception as e:
            logger.debug(f"DB AWARENESS: Could not list directory {data_dir}: {e}")

    def get_connection(self, internal: bool = False):
        """
        Returns a new connection to the SQLite database.
        Recommended to use as a context manager if possible, 
        or close manually.
        """
        if not internal:
            # Integra el modelo operativo de permisos de chip.
            from backend.core.permissions import enforce_permission, _current_ctx_info
            
            # Log to debug context propagation
            ctx = _current_ctx_info.get()
            logger.debug(f"DB ACCESS: Context detected: {ctx}")
            
            try:
                enforce_permission("db_access")
            except Exception as e:
                logger.error(f"Module attempted unauthorized DB access (Context: {ctx}): {e}")
                raise

        try:
            # We use check_same_thread=False because we manage the session lifecycle 
            # through AsyncDatabaseSession which handles the threading bridge.
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            # Row factory enables column access by name
            conn.row_factory = sqlite3.Row
            # Enable Foreign Keys
            conn.execute("PRAGMA foreign_keys = ON")
            # Enable WAL mode for concurrency
            conn.execute("PRAGMA journal_mode = WAL")
            return conn
        except sqlite3.Error as e:
            logger.error(f"Error connecting to SQLite ({self.db_path}): {e}")
            raise

    def get_session(self):
        """
        OmniWeb Async Session Wrapper.
        Provides a context manager for async database operations using a simple bridge.
        """
        return AsyncDatabaseSession(self)

    def init_db(self):
        """
        Initializes core system tables.
        """
        logger.info(f"Initializing SQLite persistence at {self.db_path}")
        with self.get_connection(internal=True) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS system_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_name TEXT NOT NULL,
                    payload TEXT,
                    source_chip TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS system_locks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    resource_key TEXT UNIQUE NOT NULL,
                    mission_id TEXT NOT NULL,
                    lock_type TEXT DEFAULT 'WRITE', -- WRITE, READ
                    reason TEXT,
                    acquired_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS governance_chat_signals (
                    signal_id TEXT PRIMARY KEY,
                    message_id TEXT,
                    conversation_id TEXT,
                    signal_type TEXT NOT NULL,
                    target_domain TEXT,
                    severity_band TEXT, -- INFO, WARN, CRITICAL
                    confidence REAL,
                    rationale TEXT,
                    suggested_adjustment TEXT,
                    adjustment_payload TEXT, -- JSON
                    status TEXT DEFAULT 'ACTIVE', -- ACTIVE, IGNORED, APPLIED
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS branch_synergy_relations (
                    relation_id TEXT PRIMARY KEY,
                    branch_a_id TEXT NOT NULL,
                    branch_b_id TEXT NOT NULL,
                    relation_type TEXT NOT NULL, -- COLLISION, REDUNDANCY, SYNERGY, DEPENDENCY
                    affected_domains TEXT, -- JSON list
                    confidence REAL,
                    rationale TEXT,
                    risk_score REAL,
                    synergy_score REAL,
                    recommended_action TEXT,
                    status TEXT DEFAULT 'ACTIVE', -- ACTIVE, ACKNOWLEDGED, RESOLVED, IGNORED
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(branch_a_id) REFERENCES roadmap_branches(branch_id),
                    FOREIGN KEY(branch_b_id) REFERENCES roadmap_branches(branch_id)
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS branch_consolidations (
                    consolidation_id TEXT PRIMARY KEY,
                    primary_branch_id TEXT NOT NULL,
                    secondary_branch_id TEXT NOT NULL,
                    relation_ref_id TEXT,
                    state TEXT DEFAULT 'PROPOSED', -- PROPOSED, ACCEPTED, POSTPONED, REJECTED, EXECUTED
                    consolidation_type TEXT, -- ABSORB, MERGE_INTENT, UNIFIED_SUCCESSOR
                    confidence REAL,
                    shared_surfaces TEXT, -- JSON
                    rationale TEXT,
                    expected_gain TEXT,
                    creator_action TEXT, -- ESCALATED, MANUAL_SYNC_REQUIRED
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(primary_branch_id) REFERENCES roadmap_branches(branch_id),
                    FOREIGN KEY(secondary_branch_id) REFERENCES roadmap_branches(branch_id),
                    FOREIGN KEY(relation_ref_id) REFERENCES branch_synergy_relations(relation_id)
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS branch_investment_audits (
                    audit_id TEXT PRIMARY KEY,
                    branch_id TEXT NOT NULL,
                    cost_score REAL,
                    cost_factors TEXT, -- JSON
                    value_score REAL,
                    value_factors TEXT, -- JSON
                    return_band TEXT, -- HIGH_VALUE_LOW_COST, HIGH_VALUE_HIGH_COST, LOW_VALUE_HIGH_COST, EXPERIMENTAL, etc.
                    rationale TEXT,
                    recommendation TEXT,
                    confidence REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(branch_id) REFERENCES roadmap_branches(branch_id)
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS governance_autopsies (
                    autopsy_id TEXT PRIMARY KEY,
                    branch_id TEXT NOT NULL,
                    reason TEXT, -- MERGE, ABORT, CONSOLIDATION
                    structural_learnings TEXT, -- JSON
                    debt_reduction_score REAL,
                    friction_alleviation REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(branch_id) REFERENCES roadmap_branches(branch_id)
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS branch_predictive_roi_advisories (
                    advisory_id TEXT PRIMARY KEY,
                    branch_id TEXT NOT NULL,
                    predicted_return_band TEXT, -- HIGH_EXPECTED_VALUE, MODERATE, HIGH_RISK_LOW_RETURN, EXPERIMENTAL, INSUFFICIENT
                    predicted_cost_band TEXT, -- HIGH, MEDIUM, LOW
                    predicted_value_band TEXT, -- HIGH, MEDIUM, LOW
                    confidence REAL,
                    rationale TEXT,
                    supporting_evidence TEXT, -- JSON with branch_refs, learning_refs, autopsy_refs
                    recommended_strategy TEXT,
                    is_active INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(branch_id) REFERENCES roadmap_branches(branch_id)
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS branch_alternative_paths (
                    path_id TEXT PRIMARY KEY,
                    branch_id TEXT NOT NULL,
                    path_type TEXT NOT NULL, -- SPLIT, SCOPE_REDUCTION, FOLLOW_PRECEDENT, RELIEF_FIRST, CONSOLIDATE, etc.
                    proposed_strategy TEXT,
                    expected_benefit TEXT,
                    expected_risk_reduction REAL,
                    confidence REAL,
                    rationale TEXT,
                    supporting_evidence TEXT, -- JSON: branch_refs, autopsy_refs, learning_refs
                    suggested_scope_change TEXT, -- JSON or textual description
                    status TEXT DEFAULT 'PROPOSED', -- PROPOSED, ACCEPTED, IGNORED, EXECUTED
                    creator_action_required INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(branch_id) REFERENCES roadmap_branches(branch_id)
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS governance_decision_ledger (
                    ledger_id TEXT PRIMARY KEY,
                    decision_type TEXT NOT NULL, -- STRATEGIC_PIVOT, RISK_OVERRIDE, CONSOLIDATION, ALTERNATIVE_PATH_ACCEPTANCE, ARBITRATION, etc.
                    target_ref_type TEXT, -- BRANCH, MISSION, DOMAIN, SYNERGY
                    target_id TEXT,
                    actor TEXT DEFAULT 'SYSTEM', -- CREATOR, SYSTEM, HYBRID
                    action_taken TEXT, -- ACCEPTED, REJECTED, SUPERSEDED, EXECUTED
                    rationale TEXT,
                    evidence_refs TEXT, -- JSON: links to autopsies, learnings, ROI audits, or synergy reports
                    severity_context TEXT, -- CRITICAL, MODERATE, LOW
                    outcome_state TEXT DEFAULT 'PENDING_OUTCOME', -- EFFECTIVE, DEGRADED, SUPERSEDED, FAILED
                    active_flag INTEGER DEFAULT 1,
                    superseded_by_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(superseded_by_id) REFERENCES governance_decision_ledger(ledger_id)
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS governance_consensus_advisories (
                    advisory_id TEXT PRIMARY KEY,
                    advisory_type TEXT NOT NULL, -- RISK_TOLERANCE_TOO_HIGH, ESCALATION_TOO_LATE, REPEAT_INEFFECTIVE_TACTIC, etc.
                    affected_domains TEXT, -- JSON list
                    confidence REAL,
                    recommendation TEXT,
                    pattern_summary TEXT,
                    ledger_refs TEXT, -- JSON list of ledger_ids
                    trace_refs TEXT, -- JSON list of trace_ids
                    severity_band TEXT, -- CRITICAL, HIGH, MODERATE, LOW
                    status TEXT DEFAULT 'PENDING', -- PENDING, ATTENDED, IGNORED
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS governance_engine_parameters (
                    param_id TEXT PRIMARY KEY,
                    engine_name TEXT NOT NULL,
                    param_key TEXT NOT NULL,
                    current_value REAL NOT NULL,
                    default_value REAL NOT NULL,
                    description TEXT,
                    last_recalibrated_at TIMESTAMP,
                    recalibration_ref_id TEXT,
                    UNIQUE(engine_name, param_key)
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS governance_recalibration_proposals (
                    recalibration_id TEXT PRIMARY KEY,
                    consensus_advisory_id TEXT,
                    target_engine TEXT NOT NULL,
                    param_key TEXT NOT NULL,
                    current_value REAL,
                    proposed_value REAL,
                    rationale TEXT,
                    confidence REAL,
                    expected_impact TEXT,
                    status TEXT DEFAULT 'PROPOSED', -- PROPOSED, APPROVED, REJECTED, REVERTED, SUPERSEDED
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(consensus_advisory_id) REFERENCES governance_consensus_advisories(advisory_id)
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS governance_projects (
                    project_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    is_current INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS governance_project_contexts (
                    context_id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    primary_domains TEXT, -- JSON
                    risk_profile_dna TEXT, -- JSON: avg_friction, high_risk_incidence, etc.
                    learning_density REAL,
                    active_thresholds TEXT, -- JSON: friction_threshold, risk_tolerance, etc.
                    confidence REAL,
                    rationale TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(project_id) REFERENCES governance_projects(project_id)
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS governance_contextual_mappings (
                    mapping_id TEXT PRIMARY KEY,
                    source_project_id TEXT NOT NULL,
                    target_project_id TEXT NOT NULL,
                    similarity_score REAL,
                    match_type TEXT, -- STRONG_CONTEXT_MATCH, SOFT_CONTEXT_MATCH, REUSABLE_LEARNING_ONLY, INSUFFICIENT
                    shared_domains TEXT, -- JSON
                    transferable_learnings TEXT, -- JSON list of learning_item_ids
                    suggested_baseline_params TEXT, -- JSON dict: param_key -> value
                    rationale TEXT,
                    transfer_risk TEXT,
                    status TEXT DEFAULT 'PROPOSED', -- PROPOSED, ACCEPTED, PARTIAL, IGNORED
                    creator_action_required INTEGER DEFAULT 1,
                    applied_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(source_project_id) REFERENCES governance_projects(project_id),
                    FOREIGN KEY(target_project_id) REFERENCES governance_projects(project_id)
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS governance_cross_project_search_traces (
                    search_id TEXT PRIMARY KEY,
                    query_context TEXT, -- JSON: what we were searching for (domain, debt, type)
                    target_project_id TEXT,
                    results_json TEXT, -- JSON mapping of found objects
                    creator_action TEXT DEFAULT 'VIEWED', -- VIEWED, ADOPTED, IGNORED
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(target_project_id) REFERENCES governance_projects(project_id)
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS governance_tactical_simulations (
                    simulation_id TEXT PRIMARY KEY,
                    source_object_type TEXT,
                    source_object_id TEXT,
                    target_domain TEXT,
                    predicted_outcome TEXT, -- LIKELY_RELIEF, PARTIAL_RELIEF, RIESGO_ALTO, etc.
                    confidence REAL,
                    transfer_risk REAL,
                    rationale TEXT,
                    contrast_factors TEXT, -- JSON: differences in dna/friction
                    recommended_preconditions TEXT, -- What must be clear before apply
                    status TEXT DEFAULT 'COMPLETED', -- COMPLETED, ADOPTED, IGNORED
                    FOREIGN KEY(source_object_id) REFERENCES governance_learning_items(learning_item_id)
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS governance_replay_syncs (
                    sync_id TEXT PRIMARY KEY,
                    simulation_id TEXT,
                    target_branch_id TEXT,
                    autopsy_id TEXT,
                    predicted_effect TEXT,
                    actual_outcome_summary TEXT,
                    replay_outcome_state TEXT, -- SIMULATION_CONFIRMED, CONTRADICTED, etc.
                    confidence_delta_proposed REAL,
                    preconditions_respected INTEGER DEFAULT 1,
                    rationale TEXT,
                    creator_action TEXT DEFAULT 'PENDING', -- APPLIED, REJECTED, IGNORED
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(simulation_id) REFERENCES governance_tactical_simulations(simulation_id),
                    FOREIGN KEY(target_branch_id) REFERENCES roadmap_branches(branch_id),
                    FOREIGN KEY(autopsy_id) REFERENCES governance_autopsies(autopsy_id)
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS governance_mission_auto_drafts (
                    draft_id TEXT PRIMARY KEY,
                    source_reasoner_result_id TEXT,
                    source_atlas_node_ref TEXT,
                    draft_type TEXT, -- RELIEF_MISSION_DRAFT, ROOT_AUDIT_DRAFT, etc.
                    target_context_ref TEXT,
                    title_suggestion TEXT,
                    objective_suggestion TEXT,
                    affected_domains TEXT, -- JSON
                    rationale TEXT,
                    suggested_constraints TEXT, -- JSON list
                    recommended_preconditions TEXT, -- JSON list
                    risk_notes TEXT,
                    confidence REAL,
                    status TEXT DEFAULT 'PROPOSED', -- PROPOSED, EDITED, ACCEPTED, REJECTED
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS governance_wisdom_feedback (
                    feedback_id TEXT PRIMARY KEY,
                    source_atlas_node_ref TEXT,
                    source_draft_ref TEXT,
                    resulting_mission_ref TEXT, -- Linked via mission_id or branch_id
                    feedback_state TEXT, -- WISDOM_CONFIRMED, CONTRADICTED, MISAPPLIED, etc.
                    predicted_value REAL,
                    actual_outcome_friction REAL,
                    preconditions_respected INTEGER,
                    proposed_confidence_delta REAL,
                    proposed_reusability_delta REAL,
                    rationale TEXT,
                    creator_decision TEXT DEFAULT 'PENDING', -- APPLIED, REJECTED, IGNORED 
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # --- PHASE 113: ENHANCE SOURCES WITH PROJECT_ID ---
            tables_to_enhance = [
                'governance_autopsies', 
                'governance_decision_ledger',
                'governance_consensus_advisories',
                'governance_learning_items'
            ]
            for table in tables_to_enhance:
                try:
                    conn.execute(f"ALTER TABLE {table} ADD COLUMN project_id TEXT DEFAULT 'PROJECT_OMNIWEB_PROD'")
                except sqlite3.OperationalError:
                    pass # Already exists or table not in main DB

            # --- INITIALIZE DEFAULT PROJECT (CONTEXT SEED) ---
            conn.execute("INSERT OR IGNORE INTO governance_projects (project_id, name, is_current) VALUES ('PROJECT_OMNIWEB_PROD', 'OmniWeb Production Core', 1)")

            # --- INITIALIZE CORE PARAMETERS (PHASE 111) ---
            params = [
                ('P1', 'PREDICTIVE_DRIFT', 'FRICTION_THRESHOLD', 65.0, 65.0, 'Umbral de fricción para activar warnings predictivos.'),
                ('P2', 'PREDICTIVE_DRIFT', 'CONFIDENCE_BIAS', 1.0, 1.0, 'Multiplicador de confianza para señales de drift.'),
                ('P3', 'PREDICTIVE_ROI', 'SUCCESS_CONFIDENCE', 0.8, 0.8, 'Confianza base para proyecciones de alto retorno.'),
                ('P4', 'GOVERNANCE_ADVISOR', 'ACCEPTED_RISK_THRESHOLD', 0.5, 0.5, 'Umbral para endurecer advertencias de deuda acumulada.')
            ]
            for p in params:
                conn.execute("""
                    INSERT OR IGNORE INTO governance_engine_parameters (
                        param_id, engine_name, param_key, current_value, default_value, description
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, p)
            
            conn.commit()
            
            # --- Phase 0: Identity Seeding (Idempotent) ---
            SYSTEM_UUID = "00000000-0000-0000-0000-000000000000"
            try:
                row = conn.execute("SELECT 1 FROM users WHERE id = ?", (SYSTEM_UUID,)).fetchone()
                if not row:
                    conn.execute("""
                        INSERT INTO users (id, username, hashed_password, role)
                        VALUES (?, 'system', 'system-vault-locked', 'admin')
                    """, (SYSTEM_UUID,))
                    conn.commit()
                    logger.info(f"IDENTITY SEEDING: Created System User (id={SYSTEM_UUID})")
                else:
                    logger.debug(f"IDENTITY SEEDING: System User already exists.")
            except sqlite3.OperationalError as e:
                if "no such table: users" in str(e):
                    logger.warning("IDENTITY SEEDING: 'users' table not yet available (waiting for migrations).")
                else:
                    logger.error(f"IDENTITY SEEDING: Unexpected error seeding system user: {e}")

        logger.info("System core tables initialized.")

    def run_migrations(self):
        """
        Executes raw SQL migration files inside backend/data/migrations.
        Ensures versioned schema evolutions.
        """
        data_dir = os.path.dirname(self.db_path)
        migrations_dir = os.path.join(data_dir, "migrations")
        os.makedirs(migrations_dir, exist_ok=True)
            
        with self.get_connection(internal=True) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS system_migrations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filename TEXT UNIQUE NOT NULL,
                    applied_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
            
            applied = {row["filename"] for row in conn.execute("SELECT filename FROM system_migrations")}
            files = sorted([f for f in os.listdir(migrations_dir) if f.endswith(".sql")])
            for file in files:
                if file not in applied:
                    logger.info(f"Applying DB migration: {file}")
                    with open(os.path.join(migrations_dir, file), "r", encoding="utf-8") as f:
                        sql = f.read()
                    
                    try:
                        conn.executescript(sql)
                        conn.execute("INSERT INTO system_migrations (filename) VALUES (?)", (file,))
                        conn.commit()
                    except Exception as e:
                        logger.error(f"Migration {file} failed: {e}")
                        conn.rollback()
                        raise

    def backup_db(self, destination_path: str = None) -> str:
        """
        Creates a consistent online backup of the SQLite database.
        Returns the absolute path to the backup file.
        """
        import time
        if not destination_path:
            filename = f"omniweb_backup_{int(time.time())}.db"
            data_dir = os.path.dirname(self.db_path)
            destination_path = os.path.join(data_dir, "backups", filename)
            
        os.makedirs(os.path.dirname(destination_path), exist_ok=True)
        
        logger.info(f"Creating DB backup at {destination_path}")
        # Note: We use sqlite3.connect directly here to bypass standard permission checks
        # as this is a core infrastructural operation, but we still do it safely.
        with sqlite3.connect(self.db_path) as source:
            with sqlite3.connect(destination_path) as dest:
                source.backup(dest)
                
        logger.info("DB backup completed successfully.")
        return destination_path

    def restore_db(self, source_path: str):
        """
        Restores the main database from a backup file path.
        Uses the backup API to safely overwrite the current database online.
        """
        if not os.path.exists(source_path):
            raise FileNotFoundError(f"Backup file not found: {source_path}")

        logger.warning(f"Restoring database from {source_path}...")
        
        # We use direct connections to bypass permission logic for this critical operation
        with sqlite3.connect(source_path) as source:
            with sqlite3.connect(self.db_path) as dest:
                source.backup(dest)
                
        logger.info("Database restoration complete.")

# Global instance for shared access
db_manager = DatabaseManager()

class AsyncDatabaseSession:
    """
    A simple bridge for modules expecting 'async with db_manager.get_session()'.
    Uses threading to keep the async loop free.
    """
    def __init__(self, manager: DatabaseManager):
        self.manager = manager
        self.conn = None

    async def __aenter__(self):
        self.conn = await asyncio.to_thread(self.manager.get_connection)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.conn:
            def _cleanup():
                if exc_type is None:
                    self.conn.commit()
                else:
                    self.conn.rollback()
                self.conn.close()
            await asyncio.to_thread(_cleanup)

    async def execute(self, query, parameters: dict = None):
        """Executes a query and returns a result wrapper."""
        if parameters is None:
            parameters = {}
        
        # Serialize list/dict parameters to JSON strings for SQLite
        import json
        for key, val in parameters.items():
            if isinstance(val, (list, dict)):
                parameters[key] = json.dumps(val)
        
        # Handle SQLAlchemy text objects if passed
        if hasattr(query, "text"):
            query = query.text
        elif not isinstance(query, str):
            query = str(query)
            
        def _execute():
            # Using fetchall() to avoid cursor threading issues
            cursor = self.conn.execute(query, parameters)
            
            # Use cursor.description safely (it is None for non-SELECT queries)
            cols = [desc[0] for desc in cursor.description] if cursor.description else []
            rows = cursor.fetchall() if cursor.description else []
            
            # Map to dicts and handle JSON automatically
            results = []
            for row in rows:
                d = dict(row)
                for key, val in d.items():
                    if isinstance(val, str) and (val.startswith('[') or val.startswith('{')):
                        try:
                            d[key] = json.loads(val)
                        except: pass
                results.append(d)
            return results
            
        rows = await asyncio.to_thread(_execute)
        return AsyncResultWrapper(rows)

    async def commit(self):
        """Manually commit the transaction."""
        await asyncio.to_thread(self.conn.commit)

class AsyncResultWrapper:
    """Wraps a list of dicts to simulate a cursor for fetchone/iteration."""
    def __init__(self, rows):
        self.rows = rows
        self._index = 0

    def __iter__(self):
        return iter(self.rows)

    def fetchone(self):
        if self._index < len(self.rows):
            row = self.rows[self._index]
            self._index += 1
            return row
        return None

    def fetchall(self):
        return self.rows

    def mappings(self):
        """SQLAlchemy compatibility layer."""
        return self

    def all(self):
        """SQLAlchemy compatibility layer."""
        return self.rows

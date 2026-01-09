-- =============================================================================
-- AUDIT TRAIL SCHEMA (Chain of Custody)
-- =============================================================================
-- Intelligence-Grade: Lückenlose Nachverfolgung aller Verarbeitungsschritte
-- Append-Only Design: Keine Updates, nur Inserts
-- =============================================================================

-- Audit Trail Table
CREATE TABLE IF NOT EXISTS audit_trail (
    id SERIAL PRIMARY KEY,
    
    -- File Identification
    file_hash TEXT NOT NULL,           -- SHA256 des Dateiinhalts
    filename TEXT NOT NULL,
    filepath TEXT,
    
    -- Processing Stage
    stage TEXT NOT NULL,               -- intake, extract, enrich, index, dlq
    status TEXT NOT NULL,              -- started, completed, failed, skipped
    
    -- Worker Info
    worker_id TEXT,                    -- Container ID / Worker Name
    worker_type TEXT,                  -- documents, audio, images, video
    queue_name TEXT,                   -- Source queue name
    
    -- Timing
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    processing_time_ms INTEGER,        -- Duration in milliseconds
    
    -- Results
    output_queue TEXT,                 -- Next queue (if any)
    error_message TEXT,                -- Error details (if failed)
    retry_count INTEGER DEFAULT 0,
    
    -- Metadata (JSONB for flexibility)
    metadata JSONB DEFAULT '{}'::jsonb
);

-- =============================================================================
-- INDEXES (für schnelle Abfragen)
-- =============================================================================

-- Suche nach Datei
CREATE INDEX IF NOT EXISTS idx_audit_file_hash ON audit_trail(file_hash);

-- Zeitbasierte Abfragen
CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_trail(timestamp DESC);

-- Status-basierte Abfragen (z.B. alle Fehler)
CREATE INDEX IF NOT EXISTS idx_audit_status ON audit_trail(status);

-- Stage-basierte Abfragen
CREATE INDEX IF NOT EXISTS idx_audit_stage ON audit_trail(stage);

-- Composite für häufige Abfragen
CREATE INDEX IF NOT EXISTS idx_audit_file_stage ON audit_trail(file_hash, stage);

-- =============================================================================
-- VIEWS (für einfache Auswertung)
-- =============================================================================

-- Aktive Fehler (letzte 24h)
CREATE OR REPLACE VIEW v_recent_failures AS
SELECT 
    file_hash,
    filename,
    stage,
    error_message,
    retry_count,
    timestamp,
    worker_id
FROM audit_trail
WHERE status = 'failed'
  AND timestamp > NOW() - INTERVAL '24 hours'
ORDER BY timestamp DESC;

-- Processing Pipeline Status per File
CREATE OR REPLACE VIEW v_file_pipeline_status AS
SELECT 
    file_hash,
    filename,
    jsonb_object_agg(stage, status) as stages,
    MIN(timestamp) as first_seen,
    MAX(timestamp) as last_updated,
    SUM(processing_time_ms) as total_processing_ms
FROM audit_trail
GROUP BY file_hash, filename;

-- Worker Performance
CREATE OR REPLACE VIEW v_worker_stats AS
SELECT 
    worker_type,
    worker_id,
    COUNT(*) as jobs_processed,
    COUNT(*) FILTER (WHERE status = 'completed') as successful,
    COUNT(*) FILTER (WHERE status = 'failed') as failed,
    AVG(processing_time_ms) as avg_processing_ms,
    MAX(timestamp) as last_active
FROM audit_trail
WHERE timestamp > NOW() - INTERVAL '1 hour'
GROUP BY worker_type, worker_id;

-- Queue Throughput
CREATE OR REPLACE VIEW v_queue_throughput AS
SELECT 
    DATE_TRUNC('minute', timestamp) as minute,
    queue_name,
    COUNT(*) as jobs,
    AVG(processing_time_ms) as avg_ms
FROM audit_trail
WHERE timestamp > NOW() - INTERVAL '1 hour'
GROUP BY DATE_TRUNC('minute', timestamp), queue_name
ORDER BY minute DESC;

-- =============================================================================
-- FUNCTIONS (für API-Endpunkte)
-- =============================================================================

-- Get full audit trail for a file
CREATE OR REPLACE FUNCTION get_file_audit_trail(p_file_hash TEXT)
RETURNS TABLE (
    stage TEXT,
    status TEXT,
    worker_id TEXT,
    timestamp TIMESTAMPTZ,
    processing_time_ms INTEGER,
    error_message TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        at.stage,
        at.status,
        at.worker_id,
        at.timestamp,
        at.processing_time_ms,
        at.error_message
    FROM audit_trail at
    WHERE at.file_hash = p_file_hash
    ORDER BY at.timestamp ASC;
END;
$$ LANGUAGE plpgsql;

-- Log a new audit entry
CREATE OR REPLACE FUNCTION log_audit(
    p_file_hash TEXT,
    p_filename TEXT,
    p_filepath TEXT,
    p_stage TEXT,
    p_status TEXT,
    p_worker_id TEXT DEFAULT NULL,
    p_worker_type TEXT DEFAULT NULL,
    p_queue_name TEXT DEFAULT NULL,
    p_processing_time_ms INTEGER DEFAULT NULL,
    p_output_queue TEXT DEFAULT NULL,
    p_error_message TEXT DEFAULT NULL,
    p_metadata JSONB DEFAULT '{}'::jsonb
)
RETURNS INTEGER AS $$
DECLARE
    v_id INTEGER;
BEGIN
    INSERT INTO audit_trail (
        file_hash, filename, filepath, stage, status,
        worker_id, worker_type, queue_name,
        processing_time_ms, output_queue, error_message, metadata
    ) VALUES (
        p_file_hash, p_filename, p_filepath, p_stage, p_status,
        p_worker_id, p_worker_type, p_queue_name,
        p_processing_time_ms, p_output_queue, p_error_message, p_metadata
    )
    RETURNING id INTO v_id;
    
    RETURN v_id;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- SAMPLE QUERIES
-- =============================================================================

-- All processing steps for a file:
-- SELECT * FROM get_file_audit_trail('abc123...');

-- Recent failures:
-- SELECT * FROM v_recent_failures;

-- Worker performance:
-- SELECT * FROM v_worker_stats;

-- Files stuck in a stage:
-- SELECT file_hash, filename, timestamp 
-- FROM audit_trail 
-- WHERE stage = 'extract' 
--   AND status = 'started'
--   AND timestamp < NOW() - INTERVAL '10 minutes';

-- F:\conductor\scripts\schema_quarantine.sql
-- Erweiterung des Shadow Ledger für Quarantäne und Qualitätsprüfung

-- Quarantäne-Ordner erstellen (über Filesystem, nicht SQL)
-- F:/_Quarantine/_processing_error/
-- F:/_Quarantine/_low_confidence/
-- F:/_Quarantine/_review_needed/
-- F:/_Quarantine/_duplicates/

-- Tabelle: Quarantäne-Log
CREATE TABLE IF NOT EXISTS quarantine_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- Referenz zur Haupttabelle
    file_id INTEGER REFERENCES file_metadata(id),
    sha256 TEXT NOT NULL,
    
    -- Quarantäne-Details
    quarantine_reason TEXT NOT NULL,
    -- Mögliche Gründe:
    -- PROCESSING_ERROR   = Exception während Verarbeitung
    -- LOW_CONFIDENCE     = KI-Konfidenz < 50%
    -- REVIEW_NEEDED      = Plausibilitätsprüfung fehlgeschlagen
    -- DUPLICATE          = Exaktes Duplikat (SHA-256 Match)
    -- UNSUPPORTED_TYPE   = Dateityp nicht verarbeitbar
    -- CORRUPTED_FILE     = Datei beschädigt/nicht lesbar
    
    quarantine_path TEXT NOT NULL,       -- Aktueller Pfad in Quarantäne
    original_inbox_path TEXT NOT NULL,   -- Ursprünglicher Pfad in _Inbox
    
    -- Fehlerdetails
    error_message TEXT,
    error_traceback TEXT,
    failed_quality_gates TEXT,           -- JSON Array: ["CATEGORY_MISMATCH", "LOW_CONFIDENCE"]
    
    -- Timestamps
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- Resolution
    resolved_at DATETIME,
    resolved_by TEXT,                    -- 'auto', 'user:admin', 'system:retry'
    resolution TEXT,                     -- 'approved', 'rejected', 'reprocessed', 'deleted'
    resolution_notes TEXT
);

-- Tabelle: Qualitätsprüfungen (detailliert pro Datei)
CREATE TABLE IF NOT EXISTS quality_checks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_id INTEGER REFERENCES file_metadata(id),
    
    -- Check-Details
    check_name TEXT NOT NULL,
    -- Mögliche Checks:
    -- CATEGORY_PLAUSIBILITY  = Passt Kategorie zum MIME-Type?
    -- FILENAME_QUALITY       = Ist der generierte Name sinnvoll?
    -- TARGET_FOLDER_VALID    = Existiert der Zielordner?
    -- NO_COLLISION           = Keine Namenskollision am Ziel?
    -- CONFIDENCE_THRESHOLD   = Ist die Konfidenz ausreichend?
    -- CONTENT_EXTRACTED      = Wurde Inhalt extrahiert?
    -- ENTITY_EXTRACTION      = Wurden Entitäten erkannt?
    -- DATE_VALID             = Ist das extrahierte Datum gültig?
    -- AMOUNT_VALID           = Ist der extrahierte Betrag gültig?
    
    check_passed BOOLEAN NOT NULL,
    check_score REAL,                    -- 0.0 - 1.0 für graduierte Checks
    check_details TEXT,                  -- JSON mit Details
    
    checked_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Tabelle: Verarbeitungsversuche (Retry-Tracking)
CREATE TABLE IF NOT EXISTS processing_attempts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_id INTEGER REFERENCES file_metadata(id),
    sha256 TEXT NOT NULL,
    
    attempt_number INTEGER NOT NULL,
    started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    completed_at DATETIME,
    
    success BOOLEAN,
    error_message TEXT,
    
    -- Was wurde versucht?
    processing_stage TEXT,               -- 'tika', 'ocr', 'llm', 'move'
    processing_params TEXT               -- JSON mit Parametern
);

-- Indizes
CREATE INDEX IF NOT EXISTS idx_quarantine_reason ON quarantine_log(quarantine_reason);
CREATE INDEX IF NOT EXISTS idx_quarantine_resolved ON quarantine_log(resolved_at);
CREATE INDEX IF NOT EXISTS idx_quality_check_name ON quality_checks(check_name);
CREATE INDEX IF NOT EXISTS idx_quality_passed ON quality_checks(check_passed);
CREATE INDEX IF NOT EXISTS idx_attempts_success ON processing_attempts(success);

-- View: Übersicht Quarantäne
CREATE VIEW IF NOT EXISTS v_quarantine_summary AS
SELECT 
    quarantine_reason,
    COUNT(*) as count,
    COUNT(CASE WHEN resolved_at IS NULL THEN 1 END) as pending,
    COUNT(CASE WHEN resolved_at IS NOT NULL THEN 1 END) as resolved
FROM quarantine_log
GROUP BY quarantine_reason
ORDER BY count DESC;

-- View: Ungelöste Quarantäne-Fälle
CREATE VIEW IF NOT EXISTS v_quarantine_pending AS
SELECT 
    ql.id,
    ql.quarantine_reason,
    ql.original_inbox_path,
    ql.quarantine_path,
    ql.error_message,
    ql.created_at,
    fm.original_filename,
    fm.content_type,
    fm.file_size_bytes
FROM quarantine_log ql
JOIN file_metadata fm ON ql.file_id = fm.id
WHERE ql.resolved_at IS NULL
ORDER BY ql.created_at ASC;

-- View: Qualitätsprüfungs-Statistiken
CREATE VIEW IF NOT EXISTS v_quality_stats AS
SELECT 
    check_name,
    COUNT(*) as total_checks,
    SUM(CASE WHEN check_passed THEN 1 ELSE 0 END) as passed,
    SUM(CASE WHEN NOT check_passed THEN 1 ELSE 0 END) as failed,
    ROUND(100.0 * SUM(CASE WHEN check_passed THEN 1 ELSE 0 END) / COUNT(*), 2) as pass_rate_percent,
    AVG(check_score) as avg_score
FROM quality_checks
GROUP BY check_name
ORDER BY pass_rate_percent ASC;

-- View: Dateien mit mehreren fehlgeschlagenen Versuchen
CREATE VIEW IF NOT EXISTS v_repeated_failures AS
SELECT 
    sha256,
    COUNT(*) as attempt_count,
    MAX(attempt_number) as max_attempts,
    GROUP_CONCAT(DISTINCT processing_stage) as failed_stages,
    GROUP_CONCAT(DISTINCT error_message, ' | ') as errors
FROM processing_attempts
WHERE success = FALSE
GROUP BY sha256
HAVING COUNT(*) >= 2
ORDER BY attempt_count DESC;

-- Trigger: Automatisch Quarantäne-Eintrag wenn Status = 'error'
CREATE TRIGGER IF NOT EXISTS auto_quarantine_on_error
AFTER UPDATE OF status ON file_metadata
WHEN NEW.status = 'error' AND OLD.status != 'error'
BEGIN
    INSERT INTO quarantine_log (
        file_id, 
        sha256, 
        quarantine_reason, 
        quarantine_path,
        original_inbox_path,
        error_message
    ) VALUES (
        NEW.id,
        NEW.sha256,
        'PROCESSING_ERROR',
        'F:/_Quarantine/_processing_error/' || NEW.original_filename,
        NEW.original_path,
        NEW.error_message
    );
END;

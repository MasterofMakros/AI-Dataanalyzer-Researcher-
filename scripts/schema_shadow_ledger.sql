-- F:\conductor\scripts\schema_shadow_ledger.sql
-- Shadow Ledger: Tracking aller Dateien im Neural Vault

-- Haupttabelle: Datei-Metadaten
CREATE TABLE IF NOT EXISTS file_metadata (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- Identifikation (unveränderlich)
    sha256 TEXT UNIQUE NOT NULL,
    file_size_bytes INTEGER NOT NULL,
    
    -- Original-Informationen (unveränderlich nach Ingest)
    original_path TEXT NOT NULL,
    original_filename TEXT NOT NULL,
    original_extension TEXT NOT NULL,
    
    -- Aktuelle Informationen (ändern sich bei Verschiebungen)
    current_path TEXT NOT NULL,
    current_filename TEXT NOT NULL,
    
    -- Klassifizierung durch KI
    category TEXT,                    -- z.B. "Finanzen"
    subcategory TEXT,                 -- z.B. "Rechnung"
    confidence REAL,                  -- 0.0 - 1.0 (KI-Konfidenz)
    classification_model TEXT,        -- z.B. "llama3:8b"
    
    -- ⭐ META-BESCHREIBUNG (1-2 Sätze: Worum geht es?)
    meta_description TEXT,            -- "Eine Bauhaus-Rechnung über 127€ für Gartenzubehör"
    tags TEXT,                        -- JSON Array: ["Bauhaus", "Garten", "Rechnung"]
    
    -- Extrahierte Entitäten (JSON)
    extracted_entities TEXT,          -- {"vendor": "Bauhaus", "amount": 45.00}
    
    -- Inhalts-Analyse
    content_type TEXT,                -- MIME Type (z.B. "application/pdf")
    extracted_text TEXT,              -- Volltext für lokale Suche
    language TEXT,                    -- Erkannte Sprache (z.B. "de")
    page_count INTEGER,               -- Anzahl Seiten (bei PDFs)
    
    -- ⭐ AUDIO/VIDEO: Transkript mit Zeitmarken (JSON)
    transcript_timestamped TEXT,      -- JSON Array: [{"start": 0, "end": 5, "text": "...", "speaker": "..."}]
    chapters TEXT,                    -- JSON Array: [{"start": 0, "end": 120, "title": "Intro"}]
    duration_seconds REAL,            -- Dauer in Sekunden
    
    -- Timestamps
    file_created_at DATETIME,         -- Ursprüngliches Erstelldatum der Datei
    file_modified_at DATETIME,        -- Ursprüngliches Änderungsdatum
    ingested_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    processed_at DATETIME,
    moved_at DATETIME,
    indexed_at DATETIME,
    
    -- Status & Workflow
    status TEXT DEFAULT 'pending',    
    -- Mögliche Status:
    -- pending     = Wartet auf Verarbeitung
    -- processing  = Wird gerade analysiert
    -- awaiting_confirmation = Wartet auf User-Bestätigung (Konfidenz < 80%)
    -- indexed     = Fertig verarbeitet und indexiert
    -- archived    = Manuell archiviert
    -- error       = Fehler bei Verarbeitung
    -- duplicate   = Als Duplikat erkannt
    
    error_message TEXT,
    requires_confirmation BOOLEAN DEFAULT FALSE,
    confirmed_by TEXT,                -- 'auto' oder 'user'
    confirmed_at DATETIME,
    
    -- Externe System-IDs
    qdrant_point_id TEXT,             -- Vector-ID in Qdrant
    meilisearch_doc_id TEXT,          -- ID in Meilisearch
    nextcloud_file_id INTEGER,        -- Nextcloud interne ID
    
    -- Audit & Performance
    processing_duration_ms INTEGER,
    processed_by TEXT DEFAULT 'n8n',
    processing_attempts INTEGER DEFAULT 0,
    
    -- Soft Delete
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at DATETIME
);

-- Indizes für schnelle Suche
CREATE INDEX IF NOT EXISTS idx_sha256 ON file_metadata(sha256);
CREATE INDEX IF NOT EXISTS idx_original_filename ON file_metadata(original_filename);
CREATE INDEX IF NOT EXISTS idx_current_path ON file_metadata(current_path);
CREATE INDEX IF NOT EXISTS idx_category ON file_metadata(category);
CREATE INDEX IF NOT EXISTS idx_status ON file_metadata(status);
CREATE INDEX IF NOT EXISTS idx_ingested_at ON file_metadata(ingested_at);
CREATE INDEX IF NOT EXISTS idx_content_type ON file_metadata(content_type);
CREATE INDEX IF NOT EXISTS idx_requires_confirmation ON file_metadata(requires_confirmation);

-- Volltextsuche auf extracted_text (SQLite FTS5)
CREATE VIRTUAL TABLE IF NOT EXISTS file_fulltext USING fts5(
    file_id,
    original_filename,
    current_filename,
    extracted_text,
    category,
    subcategory,
    content='file_metadata',
    content_rowid='id'
);

-- Trigger für automatische Volltextindex-Updates
CREATE TRIGGER IF NOT EXISTS file_metadata_ai AFTER INSERT ON file_metadata BEGIN
    INSERT INTO file_fulltext(rowid, file_id, original_filename, current_filename, extracted_text, category, subcategory)
    VALUES (new.id, new.id, new.original_filename, new.current_filename, new.extracted_text, new.category, new.subcategory);
END;

CREATE TRIGGER IF NOT EXISTS file_metadata_au AFTER UPDATE ON file_metadata BEGIN
    INSERT INTO file_fulltext(file_fulltext, rowid, file_id, original_filename, current_filename, extracted_text, category, subcategory)
    VALUES ('delete', old.id, old.id, old.original_filename, old.current_filename, old.extracted_text, old.category, old.subcategory);
    INSERT INTO file_fulltext(rowid, file_id, original_filename, current_filename, extracted_text, category, subcategory)
    VALUES (new.id, new.id, new.original_filename, new.current_filename, new.extracted_text, new.category, new.subcategory);
END;

-- Hilfstabelle: Kategorie-Mapping für Zielordner
CREATE TABLE IF NOT EXISTS category_folder_mapping (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT UNIQUE NOT NULL,
    target_folder_template TEXT NOT NULL,  -- z.B. "09 Datenpool Finanzen/{subcategory}/{year}"
    description TEXT
);

-- Standard-Mappings einfügen
INSERT OR IGNORE INTO category_folder_mapping (category, target_folder_template, description) VALUES
('Rechnung', '09 Datenpool Finanzen/Eingangsrechnungen/{year}', 'Eingehende Rechnungen'),
('Kontoauszug', '09 Datenpool Finanzen/Kontoauszüge/{year}/{month}', 'Bank-Kontoauszüge'),
('Vertrag', '08 Datenpool Rechtliches/Verträge/{year}', 'Rechtliche Verträge'),
('Foto', '07 Datenpool Persönlich/Fotos/{year}/{month}', 'Persönliche Fotos'),
('Screenshot', '07 Datenpool Persönlich/Screenshots/{year}', 'Screenshots'),
('Dokument', '10 Datenpool Wissen/Dokumente/{year}', 'Allgemeine Dokumente'),
('Video', '12 Datenpool Mediathek/Video/{year}', 'Video-Dateien'),
('Audio', '12 Datenpool Mediathek/Audio/{year}', 'Audio-Dateien'),
('Projekt', '09 Datenpool Projekte/{subcategory}', 'Projektbezogene Dateien'),
('Unsortiert', '99 Datenpool Archiv/Unsortiert/{year}/{month}', 'Nicht klassifizierbare Dateien');

-- View: Aktive Dateien (nicht gelöscht)
CREATE VIEW IF NOT EXISTS v_active_files AS
SELECT * FROM file_metadata 
WHERE is_deleted = FALSE 
ORDER BY ingested_at DESC;

-- View: Dateien die Bestätigung brauchen
CREATE VIEW IF NOT EXISTS v_awaiting_confirmation AS
SELECT 
    id,
    original_filename,
    category,
    subcategory,
    confidence,
    extracted_entities,
    ingested_at
FROM file_metadata 
WHERE status = 'awaiting_confirmation'
ORDER BY ingested_at ASC;

-- View: Dateibewegungen (Was wurde wohin verschoben?)
CREATE VIEW IF NOT EXISTS v_file_moves AS
SELECT 
    id,
    original_filename,
    current_filename,
    original_path,
    current_path,
    category,
    confidence,
    ingested_at,
    moved_at,
    CASE 
        WHEN original_filename = current_filename THEN 'Nicht umbenannt'
        ELSE 'Umbenannt'
    END as rename_status
FROM file_metadata
WHERE moved_at IS NOT NULL
  AND is_deleted = FALSE
ORDER BY moved_at DESC;

-- View: Statistiken pro Kategorie
CREATE VIEW IF NOT EXISTS v_category_stats AS
SELECT 
    category,
    COUNT(*) as file_count,
    SUM(file_size_bytes) / 1024 / 1024 as total_size_mb,
    AVG(confidence) as avg_confidence,
    MIN(ingested_at) as first_ingested,
    MAX(ingested_at) as last_ingested
FROM file_metadata
WHERE is_deleted = FALSE
GROUP BY category
ORDER BY file_count DESC;

-- View: Fehlerhafte Dateien
CREATE VIEW IF NOT EXISTS v_errors AS
SELECT 
    id,
    original_filename,
    original_path,
    status,
    error_message,
    processing_attempts,
    ingested_at
FROM file_metadata
WHERE status = 'error'
ORDER BY ingested_at DESC;

-- View: Duplikate
CREATE VIEW IF NOT EXISTS v_duplicates AS
SELECT 
    sha256,
    COUNT(*) as duplicate_count,
    GROUP_CONCAT(original_filename, ' | ') as filenames,
    GROUP_CONCAT(original_path, ' | ') as paths
FROM file_metadata
WHERE is_deleted = FALSE
GROUP BY sha256
HAVING COUNT(*) > 1;

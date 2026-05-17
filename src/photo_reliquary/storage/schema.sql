PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS photos (
    photo_id TEXT PRIMARY KEY,
    current_path TEXT NOT NULL,
    checksum TEXT NOT NULL,
    checksum_algorithm TEXT NOT NULL,
    checksum_tail TEXT NOT NULL,
    size_bytes INTEGER NOT NULL,
    mtime_ns INTEGER NOT NULL,
    first_seen_at TEXT NOT NULL,
    last_seen_at TEXT NOT NULL,
    missing_since TEXT,
    identity_storage_mode TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_photos_checksum ON photos (checksum);
CREATE INDEX IF NOT EXISTS idx_photos_missing_since ON photos (missing_since);

CREATE TABLE IF NOT EXISTS tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS photo_tags (
    photo_id TEXT NOT NULL,
    tag_id INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    PRIMARY KEY (photo_id, tag_id),
    FOREIGN KEY (photo_id) REFERENCES photos(photo_id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS analysis_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    plugin_name TEXT NOT NULL,
    plugin_version TEXT NOT NULL,
    model_name TEXT,
    model_version TEXT,
    target_path TEXT NOT NULL,
    started_at TEXT NOT NULL,
    completed_at TEXT
);

CREATE TABLE IF NOT EXISTS annotations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL,
    photo_id TEXT NOT NULL,
    namespace TEXT NOT NULL,
    label TEXT NOT NULL,
    confidence REAL,
    value_text TEXT,
    region_json TEXT,
    plugin_name TEXT NOT NULL,
    plugin_version TEXT NOT NULL,
    model_name TEXT,
    model_version TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (run_id) REFERENCES analysis_runs(id) ON DELETE CASCADE,
    FOREIGN KEY (photo_id) REFERENCES photos(photo_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_annotations_photo ON annotations (photo_id);
CREATE INDEX IF NOT EXISTS idx_annotations_namespace_label ON annotations (namespace, label);

CREATE TABLE IF NOT EXISTS scan_issues (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    issue_type TEXT NOT NULL,
    photo_id TEXT,
    related_photo_id TEXT,
    checksum TEXT,
    path TEXT,
    details_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_scan_issues_type ON scan_issues (issue_type);

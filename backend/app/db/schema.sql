CREATE TABLE IF NOT EXISTS stories (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY,
    role TEXT NOT NULL CHECK (role IN ('draft_script', 'story_note')),
    source_path TEXT NOT NULL,
    filename TEXT NOT NULL,
    source_type TEXT NOT NULL CHECK (source_type IN ('docx', 'pdf', 'txt', 'md')),
    content_hash TEXT NOT NULL,
    ingested_at TEXT NOT NULL,
    page_count INTEGER,
    story_position INTEGER,
    story_id INTEGER REFERENCES stories(id)
);

CREATE TABLE IF NOT EXISTS segments (
    id INTEGER PRIMARY KEY,
    document_id INTEGER NOT NULL REFERENCES documents(id),
    sequence_index INTEGER NOT NULL,
    page_number INTEGER,
    paragraph_index INTEGER,
    text TEXT NOT NULL,
    char_start INTEGER,
    char_end INTEGER
);

CREATE INDEX IF NOT EXISTS idx_segments_document_sequence
    ON segments(document_id, sequence_index);

CREATE TABLE IF NOT EXISTS segment_styles (
    id INTEGER PRIMARY KEY,
    segment_id INTEGER NOT NULL REFERENCES segments(id),
    style_kind TEXT NOT NULL CHECK (
        style_kind IN ('bold', 'italic', 'underline', 'highlight', 'font_color', 'comment', 'heading', 'semantic')
    ),
    style_value TEXT
);

CREATE INDEX IF NOT EXISTS idx_segment_styles_segment
    ON segment_styles(segment_id);

CREATE TABLE IF NOT EXISTS themes (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    summary TEXT NOT NULL,
    is_main INTEGER NOT NULL DEFAULT 0,
    excluded INTEGER NOT NULL DEFAULT 0,
    story_id INTEGER REFERENCES stories(id),
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS topics (
    id INTEGER PRIMARY KEY,
    document_id INTEGER NOT NULL REFERENCES documents(id),
    theme_id INTEGER NOT NULL REFERENCES themes(id),
    act TEXT CHECK (act IN ('opening', 'conflict', 'climax')),
    sequence_index INTEGER NOT NULL,
    title TEXT NOT NULL,
    summary TEXT NOT NULL,
    segment_start_id INTEGER REFERENCES segments(id),
    segment_end_id INTEGER REFERENCES segments(id),
    excluded INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_topics_document_sequence
    ON topics(document_id, sequence_index);

CREATE TABLE IF NOT EXISTS subplots (
    id INTEGER PRIMARY KEY,
    theme_id INTEGER NOT NULL REFERENCES themes(id),
    resolved INTEGER NOT NULL DEFAULT 0,
    resolved_at_position INTEGER,
    created_at TEXT NOT NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_subplots_theme_id
    ON subplots(theme_id);

CREATE TABLE IF NOT EXISTS encoding_rules (
    id INTEGER PRIMARY KEY,
    style_kind TEXT NOT NULL,
    block_length TEXT NOT NULL CHECK (block_length IN ('single', 'multi')),
    position TEXT NOT NULL CHECK (position IN ('chapter_start', 'anywhere')),
    label TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL
);

-- A row's mere presence means the rule is disabled for that document.
-- Absence means enabled - the default for every existing document/rule.
CREATE TABLE IF NOT EXISTS document_encoding_rule_exclusions (
    document_id INTEGER NOT NULL REFERENCES documents(id),
    encoding_rule_id INTEGER NOT NULL REFERENCES encoding_rules(id),
    PRIMARY KEY (document_id, encoding_rule_id)
);

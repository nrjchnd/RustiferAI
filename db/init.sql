CREATE TABLE repositories (
    id SERIAL PRIMARY KEY,
    source_repo TEXT NOT NULL,
    source_branch TEXT NOT NULL,
    source_auth TEXT,
    dest_repo TEXT NOT NULL,
    dest_branch TEXT NOT NULL,
    dest_auth TEXT
);

CREATE TABLE fileindex (
    id SERIAL PRIMARY KEY,
    file_path TEXT UNIQUE NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    last_modified TIMESTAMP,
    size INTEGER
);

CREATE TABLE translationstatus (
    file_id INTEGER PRIMARY KEY REFERENCES fileindex(id),
    translated BOOLEAN DEFAULT FALSE,
    compiled BOOLEAN DEFAULT FALSE,
    error_message TEXT
);

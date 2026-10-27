PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS account (
    account_id INTEGER PRIMARY KEY AUTOINCREMENT,
    google_account_id TEXT UNIQUE NOT NULL,
    display_name TEXT NOT NULL,
    email TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS media (
    media_id INTEGER PRIMARY KEY AUTOINCREMENT,
    type TEXT NOT NULL,                             
    title TEXT NOT NULL,
    filter TEXT,                                    
    publication_date TEXT,                          
    file_path TEXT,                                 
    author_id INTEGER,                              
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (author_id) REFERENCES account(account_id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS constant (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,                          
    description TEXT
);

CREATE INDEX IF NOT EXISTS idx_media_author_id ON media(author_id);
CREATE INDEX IF NOT EXISTS idx_media_type ON media(type);
CREATE INDEX IF NOT EXISTS idx_media_filter ON media(filter);
CREATE INDEX IF NOT EXISTS idx_account_google_id ON account(google_account_id);

CREATE VIEW IF NOT EXISTS v_media AS
SELECT 
    m.media_id,
    m.type,
    m.title,
    m.filter,
    m.publication_date,
    m.file_path,
    m.author_id,
    m.created_at,
    a.display_name AS author_name,
    a.email AS author_email
FROM media m
LEFT JOIN account a ON m.author_id = a.account_id;

-- Account view with list of contributed media IDs and count
CREATE VIEW IF NOT EXISTS v_account_contributions AS
SELECT 
    a.account_id,
    a.google_account_id,
    a.display_name,
    a.email,
    a.created_at,
    GROUP_CONCAT(m.media_id, ', ') AS contributed_media_ids,
    COUNT(m.media_id) AS total_contributions
FROM account a
LEFT JOIN media m ON a.account_id = m.author_id
GROUP BY a.account_id;

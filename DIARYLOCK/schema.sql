CREATE TABLE IF NOT EXISTS settings (
    setting_key TEXT PRIMARY KEY,
    setting_value TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS diary_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    encrypted_payload TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY(username) REFERENCES users(username)
);
CREATE TABLE IF NOT EXISTS blockchain_blocks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    block_index INTEGER NOT NULL UNIQUE,
    timestamp TEXT NOT NULL,
    username TEXT NOT NULL,
    asset_type TEXT NOT NULL,
    asset_id INTEGER,
    asset_name TEXT NOT NULL,
    asset_hash TEXT NOT NULL,
    previous_hash TEXT NOT NULL,
    block_hash TEXT NOT NULL UNIQUE
);

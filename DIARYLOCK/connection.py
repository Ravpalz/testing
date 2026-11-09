"""Lapisan database SQLite DIARYLOCK.

Strukturnya mengikuti pola connection.py pada project acuan, tetapi memakai
SQLite lokal sehingga tidak memerlukan server database eksternal.
"""
from pathlib import Path
import sqlite3
from datetime import datetime, timezone
from typing import Any, Iterable

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "diarylock.db"


def create_connection() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=15)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def initialize_database() -> None:
    conn = create_connection()
    try:
        conn.executescript(
            """
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
            """
        )
        conn.commit()
    finally:
        conn.close()


def run_query(query: str, params: Iterable[Any] | None = None, fetch: bool = True):
    """Helper SQL bergaya project acuan; selalu gunakan parameter query."""
    conn = create_connection()
    try:
        cursor = conn.execute(query, tuple(params or ()))
        if fetch:
            return cursor.fetchall()
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def get_setting(key: str) -> str | None:
    rows = run_query("SELECT setting_value FROM settings WHERE setting_key = ?", (key,))
    return rows[0]["setting_value"] if rows else None


def set_setting(key: str, value: str) -> None:
    run_query(
        "INSERT INTO settings(setting_key, setting_value) VALUES(?, ?) "
        "ON CONFLICT(setting_key) DO UPDATE SET setting_value = excluded.setting_value",
        (key, value),
        fetch=False,
    )


def get_user(username: str):
    rows = run_query(
        "SELECT id, username, password_hash, created_at FROM users WHERE username = ?",
        (username,),
    )
    return rows[0] if rows else None


def create_user(username: str, password_hash: str) -> int:
    return run_query(
        "INSERT INTO users(username, password_hash, created_at) VALUES(?, ?, ?)",
        (username, password_hash, datetime.now(timezone.utc).isoformat()),
        fetch=False,
    )


def insert_diary_entry(username: str, encrypted_payload: str) -> int:
    return run_query(
        "INSERT INTO diary_entries(username, encrypted_payload, created_at) VALUES(?, ?, ?)",
        (username, encrypted_payload, datetime.now(timezone.utc).isoformat()),
        fetch=False,
    )


def get_diary_entries(username: str):
    return run_query(
        "SELECT id, created_at FROM diary_entries WHERE username = ? ORDER BY id DESC",
        (username,),
    )


def get_diary_entry(entry_id: int, username: str):
    rows = run_query(
        "SELECT id, username, encrypted_payload, created_at "
        "FROM diary_entries WHERE id = ? AND username = ?",
        (entry_id, username),
    )
    return rows[0] if rows else None


def get_all_blocks():
    return run_query("SELECT * FROM blockchain_blocks ORDER BY block_index ASC")


def get_latest_block():
    rows = run_query("SELECT * FROM blockchain_blocks ORDER BY block_index DESC LIMIT 1")
    return rows[0] if rows else None


def insert_block(block: dict) -> int:
    return run_query(
        """INSERT INTO blockchain_blocks
        (block_index, timestamp, username, asset_type, asset_id, asset_name,
         asset_hash, previous_hash, block_hash)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            block["block_index"], block["timestamp"], block["username"],
            block["asset_type"], block.get("asset_id"), block["asset_name"],
            block["asset_hash"], block["previous_hash"], block["block_hash"],
        ),
        fetch=False,
    )

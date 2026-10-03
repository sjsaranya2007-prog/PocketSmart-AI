import sqlite3
import hashlib
import os
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "pocketsmart.db"


def connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = connect()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            planner TEXT NOT NULL,
            request_json TEXT NOT NULL,
            result_json TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)
    conn.commit()
    conn.close()


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    key = hashlib.pbkdf2_hmac(
        "sha256", password.encode(), salt, 120000
    )
    return salt.hex() + ":" + key.hex()


def verify_password(password: str, stored: str) -> bool:
    try:
        salt_hex, key_hex = stored.split(":")
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(key_hex)
        actual = hashlib.pbkdf2_hmac(
            "sha256", password.encode(), salt, 120000
        )
        return actual == expected
    except Exception:
        return False


def create_user(name: str, email: str, password: str):
    conn = connect()
    try:
        cur = conn.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            (name, email, hash_password(password))
        )
        conn.commit()
        return cur.lastrowid
    except sqlite3.IntegrityError:
        return None
    finally:
        conn.close()


def verify_user(email: str, password: str):
    conn = connect()
    row = conn.execute(
        "SELECT * FROM users WHERE email = ?", (email,)
    ).fetchone()
    conn.close()

    if row and verify_password(password, row["password_hash"]):
        return dict(row)
    return None


def get_user(user_id: int):
    conn = connect()
    row = conn.execute(
        "SELECT id, name, email, created_at FROM users WHERE id = ?",
        (user_id,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def save_history(user_id: int, planner: str, request_json: str, result_json: str):
    conn = connect()
    conn.execute(
        """INSERT INTO history (user_id, planner, request_json, result_json)
           VALUES (?, ?, ?, ?)""",
        (user_id, planner, request_json, result_json)
    )
    conn.commit()
    conn.close()


def get_history(user_id: int, limit: int = 50):
    conn = connect()
    rows = conn.execute(
        """SELECT id, planner, request_json, result_json, created_at
           FROM history WHERE user_id = ?
           ORDER BY id DESC LIMIT ?""",
        (user_id, limit)
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]

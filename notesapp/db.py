"""Tiny DB layer that works on SQLite (tests/local) and PostgreSQL (real deployments)."""
import sqlite3

from flask import current_app, g


def _url():
    return current_app.config["DATABASE_URL"]


def _is_sqlite():
    return _url().startswith("sqlite")


def get_db():
    if "db" not in g:
        url = _url()
        if _is_sqlite():
            conn = sqlite3.connect(url.replace("sqlite:///", "", 1))
            conn.row_factory = sqlite3.Row
        else:
            import psycopg2
            import psycopg2.extras

            conn = psycopg2.connect(url, cursor_factory=psycopg2.extras.RealDictCursor)
        g.db = conn
    return g.db


def close_db(_exc=None):
    conn = g.pop("db", None)
    if conn is not None:
        conn.close()


def _run(cur, sql, params):
    if _is_sqlite():
        cur.execute(sql, params or ())
    else:
        # psycopg2 uses %s placeholders; only convert when we actually have params
        cur.execute(sql.replace("?", "%s") if params else sql, params or None)


def query(sql, params=(), one=False):
    cur = get_db().cursor()
    _run(cur, sql, params)
    rows = [dict(r) for r in cur.fetchall()]
    cur.close()
    if one:
        return rows[0] if rows else None
    return rows


def execute(sql, params=()):
    conn = get_db()
    cur = conn.cursor()
    _run(cur, sql, params)
    rowcount = cur.rowcount
    conn.commit()
    cur.close()
    return rowcount


def insert(sql, params=()):
    """Run an INSERT and return the new row id."""
    conn = get_db()
    cur = conn.cursor()
    _run(cur, sql + " RETURNING id", params)
    new_id = cur.fetchone()["id"]
    conn.commit()
    cur.close()
    return new_id


def init_db():
    pk = "INTEGER PRIMARY KEY AUTOINCREMENT" if _is_sqlite() else "SERIAL PRIMARY KEY"
    execute(
        f"CREATE TABLE IF NOT EXISTS users ("
        f"id {pk}, username TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL)"
    )
    execute(
        f"CREATE TABLE IF NOT EXISTS notes ("
        f"id {pk}, owner_id INTEGER NOT NULL REFERENCES users(id), "
        f"title TEXT NOT NULL, body TEXT NOT NULL, checksum TEXT NOT NULL, "
        f"created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"
    )

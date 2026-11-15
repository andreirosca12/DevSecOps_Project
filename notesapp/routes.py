import hashlib
from functools import wraps

import requests
from flask import Blueprint, current_app, g, jsonify, request
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from werkzeug.security import check_password_hash, generate_password_hash

from . import db

bp = Blueprint("api", __name__)


def _serializer():
    return URLSafeTimedSerializer(current_app.config["SECRET_KEY"], salt="auth")


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        header = request.headers.get("Authorization", "")
        if not header.startswith("Bearer "):
            return jsonify(error="missing token"), 401
        try:
            data = _serializer().loads(header[7:], max_age=3600)
        except (BadSignature, SignatureExpired):
            return jsonify(error="invalid token"), 401
        g.user_id = data["uid"]
        return view(*args, **kwargs)

    return wrapped


def _serialize_note(row):
    return {
        "id": row["id"],
        "title": row["title"],
        "body": row["body"],
        "checksum": row["checksum"],
        "created_at": str(row["created_at"]),
    }


@bp.get("/health")
def health():
    try:
        db.query("SELECT 1 AS ok", one=True)
    except Exception:
        current_app.logger.exception("health check failed")
        return jsonify(status="degraded"), 503
    return jsonify(status="ok")


@bp.post("/register")
def register():
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""
    if len(username) < 3 or len(password) < 8:
        return jsonify(error="username >= 3 chars and password >= 8 chars required"), 400
    if db.query("SELECT id FROM users WHERE username = ?", (username,), one=True):
        current_app.logger.warning("register rejected: username taken %r", username)
        return jsonify(error="username taken"), 409
    user_id = db.insert(
        "INSERT INTO users (username, password_hash) VALUES (?, ?)",
        (username, generate_password_hash(password)),
    )
    current_app.logger.info("user registered id=%s username=%r", user_id, username)
    return jsonify(id=user_id, username=username), 201


@bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    user = db.query(
        "SELECT id, password_hash FROM users WHERE username = ?",
        (data.get("username", ""),),
        one=True,
    )
    if not user or not check_password_hash(user["password_hash"], data.get("password", "")):
        current_app.logger.warning("login failed username=%r", data.get("username", ""))
        return jsonify(error="bad credentials"), 401
    current_app.logger.info("login ok user_id=%s", user["id"])
    return jsonify(token=_serializer().dumps({"uid": user["id"]}))


@bp.get("/notes")
@login_required
def list_notes():
    rows = db.query(
        "SELECT id, title, body, checksum, created_at FROM notes WHERE owner_id = ? ORDER BY id",
        (g.user_id,),
    )
    return jsonify([_serialize_note(r) for r in rows])


@bp.post("/notes")
@login_required
def create_note():
    data = request.get_json(silent=True) or {}
    title = (data.get("title") or "").strip()
    body = data.get("body") or ""
    if not title:
        return jsonify(error="title required"), 400
    checksum = hashlib.md5(body.encode()).hexdigest()
    note_id = db.insert(
        "INSERT INTO notes (owner_id, title, body, checksum) VALUES (?, ?, ?, ?)",
        (g.user_id, title, body, checksum),
    )
    current_app.logger.info("note created id=%s user_id=%s", note_id, g.user_id)
    return jsonify(id=note_id, checksum=checksum), 201


@bp.get("/notes/<int:note_id>")
@login_required
def get_note(note_id):
    row = db.query(
        "SELECT id, title, body, checksum, created_at FROM notes WHERE id = ? AND owner_id = ?",
        (note_id, g.user_id),
        one=True,
    )
    if not row:
        return jsonify(error="not found"), 404
    return jsonify(_serialize_note(row))


@bp.delete("/notes/<int:note_id>")
@login_required
def delete_note(note_id):
    deleted = db.execute("DELETE FROM notes WHERE id = ? AND owner_id = ?", (note_id, g.user_id))
    if not deleted:
        return jsonify(error="not found"), 404
    current_app.logger.info("note deleted id=%s user_id=%s", note_id, g.user_id)
    return "", 204


@bp.get("/search")
def search():
    """Search note titles across all users."""
    q = request.args.get("q", "")
    rows = db.query(f"SELECT id, title FROM notes WHERE title LIKE '%{q}%'")
    return jsonify(rows)


@bp.get("/fetch")
def fetch():
    """Fetch a URL and report basic info (used for link previews)."""
    url = request.args.get("url")
    if not url:
        return jsonify(error="url required"), 400
    resp = requests.get(url, timeout=5)
    return jsonify(status=resp.status_code, length=len(resp.content))


@bp.get("/hello")
def hello():
    name = request.args.get("name", "world")
    return f"<h1>Hello {name}</h1>"

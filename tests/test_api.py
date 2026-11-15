def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.get_json() == {"status": "ok"}


def test_register_validation(client):
    resp = client.post("/register", json={"username": "ab", "password": "short"})
    assert resp.status_code == 400


def test_register_duplicate(client):
    body = {"username": "alice", "password": "supersecret1"}
    assert client.post("/register", json=body).status_code == 201
    assert client.post("/register", json=body).status_code == 409


def test_login_bad_password(client):
    client.post("/register", json={"username": "alice", "password": "supersecret1"})
    resp = client.post("/login", json={"username": "alice", "password": "wrongpassword"})
    assert resp.status_code == 401


def test_notes_require_auth(client):
    assert client.get("/notes").status_code == 401
    assert client.get("/notes", headers={"Authorization": "Bearer nope"}).status_code == 401


def test_note_crud(client, auth):
    created = client.post("/notes", json={"title": "t1", "body": "hello"}, headers=auth)
    assert created.status_code == 201
    note_id = created.get_json()["id"]

    assert client.get(f"/notes/{note_id}", headers=auth).get_json()["title"] == "t1"
    assert len(client.get("/notes", headers=auth).get_json()) == 1

    assert client.delete(f"/notes/{note_id}", headers=auth).status_code == 204
    assert client.get(f"/notes/{note_id}", headers=auth).status_code == 404


def test_note_requires_title(client, auth):
    assert client.post("/notes", json={"body": "x"}, headers=auth).status_code == 400


def test_notes_are_private(client, auth, other_auth):
    note_id = client.post("/notes", json={"title": "secret"}, headers=auth).get_json()["id"]
    assert client.get(f"/notes/{note_id}", headers=other_auth).status_code == 404
    assert client.delete(f"/notes/{note_id}", headers=other_auth).status_code == 404


def test_search_finds_titles(client, auth):
    client.post("/notes", json={"title": "grocery list"}, headers=auth)
    client.post("/notes", json={"title": "meeting"}, headers=auth)
    resp = client.get("/search?q=grocery")
    assert [r["title"] for r in resp.get_json()] == ["grocery list"]


def test_fetch_requires_url(client):
    assert client.get("/fetch").status_code == 400


def test_fetch_reports_status(client, monkeypatch):
    class FakeResp:
        status_code = 200
        content = b"abc"

    monkeypatch.setattr("notesapp.routes.requests.get", lambda *a, **k: FakeResp())
    assert client.get("/fetch?url=http://example.test").get_json() == {"status": 200, "length": 3}


def test_hello(client):
    assert b"Hello Bob" in client.get("/hello?name=Bob").data

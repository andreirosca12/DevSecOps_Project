import pytest

from notesapp import create_app

#AWS_SECRET_ACCESS_KEY=AKIAIOSFODNN7EXAMPLE

@pytest.fixture
def app(tmp_path):
    return create_app(
        {"TESTING": True, "DATABASE_URL": f"sqlite:///{tmp_path / 'test.db'}"}
    )


@pytest.fixture
def client(app):
    return app.test_client()


def _register_and_login(client, username):
    client.post("/register", json={"username": username, "password": "supersecret1"})
    token = client.post(
        "/login", json={"username": username, "password": "supersecret1"}
    ).get_json()["token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def auth(client):
    return _register_and_login(client, "alice")


@pytest.fixture
def other_auth(client):
    return _register_and_login(client, "bob")

from datetime import datetime as dt, timezone
from types import SimpleNamespace
from uuid import uuid4
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.database import get_db
from app.auth.dependencies import get_current_active_user
from app.models.calculation import Calculation
from app.models.user import User


@pytest.fixture
def client(db_session):
    # In-process deps so requests exercise app.main directly
    def override_db():
        yield db_session

    def override_user():
        return SimpleNamespace(
            id=uuid4(),
            username="tester",
            is_active=True,
            is_verified=True,
        )

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_active_user] = override_user
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def test_health_and_web_routes(client):
    assert client.get("/health").json() == {"status": "ok"}
    for path in ["/", "/login", "/register", "/dashboard"]:
        r = client.get(path)
        assert r.status_code == 200
        assert "text/html" in r.headers["content-type"]


def test_login_json_422_validation(client):
    # Intentionally invalid to cover 422 path
    r = client.post("/auth/login", json={"username": "x", "password": "pw"})
    assert r.status_code == 422


def test_login_json_401_branch(client, monkeypatch):
    # Valid payload that passes schema, but auth fails -> 401
    monkeypatch.setattr(User, "authenticate", staticmethod(lambda db, u, p: None))
    payload = {"username": "notarealuser", "password": "ValidPass123!"}
    r = client.post("/auth/login", json=payload)
    assert r.status_code == 401
    assert r.json()["detail"] == "Invalid username or password"


def test_login_json_success_makes_expires_aware(client, monkeypatch):
    # Return naive expires_at to trigger TZ-fix branch
    naive = dt.utcnow()
    user = SimpleNamespace(
        id=uuid4(),
        username="testeruser",
        email="t@example.com",
        first_name="T",
        last_name="User",
        is_active=True,
        is_verified=True,
    )

    def fake_auth(_db, _u, _p):
        return {
            "access_token": "at",
            "refresh_token": "rt",
            "expires_at": naive,  # naive on purpose
            "user": user,
        }

    monkeypatch.setattr(User, "authenticate", staticmethod(fake_auth))
    payload = {"username": "testeruser", "password": "ValidPass123!"}
    r = client.post("/auth/login", json=payload)
    assert r.status_code == 200, r.json()

    body = r.json()
    ts = body["expires_at"].replace("Z", "+00:00")
    assert dt.fromisoformat(ts).tzinfo is not None


def test_login_form_endpoint(client, monkeypatch):
    user = SimpleNamespace(
        id=uuid4(),
        username="formuser",
        email="f@example.com",
        first_name="F",
        last_name="U",
        is_active=True,
        is_verified=True,
    )

    def fake_auth(db, u, p):
        return {
            "access_token": "formtoken",
            "refresh_token": "rt",
            "expires_at": dt.now(timezone.utc),
            "user": user,
        }

    monkeypatch.setattr(User, "authenticate", staticmethod(fake_auth))

    r = client.post("/auth/token", data={"username": "formuser", "password": "ValidPass123!"})
    assert r.status_code == 200
    assert r.json()["access_token"] == "formtoken"


def test_calc_create_valueerror_path(client, monkeypatch):
    # Force ValueError so the except branch returns 400
    def raise_value_error(**kwargs):
        raise ValueError("Bad inputs")

    monkeypatch.setattr(Calculation, "create", staticmethod(lambda **kw: raise_value_error()))
    r = client.post("/calculations", json={"type": "addition", "inputs": [1, 2]})
    assert r.status_code == 400
    assert r.json()["detail"] == "Bad inputs"


def test_get_invalid_uuid_400(client):
    r = client.get("/calculations/not-a-uuid")
    assert r.status_code == 400
    assert r.json()["detail"] == "Invalid calculation id format."


def test_get_not_found_404(client):
    r = client.get(f"/calculations/{uuid4()}")
    assert r.status_code == 404
    assert r.json()["detail"] == "Calculation not found."

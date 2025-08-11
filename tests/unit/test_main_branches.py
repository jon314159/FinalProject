from datetime import datetime as dt, timezone
from types import SimpleNamespace
from uuid import uuid4
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.database import get_db
from app.auth.dependencies import get_current_active_user
from app.models.user import User


# ---------------- helpers ----------------

def make_client(override_db, user=None):
    if user is None:
        user = SimpleNamespace(id=uuid4(), username="tester", is_active=True, is_verified=True)

    def override_user():
        return user

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_active_user] = override_user
    client = TestClient(app)
    return client, user


def create_user_in_db(db_session):
    payload = {
        "first_name": "T",
        "last_name": "User",
        "email": f"t{uuid4().hex}@example.com",
        "username": f"user_{uuid4().hex[:12]}",
        "password": "ValidPass123!",
    }
    u = User.register(db_session, payload)
    db_session.commit()
    db_session.refresh(u)
    return u


# ---------------- web routes ----------------

def test_web_view_and_edit_pages_render(db_session):
    def override_db():
        yield db_session

    client, _ = make_client(override_db)
    try:
        assert client.get("/dashboard/view/abc123").status_code == 200
        assert client.get("/dashboard/edit/abc123").status_code == 200
    finally:
        app.dependency_overrides.clear()
        client.close()


# ---------------- register (covers 187-195) ----------------

def test_register_success_inprocess(db_session):
    def override_db():
        yield db_session

    client, _ = make_client(override_db)
    try:
        payload = {
            "first_name": "Alice",
            "last_name": "Smith",
            "email": f"alice{uuid4().hex[:6]}@example.com",
            "username": f"alicesmith_{uuid4().hex[:6]}",
            "password": "ValidPass123!",
            "confirm_password": "ValidPass123!",
        }
        r = client.post("/auth/register", json=payload)
        assert r.status_code == 201, r.text
        data = r.json()
        assert data["username"].startswith("alicesmith_")
        assert data["email"].startswith("alice")
    finally:
        app.dependency_overrides.clear()
        client.close()


def test_register_valueerror_returns_400(monkeypatch, db_session):
    # Force error path inside the try/except
    from app.models.user import User as UserModel
    monkeypatch.setattr(UserModel, "register", staticmethod(lambda db, data: (_ for _ in ()).throw(ValueError("duplicate"))))

    def override_db():
        yield db_session

    client, _ = make_client(override_db)
    try:
        payload = {
            "first_name": "Bob",
            "last_name": "Jones",
            "email": "dup@example.com",
            "username": "dupuser",
            "password": "ValidPass123!",
            "confirm_password": "ValidPass123!",
        }
        r = client.post("/auth/register", json=payload)
        assert r.status_code == 400
        assert r.json()["detail"] == "duplicate"
    finally:
        app.dependency_overrides.clear()
        client.close()


# ---------------- auth branches ----------------

def test_login_json_sets_default_expiry_when_missing(monkeypatch, db_session):
    from app.models.user import User as UserModel

    def fake_auth(_db, _u, _p):
        user = SimpleNamespace(
            id=uuid4(), username="testeruser", email="t@example.com",
            first_name="T", last_name="User", is_active=True, is_verified=True
        )
        # No expires_at, triggers default branch
        return {"access_token": "at", "refresh_token": "rt", "user": user}

    monkeypatch.setattr(UserModel, "authenticate", staticmethod(fake_auth))

    def override_db():
        yield db_session

    client, _ = make_client(override_db)
    try:
        r = client.post("/auth/login", json={"username": "testeruser", "password": "ValidPass123!"})
        assert r.status_code == 200, r.json()
        assert "expires_at" in r.json()
    finally:
        app.dependency_overrides.clear()
        client.close()


def test_login_form_401_branch(monkeypatch, db_session):
    from app.models.user import User as UserModel
    monkeypatch.setattr(UserModel, "authenticate", staticmethod(lambda db, u, p: None))

    def override_db():
        yield db_session

    client, _ = make_client(override_db)
    try:
        r = client.post("/auth/token", data={"username": "formuser", "password": "ValidPass123!"})
        assert r.status_code == 401
        assert r.json()["detail"] == "Invalid username or password"
    finally:
        app.dependency_overrides.clear()
        client.close()


def test_login_form_success_branch(monkeypatch, db_session):
    from app.models.user import User as UserModel

    def fake_auth(_db, u, p):
        user = SimpleNamespace(
            id=uuid4(), username=u, email="f@example.com",
            first_name="F", last_name="U", is_active=True, is_verified=True
        )
        return {"access_token": "formtoken", "refresh_token": "rt", "expires_at": dt.now(timezone.utc), "user": user}

    monkeypatch.setattr(UserModel, "authenticate", staticmethod(fake_auth))

    def override_db():
        yield db_session

    client, _ = make_client(override_db)
    try:
        r = client.post("/auth/token", data={"username": "formuser", "password": "ValidPass123!"})
        assert r.status_code == 200
        assert r.json()["access_token"] == "formtoken"
    finally:
        app.dependency_overrides.clear()
        client.close()


# ---------------- CRUD via real DB ----------------

def test_create_calculation_success(db_session):
    user = create_user_in_db(db_session)

    def override_db():
        yield db_session

    client, _ = make_client(override_db, user=user)
    try:
        r = client.post("/calculations", json={"type": "addition", "inputs": [1, 2, 3]})
        assert r.status_code == 201, r.text
        data = r.json()
        assert data["type"] == "addition"
        assert data["inputs"] == [1.0, 2.0, 3.0]
        assert data["result"] == 6.0
    finally:
        app.dependency_overrides.clear()
        client.close()


def test_list_calculations_nonempty(db_session):
    user = create_user_in_db(db_session)

    def override_db():
        yield db_session

    client, _ = make_client(override_db, user=user)
    try:
        created = client.post("/calculations", json={"type": "addition", "inputs": [5, 6]}).json()
        r = client.get("/calculations")
        assert r.status_code == 200
        ids = [c["id"] for c in r.json()]
        assert created["id"] in ids
    finally:
        app.dependency_overrides.clear()
        client.close()


def test_get_calculation_success(db_session):
    user = create_user_in_db(db_session)

    def override_db():
        yield db_session

    client, _ = make_client(override_db, user=user)
    try:
        created = client.post("/calculations", json={"type": "multiplication", "inputs": [2, 3]}).json()
        r = client.get(f"/calculations/{created['id']}")
        assert r.status_code == 200
        assert r.json()["id"] == created["id"]
    finally:
        app.dependency_overrides.clear()
        client.close()


def test_update_calculation_success_inputs_changed(db_session):
    # Covers the branch where inputs is provided (the two assignment lines)
    user = create_user_in_db(db_session)

    def override_db():
        yield db_session

    client, _ = make_client(override_db, user=user)
    try:
        created = client.post("/calculations", json={"type": "multiplication", "inputs": [2, 3]}).json()
        cid = created["id"]
        r = client.put(f"/calculations/{cid}", json={"inputs": [5, 6]})
        assert r.status_code == 200, r.text
        assert r.json()["result"] == 30  # 5 * 6
    finally:
        app.dependency_overrides.clear()
        client.close()


def test_update_calculation_no_inputs_branch(db_session):
    # Covers the path where inputs is None (skip the two assignment lines)
    user = create_user_in_db(db_session)

    def override_db():
        yield db_session

    client, _ = make_client(override_db, user=user)
    try:
        created = client.post("/calculations", json={"type": "addition", "inputs": [1, 2]}).json()
        cid = created["id"]
        # Send empty body -> inputs remains None in schema
        r = client.put(f"/calculations/{cid}", json={})
        assert r.status_code == 200
        # Result should remain the original sum 3.0
        assert r.json()["result"] == 3.0
    finally:
        app.dependency_overrides.clear()
        client.close()


def test_update_calculation_404(db_session):
    user = create_user_in_db(db_session)

    def override_db():
        yield db_session

    client, _ = make_client(override_db, user=user)
    try:
        r = client.put(f"/calculations/{uuid4()}", json={"inputs": [1, 2]})
        assert r.status_code == 404
        assert r.json()["detail"] == "Calculation not found."
    finally:
        app.dependency_overrides.clear()
        client.close()


def test_delete_calculation_success(db_session):
    user = create_user_in_db(db_session)

    def override_db():
        yield db_session

    client, _ = make_client(override_db, user=user)
    try:
        created = client.post("/calculations", json={"type": "addition", "inputs": [7, 8]}).json()
        cid = created["id"]
        r = client.delete(f"/calculations/{cid}")
        assert r.status_code == 204
        # confirm gone
        r2 = client.get(f"/calculations/{cid}")
        assert r2.status_code == 404
    finally:
        app.dependency_overrides.clear()
        client.close()


def test_delete_calculation_404(db_session):
    user = create_user_in_db(db_session)

    def override_db():
        yield db_session

    client, _ = make_client(override_db, user=user)
    try:
        r = client.delete(f"/calculations/{uuid4()}")
        assert r.status_code == 404
        assert r.json()["detail"] == "Calculation not found."
    finally:
        app.dependency_overrides.clear()
        client.close()


def test_delete_calculation_invalid_uuid_400(db_session):
    # Covers invalid UUID branch (382-383 range)
    user = create_user_in_db(db_session)

    def override_db():
        yield db_session

    client, _ = make_client(override_db, user=user)
    try:
        r = client.delete("/calculations/not-a-uuid")
        assert r.status_code == 400
        assert r.json()["detail"] == "Invalid calculation id format."
    finally:
        app.dependency_overrides.clear()
        client.close()

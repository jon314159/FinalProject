from uuid import uuid4

import pytest
from fastapi import HTTPException, status

from app.auth.dependencies import get_current_active_user, get_current_user
from app.models.user import User


def _token_payload(user_id):
    return {"sub": str(user_id), "type": "access"}


def test_get_current_user_loads_existing_user(db_session, test_user, monkeypatch):
    monkeypatch.setattr(
        "app.auth.dependencies.decode_token",
        lambda token, token_type: _token_payload(test_user.id),
    )

    current_user = get_current_user(token="valid-token", db=db_session)

    assert isinstance(current_user, User)
    assert current_user.id == test_user.id


def test_get_current_user_propagates_invalid_token(db_session, monkeypatch):
    def reject_token(token, token_type):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )

    monkeypatch.setattr("app.auth.dependencies.decode_token", reject_token)

    with pytest.raises(HTTPException) as exc_info:
        get_current_user(token="invalid-token", db=db_session)

    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.parametrize("subject", [None, "not-a-uuid"])
def test_get_current_user_rejects_invalid_subject(db_session, monkeypatch, subject):
    monkeypatch.setattr(
        "app.auth.dependencies.decode_token",
        lambda token, token_type: {"sub": subject},
    )

    with pytest.raises(HTTPException) as exc_info:
        get_current_user(token="valid-token", db=db_session)

    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED


def test_get_current_user_rejects_missing_user(db_session, monkeypatch):
    monkeypatch.setattr(
        "app.auth.dependencies.decode_token",
        lambda token, token_type: _token_payload(uuid4()),
    )

    with pytest.raises(HTTPException) as exc_info:
        get_current_user(token="valid-token", db=db_session)

    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED


def test_get_current_active_user_accepts_active_user(test_user):
    assert get_current_active_user(current_user=test_user) is test_user


def test_get_current_active_user_rejects_inactive_user(test_user):
    test_user.is_active = False

    with pytest.raises(HTTPException) as exc_info:
        get_current_active_user(current_user=test_user)

    assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
    assert exc_info.value.detail == "Inactive user"

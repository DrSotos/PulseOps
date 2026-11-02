"""Unit tests for hashing and JWT token processing."""

from app.core.security import (
    create_access_token,
    hash_password,
    verify_password,
    verify_token,
)


def test_password_hashing():
    pw = "SuperSecurePassword999!"
    hashed = hash_password(pw)
    assert hashed != pw
    assert verify_password(pw, hashed) is True
    assert verify_password("WrongPassword!", hashed) is False


def test_jwt_lifecycle():
    user_id = "550e8400-e29b-41d4-a716-446655440000"
    token = create_access_token(user_id=user_id)
    payload = verify_token(token)

    assert payload is not None
    assert payload["sub"] == user_id
    assert "exp" in payload
    assert "iat" in payload


def test_invalid_jwt():
    assert verify_token("invalid.token.signature") is None


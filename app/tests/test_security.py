import pytest

from app.core.security import hash_password, validate_password_strength, verify_password


def test_hash_password_round_trip():
    password_hash = hash_password("Str0ngPass!23")
    assert verify_password("Str0ngPass!23", password_hash)


def test_verify_password_rejects_wrong_password():
    password_hash = hash_password("Str0ngPass!23")
    assert not verify_password("WrongPass!23", password_hash)


def test_validate_password_strength_accepts_valid_password():
    validate_password_strength("Str0ngPass!23")


@pytest.mark.parametrize(
    "password",
    [
        "short1",
        "onlyletters",
        "12345678",
        "a" * 73 + "1",
    ],
)
def test_validate_password_strength_rejects_invalid_passwords(password):
    with pytest.raises(ValueError):
        validate_password_strength(password)

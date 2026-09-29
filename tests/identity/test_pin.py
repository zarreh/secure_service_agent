"""PIN hashing: correctness, and the properties the design leans on."""

from __future__ import annotations

import pytest

from secureagent.identity.pin import hash_pin, is_well_formed_pin, spend_equal_time, verify_pin

PEPPER = "test-pepper-not-a-secret"


def test_a_correct_pin_verifies() -> None:
    assert verify_pin("4821", hash_pin("4821", PEPPER), PEPPER)


def test_a_wrong_pin_does_not_verify() -> None:
    assert not verify_pin("4822", hash_pin("4821", PEPPER), PEPPER)


def test_the_stored_value_never_contains_the_pin() -> None:
    stored = hash_pin("4821", PEPPER)
    assert "4821" not in stored


def test_salting_makes_equal_pins_hash_differently() -> None:
    assert hash_pin("4821", PEPPER) != hash_pin("4821", PEPPER)


def test_an_explicit_salt_makes_hashing_reproducible() -> None:
    salt = b"\x01" * 16
    assert hash_pin("4821", PEPPER, salt=salt) == hash_pin("4821", PEPPER, salt=salt)


def test_the_pepper_is_part_of_the_secret() -> None:
    # A stolen database without the pepper cannot verify a guess.
    stored = hash_pin("4821", PEPPER)
    assert not verify_pin("4821", stored, "a-different-pepper")


def test_hashing_requires_a_pepper() -> None:
    with pytest.raises(ValueError):
        hash_pin("4821", "")


@pytest.mark.parametrize("pin", ["", "123", "12345", "12a4", "١٢٣٤", "12 4", "1234\n"])
def test_malformed_pins_are_rejected_before_hashing(pin: str) -> None:
    assert not is_well_formed_pin(pin)
    assert not verify_pin(pin, hash_pin("4821", PEPPER), PEPPER)


@pytest.mark.parametrize(
    "stored", ["", "garbage", "scrypt$1$2$3", "bcrypt$1$1$1$AA==$AA==", "scrypt$x$8$1$AA==$AA=="]
)
def test_a_malformed_stored_value_never_verifies(stored: str) -> None:
    assert not verify_pin("4821", stored, PEPPER)


def test_spend_equal_time_runs_without_error() -> None:
    spend_equal_time(PEPPER)

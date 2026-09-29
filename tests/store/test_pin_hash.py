import pytest

from sentinel.store.pin_hash import (
    FIXTURE_PEPPER,
    hash_pin,
    is_well_formed_pin,
    verify_pin,
)

PEPPER = FIXTURE_PEPPER


def test_verify_pin_accepts_the_correct_pin() -> None:
    digest, salt = hash_pin("1234", pepper=PEPPER)
    assert verify_pin("1234", digest, salt, pepper=PEPPER)


def test_verify_pin_rejects_a_wrong_pin() -> None:
    digest, salt = hash_pin("1234", pepper=PEPPER)
    assert not verify_pin("9999", digest, salt, pepper=PEPPER)


def test_a_different_pepper_does_not_verify() -> None:
    # A stolen database alone must not be brute-forceable: without the pepper the
    # right PIN does not verify.
    digest, salt = hash_pin("1234", pepper=PEPPER)
    assert not verify_pin("1234", digest, salt, pepper="another-pepper")


def test_an_empty_pepper_is_refused() -> None:
    with pytest.raises(ValueError):
        hash_pin("1234", pepper="")
    digest, salt = hash_pin("1234", pepper=PEPPER)
    assert not verify_pin("1234", digest, salt, pepper="")


def test_hash_pin_is_salted_differently_each_call() -> None:
    digest_a, salt_a = hash_pin("1234", pepper=PEPPER)
    digest_b, salt_b = hash_pin("1234", pepper=PEPPER)
    assert salt_a != salt_b
    assert digest_a != digest_b


def test_hash_pin_is_deterministic_given_the_same_salt() -> None:
    digest_a, salt = hash_pin("1234", pepper=PEPPER)
    digest_b, _ = hash_pin("1234", pepper=PEPPER, salt=salt)
    assert digest_a == digest_b


def test_only_four_ascii_digits_are_well_formed() -> None:
    assert is_well_formed_pin("0042")
    for bad in ("", "123", "12345", "12a4", "١٢٣٤", " 123", "12.4"):
        assert not is_well_formed_pin(bad), bad

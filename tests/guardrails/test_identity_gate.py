from sentinel.guardrails.identity_gate import check_identity
from sentinel.store.account_store import AccountStore

_MAX_ATTEMPTS = 3


def test_correct_pin_verifies_and_resets_attempts(
    account_store: AccountStore, known_pins: dict[str, str]
) -> None:
    account_id, real_pin = next(iter(known_pins.items()))
    result = check_identity(account_store, account_id, real_pin, max_attempts=_MAX_ATTEMPTS)
    assert result.verified is True
    assert result.locked is False
    assert account_store.failed_attempts(account_id) == 0


def test_unknown_account_is_not_verified_and_not_tracked(account_store: AccountStore) -> None:
    result = check_identity(account_store, "ACCT_9999", "0000", max_attempts=_MAX_ATTEMPTS)
    assert result.verified is False
    assert result.locked is False
    # No lockout row is created for an id that doesn't exist — an attacker
    # cannot use the lockout counter to enumerate real account ids.
    assert account_store.failed_attempts("ACCT_9999") == 0


def test_repeated_wrong_pins_lock_the_account(
    account_store: AccountStore, known_pins: dict[str, str]
) -> None:
    account_id, real_pin = list(known_pins.items())[1]
    wrong_pin = "0000" if real_pin != "0000" else "1111"

    for expected_remaining in range(_MAX_ATTEMPTS - 1, -1, -1):
        result = check_identity(account_store, account_id, wrong_pin, max_attempts=_MAX_ATTEMPTS)
        assert result.verified is False
        assert result.attempts_remaining == expected_remaining

    assert result.locked is True
    assert account_store.is_locked(account_id) is True


def test_a_locked_account_rejects_even_the_correct_pin(
    account_store: AccountStore, known_pins: dict[str, str]
) -> None:
    account_id, real_pin = list(known_pins.items())[2]
    wrong_pin = "0000" if real_pin != "0000" else "1111"
    for _ in range(_MAX_ATTEMPTS):
        check_identity(account_store, account_id, wrong_pin, max_attempts=_MAX_ATTEMPTS)

    result = check_identity(account_store, account_id, real_pin, max_attempts=_MAX_ATTEMPTS)
    assert result.verified is False
    assert result.locked is True

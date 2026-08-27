from sentinel.store.pin_hash import hash_pin, verify_pin


def test_verify_pin_accepts_the_correct_pin() -> None:
    digest, salt = hash_pin("1234")
    assert verify_pin("1234", digest, salt)


def test_verify_pin_rejects_a_wrong_pin() -> None:
    digest, salt = hash_pin("1234")
    assert not verify_pin("9999", digest, salt)


def test_hash_pin_is_salted_differently_each_call() -> None:
    digest_a, salt_a = hash_pin("1234")
    digest_b, salt_b = hash_pin("1234")
    assert salt_a != salt_b
    assert digest_a != digest_b


def test_hash_pin_is_deterministic_given_the_same_salt() -> None:
    digest_a, salt = hash_pin("1234")
    digest_b, _ = hash_pin("1234", salt=salt)
    assert digest_a == digest_b

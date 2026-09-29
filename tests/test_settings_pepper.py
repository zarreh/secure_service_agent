import pytest
from pydantic import ValidationError

from sentinel.settings import Settings
from sentinel.store.pin_hash import FIXTURE_PEPPER


def test_the_public_fixture_pepper_is_refused_outside_development() -> None:
    for environment in ("production", "staging"):
        with pytest.raises(ValidationError):
            Settings(environment=environment)


def test_a_private_pepper_is_accepted_in_production() -> None:
    assert Settings(environment="production", identity_pepper="a-private-value").identity_pepper


def test_an_empty_pepper_is_refused_in_every_environment() -> None:
    # A blank env value must fail at startup, not on the first login.
    with pytest.raises(ValidationError):
        Settings(identity_pepper="")


def test_the_fixture_pepper_is_allowed_in_development_and_test() -> None:
    for environment in ("development", "test"):
        assert Settings(environment=environment).identity_pepper == FIXTURE_PEPPER

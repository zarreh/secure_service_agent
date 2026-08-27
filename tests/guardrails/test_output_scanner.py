from sentinel.guardrails.output_scanner import scan_output_deterministic


def test_a_normal_billing_answer_is_not_blocked() -> None:
    verdict = scan_output_deterministic(
        "Your plan costs $45/month with a 15GB data allowance.",
        verified_account_id="ACCT_2000",
    )
    assert verdict.blocked is False


def test_stating_a_pin_is_blocked() -> None:
    verdict = scan_output_deterministic(
        "Your pin is 4821, so you're all set.", verified_account_id="ACCT_2000"
    )
    assert verdict.blocked is True
    assert verdict.rule_id == "pin-disclosure"


def test_confirming_a_guessed_pin_is_blocked() -> None:
    verdict = scan_output_deterministic(
        "Yes, 4821 is the pin on file.", verified_account_id="ACCT_2000"
    )
    assert verdict.blocked is True
    assert verdict.rule_id == "pin-disclosure"


def test_referencing_another_account_is_blocked() -> None:
    verdict = scan_output_deterministic(
        "That matches what we see on ACCT_2001 as well.", verified_account_id="ACCT_2000"
    )
    assert verdict.blocked is True
    assert verdict.rule_id == "cross-account-reference"


def test_referencing_the_callers_own_account_is_not_blocked() -> None:
    verdict = scan_output_deterministic(
        "Confirmed for ACCT_2000, your plan renews next month.",
        verified_account_id="ACCT_2000",
    )
    assert verdict.blocked is False

"""Unit tests for environment classification (T050)."""

from __future__ import annotations

from aws_pick.core.environment import classify
from aws_pick.models.account import AwsAccount
from aws_pick.models.config import EnvironmentPattern


class TestClassify:
    def test_explicit_production(self) -> None:
        acct = AwsAccount(account_id="123456789012", account_name="my-app", environment="production")
        result = classify(acct)
        assert result is not None
        assert result.environment == "production"
        assert result.color == "red"

    def test_explicit_development(self) -> None:
        acct = AwsAccount(account_id="123456789012", account_name="my-app", environment="development")
        result = classify(acct)
        assert result is not None
        assert result.environment == "development"
        assert result.color == "green"

    def test_explicit_staging(self) -> None:
        acct = AwsAccount(account_id="123456789012", account_name="my-app", environment="staging")
        result = classify(acct)
        assert result is not None
        assert result.environment == "staging"
        assert result.color == "yellow"

    def test_explicit_unknown_env(self) -> None:
        acct = AwsAccount(account_id="123456789012", account_name="my-app", environment="sandbox")
        result = classify(acct)
        assert result is not None
        assert result.environment == "sandbox"
        assert result.color == "dim"

    def test_name_match_prod(self) -> None:
        acct = AwsAccount(account_id="123456789012", account_name="my-app-prod-01")
        result = classify(acct)
        assert result is not None
        assert result.environment == "production"

    def test_name_match_dev(self) -> None:
        acct = AwsAccount(account_id="123456789012", account_name="dev-my-app")
        result = classify(acct)
        assert result is not None
        assert result.environment == "development"

    def test_name_match_staging(self) -> None:
        acct = AwsAccount(account_id="123456789012", account_name="my-app-staging")
        result = classify(acct)
        assert result is not None
        assert result.environment == "staging"

    def test_name_match_stg(self) -> None:
        acct = AwsAccount(account_id="123456789012", account_name="stg-account")
        result = classify(acct)
        assert result is not None
        assert result.environment == "staging"

    def test_no_match(self) -> None:
        acct = AwsAccount(account_id="123456789012", account_name="my-app-123")
        result = classify(acct)
        assert result is None

    def test_case_insensitive(self) -> None:
        acct = AwsAccount(account_id="123456789012", account_name="MY-APP-PROD")
        result = classify(acct)
        assert result is not None
        assert result.environment == "production"

    def test_explicit_takes_precedence(self) -> None:
        acct = AwsAccount(account_id="123456789012", account_name="prod-app", environment="development")
        result = classify(acct)
        assert result is not None
        assert result.environment == "development"

    def test_custom_patterns(self) -> None:
        custom = [EnvironmentPattern(pattern="sandbox", environment="sandbox", color="cyan")]
        acct = AwsAccount(account_id="123456789012", account_name="my-sandbox-app")
        result = classify(acct, patterns=custom)
        assert result is not None
        assert result.environment == "sandbox"
        assert result.color == "cyan"

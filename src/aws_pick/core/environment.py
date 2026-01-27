"""Environment classification based on account name patterns."""

from __future__ import annotations

from aws_pick.models.account import AwsAccount
from aws_pick.models.config import EnvironmentPattern

_DEFAULT_PATTERNS: list[EnvironmentPattern] = [
    EnvironmentPattern(pattern="prod", environment="production", color="red"),
    EnvironmentPattern(pattern="production", environment="production", color="red"),
    EnvironmentPattern(pattern="dev", environment="development", color="green"),
    EnvironmentPattern(pattern="develop", environment="development", color="green"),
    EnvironmentPattern(pattern="development", environment="development", color="green"),
    EnvironmentPattern(pattern="stg", environment="staging", color="yellow"),
    EnvironmentPattern(pattern="staging", environment="staging", color="yellow"),
    EnvironmentPattern(pattern="stage", environment="staging", color="yellow"),
]


def classify(
    account: AwsAccount,
    patterns: list[EnvironmentPattern] | None = None,
) -> EnvironmentPattern | None:
    """Classify an account's environment.

    If the account has an explicit environment field, match it to a known pattern.
    Otherwise, match the account_name against patterns using case-insensitive substring.
    """
    if account.environment:
        effective_patterns = patterns or _DEFAULT_PATTERNS
        for p in effective_patterns:
            if p.environment.lower() == account.environment.lower():
                return p
        return EnvironmentPattern(pattern="", environment=account.environment, color="dim")

    effective_patterns = patterns or _DEFAULT_PATTERNS
    name_lower = account.account_name.lower()
    for p in effective_patterns:
        if p.pattern.lower() in name_lower:
            return p
    return None

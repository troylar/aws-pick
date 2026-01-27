"""Shared test fixtures for aws-pick."""

from __future__ import annotations

import pytest

from aws_pick.models.account import AccountRole, AwsAccount, AwsRole


@pytest.fixture
def small_account_list() -> list[AccountRole]:
    """3 accounts with 1 role each."""
    return [
        AccountRole(
            account=AwsAccount(account_id="111111111111", account_name="dev-account", environment="development"),
            role=AwsRole(role_name="AdminAccess"),
        ),
        AccountRole(
            account=AwsAccount(account_id="222222222222", account_name="staging-account", environment="staging"),
            role=AwsRole(role_name="ReadOnly"),
        ),
        AccountRole(
            account=AwsAccount(account_id="333333333333", account_name="prod-account", environment="production"),
            role=AwsRole(role_name="AdminAccess"),
        ),
    ]


@pytest.fixture
def mock_accounts() -> list[AccountRole]:
    """20 accounts with 3 roles each (60 items total)."""
    envs = [
        ("development", "dev"),
        ("staging", "stg"),
        ("production", "prod"),
        (None, "shared"),
    ]
    roles = ["AdminAccess", "ReadOnly", "PowerUser"]
    items: list[AccountRole] = []
    for i in range(20):
        env_label, env_prefix = envs[i % len(envs)]
        acct_id = str(100000000000 + i).zfill(12)
        acct_name = f"{env_prefix}-app-{i:02d}"
        for role_name in roles:
            items.append(
                AccountRole(
                    account=AwsAccount(account_id=acct_id, account_name=acct_name, environment=env_label),
                    role=AwsRole(role_name=role_name),
                )
            )
    return items


@pytest.fixture
def large_account_list() -> list[AccountRole]:
    """100 accounts with 1 role each."""
    items: list[AccountRole] = []
    for i in range(100):
        acct_id = str(200000000000 + i).zfill(12)
        items.append(
            AccountRole(
                account=AwsAccount(account_id=acct_id, account_name=f"account-{i:03d}"),
                role=AwsRole(role_name="AdminAccess"),
            )
        )
    return items


@pytest.fixture
def tmp_config_dir(tmp_path: object) -> object:
    """Temporary directory for config storage tests."""
    return tmp_path

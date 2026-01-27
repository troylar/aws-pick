"""Launch the TUI with sample account/role data for interactive testing."""

import tempfile
from pathlib import Path

from aws_pick.models.account import AccountRole, AwsAccount, AwsRole
from aws_pick.tui.app import CredentialSelectorApp


def _ar(account_id: str, name: str, role: str, env: str | None = None) -> AccountRole:
    return AccountRole(
        account=AwsAccount(account_id=account_id, account_name=name, environment=env),
        role=AwsRole(role_name=role),
    )


SAMPLE_ITEMS = [
    _ar("111111111111", "acme-production", "AdminAccess", "production"),
    _ar("111111111111", "acme-production", "ReadOnly", "production"),
    _ar("111111111111", "acme-production", "PowerUser", "production"),
    _ar("222222222222", "acme-staging", "AdminAccess", "staging"),
    _ar("222222222222", "acme-staging", "PowerUser", "staging"),
    _ar("222222222222", "acme-staging", "ReadOnly", "staging"),
    _ar("333333333333", "acme-development", "AdminAccess", "development"),
    _ar("333333333333", "acme-development", "Developer", "development"),
    _ar("333333333333", "acme-development", "ReadOnly", "development"),
    _ar("444444444444", "shared-services", "NetworkAdmin"),
    _ar("444444444444", "shared-services", "ReadOnly"),
    _ar("444444444444", "shared-services", "SupportUser"),
    _ar("555555555555", "data-lake-prod", "DataEngineer", "production"),
    _ar("555555555555", "data-lake-prod", "DataScientist", "production"),
    _ar("555555555555", "data-lake-prod", "ReadOnly", "production"),
    _ar("666666666666", "sandbox-dev", "AdminAccess", "development"),
    _ar("666666666666", "sandbox-dev", "Developer", "development"),
    _ar("777777777777", "security-audit", "SecurityAuditor"),
    _ar("777777777777", "security-audit", "ComplianceReviewer"),
    _ar("888888888888", "ci-cd-tooling", "DeploymentRole"),
    _ar("888888888888", "ci-cd-tooling", "PipelineAdmin"),
    _ar("888888888888", "ci-cd-tooling", "ReadOnly"),
    _ar("999999999999", "logging-prod", "ReadOnly", "production"),
    _ar("999999999999", "logging-prod", "LogAnalyst", "production"),
    _ar("101010101010", "backup-services", "BackupAdmin", "production"),
    _ar("101010101010", "backup-services", "ReadOnly", "production"),
    _ar("121212121212", "monitoring-prod", "MonitoringAdmin", "production"),
    _ar("121212121212", "monitoring-prod", "AlertManager", "production"),
    _ar("131313131313", "testing-qa", "QAEngineer", "staging"),
    _ar("131313131313", "testing-qa", "TestAutomation", "staging"),
]

if __name__ == "__main__":
    config_dir = Path(tempfile.mkdtemp(prefix="aws-pick-demo-"))
    app = CredentialSelectorApp(SAMPLE_ITEMS, config_dir=config_dir)
    app.run()

    result = app.result
    if result.cancelled:
        print("Cancelled.")
    else:
        print(f"\nSelected {len(result.selected)} account/role(s):")
        for item in result.selected:
            print(f"  {item['account_id']}:{item['role_name']} ({item['account_name']})")

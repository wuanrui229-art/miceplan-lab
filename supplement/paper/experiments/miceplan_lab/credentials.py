from __future__ import annotations

import os
import subprocess


KEYCHAIN_ACCOUNT = "miceplan-lab"


def resolve_api_key(
    env_name: str,
    *,
    keychain_service: str | None = None,
    keychain_account: str = KEYCHAIN_ACCOUNT,
) -> str:
    """Return a provider key without logging or persisting its plaintext value."""

    environment_value = os.getenv(env_name)
    if environment_value:
        return environment_value
    if not keychain_service:
        raise RuntimeError(f"Missing API credential: {env_name}")

    completed = subprocess.run(
        [
            "/usr/bin/security",
            "find-generic-password",
            "-a",
            keychain_account,
            "-s",
            keychain_service,
            "-w",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    value = completed.stdout.rstrip("\r\n") if completed.returncode == 0 else ""
    if not value:
        raise RuntimeError(
            f"Missing API credential: {env_name} or macOS Keychain service {keychain_service}"
        )
    return value

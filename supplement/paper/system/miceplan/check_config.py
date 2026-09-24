from __future__ import annotations

from .config import DEFAULT_ENV_PATH, configuration_summary


def main() -> None:
    config = configuration_summary()
    print(f"Config file: {DEFAULT_ENV_PATH}")
    print(f"Parser: {config['parser']}")
    print(f"Endpoint: {config['endpoint'] or 'MISSING'}")
    print(f"Model: {config['model'] or 'MISSING'}")
    print(f"API key: {'configured (hidden)' if config['api_key_configured'] else 'MISSING'}")


if __name__ == "__main__":
    main()

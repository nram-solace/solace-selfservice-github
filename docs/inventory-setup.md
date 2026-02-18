# Inventory Setup

Each team has a single inventory file at `inventory/<team>.yaml` containing broker connection details for all environments.

## File Format

```yaml
# inventory/team1.yaml
inventory:
    hosts:
    - environment: "dev"                 # matched by --env CLI parameter
      host: "dev-broker.example.com"
      sempUrl: "https://dev-broker.example.com:8080"
      sempUser: "admin"
      sempPasswordEnc: "Z0FBQUFBQm95..."  # encrypted password (optional)
      vpn: "Team1-DEV-VPN"

    - environment: "uat"
      host: "uat-broker.example.com"
      sempUrl: "https://uat-broker.example.com:8080"
      sempUser: "admin"
      sempPassword: "admin"              # plaintext password (optional)
      vpn: "Team1-UAT-VPN"
```

## Required Fields

| Field | Description |
| ----- | ----------- |
| `environment` | Environment key matched by the `--env` CLI parameter (e.g., `dev`, `uat`, `prod`) |
| `host` | Broker hostname |
| `sempUrl` | Full SEMP management URL including port |
| `sempUser` | SEMP admin username |
| `vpn` | Message VPN name on the broker |

## Password Fields (optional, pick one)

| Field | Description |
| ----- | ----------- |
| `sempPasswordEnc` | Fernet-encrypted password, decrypted at runtime via `PASSWORD_ENC_KEY` env var |
| `sempPassword` | Plaintext password (local dev only) |
| _(neither)_ | Falls back to `SEMP_PASSWORD` env var |

See [Password Management](password-management.md) for encryption details and priority order.

## Inventory Resolution

The tool resolves the broker connection in two steps:

1. **Team** is extracted from the CSV directory path: `input/csv/<team>/queues-dev.csv` → `team1`
2. **Environment** is matched from the `--env` CLI arg against `hosts[].environment`

```text
  CSV path:  input/csv/team1/queues-dev.csv  → team = "team1"
  CLI arg:   --env dev
  Lookup:    inventory/team1.yaml → hosts[environment="dev"] → vpn="Team1-DEV-VPN"
```

## Directory Layout

```text
inventory/
├── team1.yaml          ← All environments for team1
├── team2.yaml
├── team3.yaml
└── sample.yml          ← Sample inventory with password examples
```

## Sample Inventory

See `inventory/sample.yml` for a working example with all three password modes (encrypted, plaintext, env var fallback).

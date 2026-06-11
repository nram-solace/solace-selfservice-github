# Inventory Setup

Each client has one inventory file **per environment** at `inventory/<client>/<env>.yml`, with one entry per application (app). The environment comes from the file name; entries are keyed on `app`.

## File Format

```yaml
# inventory/NRAM/dev.yml
inventory:
    hosts:
    - app: "xyz"                          # matched by the <app> suffix of the CSV filename
      host: "dev-broker.example.com"
      sempUrl: "https://dev-broker.example.com:8080"
      sempUser: "admin"
      sempPasswordEnc: "Z0FBQUFBQm95..."  # encrypted password (optional)
      vpn: "XYZ-DEV-VPN"

    - app: "abc"
      host: "dev-broker.example.com"
      sempUrl: "https://dev-broker.example.com:8080"
      sempUser: "admin"
      sempPassword: "admin"               # plaintext password (optional)
      vpn: "ABC-DEV-VPN"
```

## Required Fields

| Field | Description |
| ----- | ----------- |
| `app` | Application name, matched by the `<app>` suffix of the CSV filename (e.g., `queues-xyz.csv` → `xyz`) |
| `host` | Broker hostname |
| `sempUrl` | Full SEMP management URL including port |
| `sempUser` | SEMP admin username |
| `vpn` | Message VPN name on the broker |

## Password Fields (optional, pick one)

| Field | Description |
| ----- | ----------- |
| `sempPasswordEnc` | Fernet-encrypted password, decrypted at runtime via `PASSWORD_ENC_KEY` env var |
| `sempPassword` | Plaintext password (local dev only) |
| _(neither)_ | Falls back to `SEMP_<ENV>_PASSWORD` then `SEMP_PASSWORD` env vars |

See [Password Management](password-management.md) for encryption details and priority order.

## Inventory Resolution

The tool resolves the broker connection from the CSV path alone:

1. **Client** and **environment** come from the CSV directory path: `input/csv/<client>/<env>/...`
2. **App** comes from the CSV filename suffix: `<object>-<app>.csv`
3. The entry matching `app` in `inventory/<client>/<env>.yml` is used

```text
  CSV path:  input/csv/NRAM/dev/queues-xyz.csv
             → client = "NRAM", env = "dev", app = "xyz"
  Lookup:    inventory/NRAM/dev.yml → hosts[app="xyz"] → vpn="XYZ-DEV-VPN"
```

If the inventory file or the app entry is missing, the run fails immediately — there is no fallback scan of other inventory files.

## Directory Layout

```text
inventory/
├── NRAM/
│   ├── dev.yml          ← All NRAM apps in dev
│   ├── int.yml
│   ├── sys.yml
│   ├── uat.yml
│   └── prod.yml
├── NT/
│   ├── dev.yml
│   ├── uat.yml
│   └── prod.yml
└── sample/
    ├── dev.yml          ← Sample inventory with password examples
    ├── uat.yml
    └── prod.yml
```

## Sample Inventory

See `inventory/sample/` for working examples covering all three password modes (plaintext in `dev.yml`, encrypted in `uat.yml`, env var fallback in `prod.yml`).

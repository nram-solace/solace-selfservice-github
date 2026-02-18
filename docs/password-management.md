# Password Management

The tool supports three password sources, checked in priority order:

1. **`sempPasswordEnc` in inventory** — encrypted password, decrypted at runtime via `PASSWORD_ENC_KEY` (recommended for shared/production use)
2. **`sempPassword` in inventory** — plaintext password (for local dev only)
3. **`SEMP_PASSWORD` env var** — fallback for hosts without inventory passwords (useful for CI/CD)
4. If none are available, the script exits with an error

## Encrypting Passwords

The `crypto_utils.py` CLI tool encrypts/decrypts passwords using Fernet encryption (AES-128-CBC + HMAC-SHA256) with PBKDF2 key derivation.

```bash
# Install cryptography library (only needed for encrypted passwords)
pip install cryptography

# Encrypt a password
export PASSWORD_ENC_KEY="your-secret-key"
python3 scripts/crypto_utils.py --encrypt-string "broker-password"

# Or use --key flag
python3 scripts/crypto_utils.py --key "your-secret-key" --encrypt-string "broker-password"

# Decrypt to verify
python3 scripts/crypto_utils.py --decrypt-string "<encrypted-value>"
```

## Inventory Password Examples

```yaml
inventory:
    hosts:
    # Encrypted password (recommended for shared use)
    - environment: "dev"
      host: "dev-broker.example.com"
      sempUrl: "https://dev-broker.example.com:8080"
      sempUser: "admin"
      sempPasswordEnc: "Z0FBQUFBQm95SXZa..."
      vpn: "Dev-VPN"

    # Plaintext password (for local dev only)
    - environment: "uat"
      host: "uat-broker.example.com"
      sempUrl: "https://uat-broker.example.com:8080"
      sempUser: "admin"
      sempPassword: "admin"
      vpn: "UAT-VPN"

    # No password in file — uses SEMP_PASSWORD env var at runtime
    - environment: "prod"
      host: "prod-broker.example.com"
      sempUrl: "https://prod-broker.example.com:8080"
      sempUser: "admin"
      vpn: "Prod-VPN"
```

## Running with Different Password Modes

```bash
# With encrypted password in inventory
PASSWORD_ENC_KEY="your-secret-key" bash scripts/solace_self_service.sh \
  --csv-file input/csv/team1/queues-dev.csv --env dev --verbose

# With env var fallback (no decryption needed)
SEMP_PASSWORD="admin" bash scripts/solace_self_service.sh \
  --csv-file input/csv/team1/queues-dev.csv --env dev --verbose
```

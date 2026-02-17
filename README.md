# Solace PubSub+ Self Service with Github Actions

Python-based automation tool for provisioning and managing Solace PubSub+ infrastructure using SEMPv2 API. Supports multi-team isolation with per-team directories and GitHub Actions workflow integration.

## Prerequisites

- Python 3.6+
- Solace PubSub+ broker access with SEMPv2 enabled
- Broker password via one of: `SEMP_PASSWORD` env var, encrypted password in inventory, or plaintext password in inventory (see [Password Management](#password-management))

## Installation

```bash
pip install -r requirements.txt
```

## Quick Start

1. **Configure broker connection** in `inventory/<team>.yaml` files
2. **Set authentication**: `export SEMP_PASSWORD=your_broker_password`
3. **Run automation**:

   ```bash
   # Using wrapper script (recommended)
   bash scripts/solace_self_service.sh --csv-file input/csv/team1/queues-dev.csv --env dev --verbose

   # Or step-by-step
   python3 scripts/csv_to_yaml.py --csv-file input/csv/team1/queues-dev.csv --env dev
   python3 scripts/yaml_to_semp.py --input input/yaml/team1/queues-dev.yaml -v
   ```

## Multi-Team Workflow

Each team gets their own isolated directory for CSV inputs and inventory. This prevents merge conflicts, provides clear ownership, and enables team-scoped workflow processing.

### Directory Layout

```text
input/csv/
├── team1/
│   ├── queues-dev.csv
│   ├── queues-uat.csv
│   ├── client-usernames.csv
│   ├── acl-profiles.csv
│   └── client-profiles.csv
├── team2/
│   ├── queues-dev.csv
│   └── queues-uat.csv
└── sample/
    ├── queues-dev.csv
    ├── queues-uat.csv
    └── queues-prod.csv

inventory/
├── team1.yaml                  ← All environments for team1
├── team2.yaml
├── team3.yaml
└── sample.yml                  ← Sample inventory with password examples
```

### How It Works

1. **Team auto-resolved from CSV path**: `input/csv/<team>/queues-dev.csv` extracts `team` from the directory name
2. **`--env` CLI parameter selects environment**: Specifies which environment (dev, uat, prod) to target
3. **Team-scoped inventory lookup**: Only the team's inventory file (`inventory/<team>.yaml`) is consulted
4. **Broker connection resolved**: The `--env` value is matched against `hosts[].name` in the team's inventory to get VPN, SEMP URL, and credentials

### Inventory Resolution

```text
  CSV path:  input/csv/team1/queues-dev.csv  → team = "team1"
  CLI arg:   --env dev
  Lookup:    inventory/team1.yaml → hosts[name="dev"] → vpn="test1-dev-vpn"
```

### Team Inventory File Format

Each team has a single inventory file with all their environment entries:

```yaml
# inventory/team1.yaml
inventory:
    hosts:
    - name: "dev"                       # --env value
      host: "dev-broker.example.com"
      sempUrl: "https://dev-broker.example.com:8080"
      sempUser: "admin"
      sempPasswordEnc: "Z0FBQUFBQm95..."  # encrypted password (optional)
      vpn: "Team1-DEV-VPN"

    - name: "uat"
      host: "uat-broker.example.com"
      sempUrl: "https://uat-broker.example.com:8080"
      sempUser: "admin"
      sempPassword: "admin"              # plaintext password (optional)
      vpn: "Team1-UAT-VPN"
```

### Team CSV Format

Team CSVs contain only object definitions — no environment column. The target environment is specified via the `--env` CLI parameter:

```csv
queueName,maxMsgSpoolUsage,accessType,permission,owner,redeliveryEnabled,maxRedeliveryCount,deliveryCountEnabled,jndiQueueName,subscriptions
team1-dev-queue1,1000,exclusive,consume,default,true,5,true,AUTO,team1/dev/orders/>
team1-dev-queue2,2000,non-exclusive,consume,default,false,10,true,,"team1/dev/events/*,team1/dev/notifications/*"
```

## Input Formats

### YAML Input

Direct configuration in `input/yaml/` directory:

```bash
python3 scripts/yaml_to_semp.py --input input/yaml/queues.yaml -v
```

### CSV Input

Convert CSV files to YAML format first, then process:

```bash
# Using wrapper script (recommended)
bash scripts/solace_self_service.sh --csv-file input/csv/team1/queues-dev.csv --env dev --verbose

# Two-step process
python3 scripts/csv_to_yaml.py --csv-file input/csv/team1/queues-dev.csv --env dev
python3 scripts/yaml_to_semp.py --input input/yaml/team1/queues-dev.yaml -v
```

**CSV Format Support:**

- **Single entries**: Automatically converted to lists (e.g., `topic1` -> `["topic1"]`)
- **Multiple entries**: Comma-separated values (e.g., `topic1,topic2` -> `["topic1", "topic2"]`)
- **Exception fields**: `clientConnectExceptions`, `publishTopicExceptions`, `subscribeTopicExceptions` are always treated as lists
- **Header validation**: CSV column headers are validated against `config/system.yaml` valid-tags
- **Per-environment CSVs**: Separate files per environment (e.g., `queues-dev.csv`, `queues-uat.csv`)

**Queue CSV Example:**

```csv
queueName,maxMsgSpoolUsage,accessType,permission,owner,redeliveryEnabled,maxRedeliveryCount,deliveryCountEnabled,jndiQueueName,subscriptions
team1-queue-1,1000,exclusive,consume,default,true,5,true,AUTO,team1/orders/>
team1-queue-2,2000,non-exclusive,consume,default,false,10,true,,"team1/events/*,team1/alerts/*"
```

## Password Management

The tool supports three password sources, checked in priority order:

1. **`SEMP_PASSWORD` env var** — overrides everything (recommended for CI/CD)
2. **`sempPasswordEnc` in inventory** — encrypted password, decrypted at runtime (recommended for shared/production use)
3. **`sempPassword` in inventory** — plaintext password (for local dev only)
4. If none are available, the script exits with an error

### Encrypting Passwords

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

### Inventory Password Examples

```yaml
inventory:
    hosts:
    # Encrypted password (recommended for shared use)
    - name: "dev"
      host: "dev-broker.example.com"
      sempUrl: "https://dev-broker.example.com:8080"
      sempUser: "admin"
      sempPasswordEnc: "Z0FBQUFBQm95SXZa..."
      vpn: "Dev-VPN"

    # Plaintext password (for local dev only)
    - name: "uat"
      host: "uat-broker.example.com"
      sempUrl: "https://uat-broker.example.com:8080"
      sempUser: "admin"
      sempPassword: "admin"
      vpn: "UAT-VPN"

    # No password in file — uses SEMP_PASSWORD env var at runtime
    - name: "prod"
      host: "prod-broker.example.com"
      sempUrl: "https://prod-broker.example.com:8080"
      sempUser: "admin"
      vpn: "Prod-VPN"
```

### Running with Different Password Modes

```bash
# With encrypted password in inventory
PASSWORD_ENC_KEY="your-secret-key" bash scripts/solace_self_service.sh \
  --csv-file input/csv/team1/queues-dev.csv --env dev --verbose

# With env var override (no decryption needed)
SEMP_PASSWORD="admin" bash scripts/solace_self_service.sh \
  --csv-file input/csv/team1/queues-dev.csv --env dev --verbose
```

## Supported Operations

### Create Operations

- **Queues**: Regular and dead message queues with configurable JNDI mappings
- **Client Usernames**: With associated ACL and client profiles
- **Client Profiles**: Connection and messaging profiles
- **ACL Profiles**: Access control lists with connect/publish/subscribe exceptions
- **Subscriptions**: Queue topic subscriptions (single or multiple topics)

### Delete Operations

- All object types except subscriptions
- JNDI mappings deleted alongside queues

### Queue Features

- **JNDI Queue Name** (`jndiQueueName` field):
  - `AUTO` - Auto-generates JNDI name as `Q_{queueName}` (dots replaced with underscores)
  - Custom value - Uses the provided JNDI name directly
  - Empty/blank - Skips JNDI mapping entirely
  - Field absent - Legacy behavior, auto-generates JNDI name
- **Max Redelivery Count** (`maxRedeliveryCount`): Configurable redelivery count per queue
- **Subscriptions**: Single topic or comma-separated multiple topics

## GitHub Actions Integration

### Available Workflows

All workflows use `workflow_dispatch` (manual trigger) with required `csv_file` and `environment` inputs. Team name is auto-extracted from the CSV directory path.

- **`process-queues-csv.yml`**: Queue processing workflow
  - Manual dispatch with `csv_file` path and `environment` inputs
  - Auto-detects team from path pattern `input/csv/<team>/queues*.csv`
  - Posts team name, environment, and file path in GitHub step summary
- **`process-client-usernames-csv.yml`**: Processes dependency chain in sequence
  - Processing order: ACL profiles → client profiles → client usernames
  - Each step checks for the corresponding CSV file in the team directory before processing
- **`process-acl-profiles-csv.yml`**: ACL profile processing

### Workflow Features

- Automatic CSV to YAML conversion via `solace_self_service.sh`
- Team-scoped processing (each team's CSV processed independently)
- Sequential processing of related configurations (ACL → Client Profiles → Client Usernames)
- GitHub step summary with team name, environment, file path, and processing results
- `--env` parameter passed through to scripts for environment targeting

### Setup Requirements

- GitHub repository secrets: `SEMP_PASSWORD` (or `PASSWORD_ENC_KEY` if using encrypted passwords in inventory)
- Optional: GitHub repository variables for `SEMP_USER`

## Configuration Structure

```text
config/
├── system.yaml          ← SEMP settings, valid-tags, processing rules
└── defaults/            ← Default object templates
    ├── queue.yaml
    ├── dmqueue.yaml
    ├── client-user.yaml
    ├── client-profile.yaml
    └── acl-profile.yaml

inventory/
├── <team>.yaml          ← Per-team inventory (multi-env hosts)
└── sample.yml           ← Sample inventory with password examples

input/
├── csv/
│   └── <team>/          ← Per-team CSV inputs (one file per env)
│       ├── queues-dev.csv
│       ├── queues-uat.csv
│       ├── client-usernames.csv
│       ├── acl-profiles.csv
│       └── client-profiles.csv
├── yaml/                ← Generated YAML (build artifact, gitignored)
└── sample/              ← Sample YAML input files for reference

scripts/
├── yaml_to_semp.py      ← Main automation script (YAML → SEMPv2)
├── csv_to_yaml.py       ← CSV to YAML converter
├── solace_self_service.sh ← Wrapper script (CSV → YAML → SEMP pipeline)
└── crypto_utils.py      ← Password encryption/decryption CLI tool

.github/workflows/       ← GitHub Actions automation workflows
```

## Team Onboarding

To add a new team to the self-service system:

1. **Create team input directory**:

   ```bash
   mkdir -p input/csv/<team-name>
   ```

2. **Create team inventory file** with environment entries:

   Create `inventory/<team-name>.yaml`:

   ```yaml
   inventory:
       hosts:
       - name: "dev"
         host: "dev-broker.example.com"
         sempUrl: "https://dev-broker.example.com:8080"
         sempUser: "admin"
         sempPasswordEnc: "<encrypted-password>"
         vpn: "<TeamName>-DEV-VPN"
       - name: "uat"
         host: "uat-broker.example.com"
         sempUrl: "https://uat-broker.example.com:8080"
         sempUser: "admin"
         sempPasswordEnc: "<encrypted-password>"
         vpn: "<TeamName>-UAT-VPN"
   ```

3. **Create CSV files** per environment in the team directory:

   ```csv
   queueName,maxMsgSpoolUsage,accessType,permission,owner
   example-queue,1000,exclusive,consume,default
   ```

4. **Test the pipeline**:

   ```bash
   export SEMP_PASSWORD=your_broker_password
   bash scripts/solace_self_service.sh --csv-file input/csv/<team-name>/queues-dev.csv --env dev --verbose
   ```

## Operational Tasks

### Environment Management

- **Development**: Use `local/input/nram-dev.yaml` and `inventory/nram/nram-local.yaml` (dev-only, multi-file)
- **Testing**: Use `inventory/nram/nram-cloud.yaml` (dev-only, multi-file)
- **Production**: Use environment-specific `inventory/` files

### Logging

- Logs written to `logs/` directory with timestamp
- Use `-v`, `-vv`, or `-vvv` for increasing verbosity levels
- Color-coded console output (cyan for yaml_to_semp, magenta for csv_to_yaml)

### Batch Processing

The tool handles object dependencies automatically:

1. Dead message queues created before regular queues
2. Client/ACL profiles created before client usernames
3. JNDI mappings handled based on `jndiQueueName` field
4. Topic subscriptions added after queue creation

### Error Handling

- Objects are skipped if they already exist (ALREADY_EXISTS treated as success)
- Failed operations logged with detailed error messages
- System continues processing remaining objects on individual failures

## Local Development with Docker

A Docker Compose setup is available for local testing with a Solace PubSub+ broker:

```bash
cd docker && docker compose up -d
```

The init container automatically provisions per-team VPNs (e.g., `test1-dev-vpn`, `test1-uat-vpn` for team1). See `docker/docker-compose.yaml` for details.

## Recent Improvements

### Encrypted Password Support

- **Per-broker passwords**: New `sempPasswordEnc` field in inventory files for encrypted passwords
- **Password priority**: `SEMP_PASSWORD` env var > `sempPasswordEnc` (decrypt) > `sempPassword` (plaintext) > error exit
- **CLI encryption tool**: `scripts/crypto_utils.py` for encrypting/decrypting passwords (Fernet/PBKDF2)
- **Lazy decryption**: Password resolved only for the target host, not during inventory loading
- **Optional dependency**: `cryptography` library only required when using encrypted passwords

### Environment Selection via CLI

- **`--env` CLI parameter**: Clean separation of "what to create" from "where to create it"
- **No env column in CSV**: Removed `envKey`/`inventoryKey` columns from CSV files
- **Per-environment CSVs**: Split CSV files by environment (e.g., `queues-dev.csv`, `queues-uat.csv`)
- **Team path required**: All CSVs must be under `input/csv/<team>/` (flat paths eliminated)
- **Workflows updated**: All workflows now use `workflow_dispatch` with required `environment` input (push triggers removed)

### Multi-Team Isolation

- **Per-team directories**: `input/csv/<team>/` for CSV inputs, `inventory/<team>.yaml` for broker connections
- **Team-scoped inventory**: Team context flows end-to-end from `csv_to_yaml.py` through `yaml_to_semp.py` to `Inventory.py`
- **Workflow glob triggers**: All workflows support multi-team path patterns

### Version 2.5.2 Updates

- **Custom JNDI Names**: Support for AUTO, custom, or skip JNDI mapping via `jndiQueueName` field
- **Max Redelivery Count**: Added `maxRedeliveryCount` queue configuration support
- **Enhanced CSV Parsing**: Fixed single entry handling for exception fields
- **Header Validation**: CSV headers validated against `config/system.yaml` valid-tags

## Limitations

- No support for object property updates (only create/delete)
- Subscription deletion not implemented
- Limited to supported Solace object types (queues, client usernames, profiles)
- No built-in backup/rollback functionality

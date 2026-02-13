# Solace PubSub+ Self Service with Github Actions

Python-based automation tool for provisioning and managing Solace PubSub+ infrastructure using SEMPv2 API. Supports multi-team isolation with per-team directories and GitHub Actions workflow integration.

## Prerequisites

- Python 3.6+
- Solace PubSub+ broker access with SEMPv2 enabled
- Environment variable `SEMP_PASSWORD` set for broker authentication

## Installation

```bash
pip install -r requirements.txt
```

## Quick Start

1. **Configure broker connection** in `inventory/<team>/` files
2. **Set authentication**: `export SEMP_PASSWORD=your_broker_password`
3. **Run automation**:

   ```bash
   # Team-based (recommended)
   bash scripts/solace_self_service.sh --csv-file input/csv/team1/queues.csv --verbose

   # Or step-by-step
   python3 scripts/csv_to_yaml.py --csv-file input/csv/team1/queues.csv
   python3 scripts/yaml_to_semp.py --input input/yaml/team1/queues.yaml -v
   ```

## Multi-Team Workflow

Each team gets their own isolated directory for CSV inputs and inventory. This prevents merge conflicts, provides clear ownership, and enables team-scoped workflow processing.

### Directory Layout

```text
input/csv/
├── team1/
│   ├── queues.csv
│   ├── client-usernames.csv
│   ├── acl-profiles.csv
│   └── client-profiles.csv
├── team2/
│   └── queues.csv
├── team3/
│   └── queues.csv
└── queues.csv                  ← Legacy flat path (backward compatible)

inventory/
├── team1/
│   └── team1.yaml              ← All environments for team1
├── team2/
│   └── team2.yaml
├── team3/
│   └── team3.yaml
├── sample-inventory-local.yaml ← Legacy inventory (backward compatible)
└── sample-inventory-cloud.yaml
```

### How It Works

1. **Team auto-resolved from CSV path**: `input/csv/<team>/queues.csv` extracts `team` from the directory name
2. **`envKey` column selects environment**: Each row in the CSV specifies which environment (dev, uat, etc.) to target
3. **Team-scoped inventory lookup**: Only the team's inventory file (`inventory/<team>/<team>.yaml`) is consulted
4. **Broker connection resolved**: The `envKey` value is matched against `hosts[].name` in the team's inventory to get VPN, SEMP URL, and credentials

### Inventory Resolution

```text
Team-based (new):
  CSV path:  input/csv/team1/queues.csv  → team = "team1"
  CSV row:   envKey = "dev"
  Lookup:    inventory/team1/team1.yaml → hosts[name="dev"] → vpn="test1-dev-vpn"

Legacy (backward compatible):
  CSV path:  input/csv/queues.csv        → team = None
  CSV row:   inventoryKey = "test"
  Lookup:    Full recursive scan of inventory/ → hosts[name="test"] → vpn="TestVPN"
```

### Team Inventory File Format

Each team has a single inventory file with all their environment entries:

```yaml
# inventory/team1/team1.yaml
inventory:
    environment: "team1"
    hosts:
    - name: "dev"                       # envKey value in CSV
      host: "dev-broker.example.com"
      sempUrl: "https://dev-broker.example.com:8080"
      sempUser: "admin"
      vpn: "Team1-DEV-VPN"

    - name: "uat"
      host: "uat-broker.example.com"
      sempUrl: "https://uat-broker.example.com:8080"
      sempUser: "admin"
      vpn: "Team1-UAT-VPN"
```

### Team CSV Format

Team CSVs use the `envKey` column (instead of `inventoryKey`) to select the target environment:

```csv
envKey,queueName,maxMsgSpoolUsage,accessType,permission,owner,redeliveryEnabled,maxRedeliveryCount,deliveryCountEnabled,jndiQueueName,subscriptions
dev,team1-order-queue,1000,exclusive,consume,default,true,5,true,AUTO,team1/dev/orders/>
dev,team1-event-queue,2000,non-exclusive,consume,default,false,10,true,,"team1/dev/events/*,team1/dev/notifications/*"
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
# Team-based (recommended)
bash scripts/solace_self_service.sh --csv-file input/csv/team1/queues.csv --verbose

# Two-step process
python3 scripts/csv_to_yaml.py --csv-file input/csv/team1/queues.csv
python3 scripts/yaml_to_semp.py --input input/yaml/team1/queues.yaml -v

# Legacy flat path (backward compatible)
bash scripts/solace_self_service.sh --csv-file input/csv/queues.csv --verbose
```

**CSV Format Support:**

- **Single entries**: Automatically converted to lists (e.g., `topic1` -> `["topic1"]`)
- **Multiple entries**: Comma-separated values (e.g., `topic1,topic2` -> `["topic1", "topic2"]`)
- **Exception fields**: `clientConnectExceptions`, `publishTopicExceptions`, `subscribeTopicExceptions` are always treated as lists
- **Header validation**: CSV column headers are validated against `config/system.yaml` valid-tags
- **envKey column** (team-based): Selects the target environment from the team's inventory file
- **inventoryKey column** (legacy): Maps CSV rows to broker inventory entries for VPN name resolution

**Queue CSV Examples:**

Team-based (with `envKey`):

```csv
envKey,queueName,maxMsgSpoolUsage,accessType,permission,owner,redeliveryEnabled,maxRedeliveryCount,deliveryCountEnabled,jndiQueueName,subscriptions
dev,team1-queue-1,1000,exclusive,consume,default,true,5,true,AUTO,team1/orders/>
uat,team1-queue-2,2000,non-exclusive,consume,default,false,10,true,,"team1/events/*,team1/alerts/*"
```

Legacy (with `inventoryKey`):

```csv
inventoryKey,queueName,maxMsgSpoolUsage,accessType,permission,owner,redeliveryEnabled,maxRedeliveryCount,deliveryCountEnabled,jndiQueueName,subscriptions
test,my-queue-1,1000,exclusive,consume,default,true,5,true,AUTO,topic/1
test,my-queue-2,2000,non-exclusive,read-only,default,false,10,true,custom/jndi/name,"topic/>,topic2/*"
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

All workflows support both team-based paths (`input/csv/<team>/`) and legacy flat paths (`input/csv/`). Team name is auto-extracted from the CSV directory path.

- **`process-queues-csv.yml`**: Queue processing workflow
  - Triggers on push to `input/csv/**/queues.csv`
  - Auto-detects team from path pattern `input/csv/<team>/queues.csv`
  - Supports `workflow_dispatch` with custom CSV path input
  - Posts team name and file path in GitHub step summary
- **`process-client-usernames-csv.yml`**: Processes dependency chain in sequence
  - Triggers on push to `input/csv/**/client-usernames.csv`
  - Processing order: ACL profiles → client profiles → client usernames
  - Each step checks for the corresponding CSV file in the team directory before processing
- **`process-acl-profiles-csv.yml`**: ACL profile processing
  - Triggers on push to `input/csv/**/acl-profiles.csv`

### Workflow Features

- Automatic CSV to YAML conversion via `solace_self_service.sh`
- Team-scoped processing (each team's CSV triggers independently)
- Sequential processing of related configurations (ACL -> Client Profiles -> Client Usernames)
- GitHub step summary with team name, file path, and processing results
- Manual trigger via `workflow_dispatch` for ad-hoc runs

### Setup Requirements

- GitHub repository secrets: `SEMP_PASSWORD`
- Optional: GitHub repository variables for `SEMP_USER`

## Configuration Structure

```text
config/
├── system.yaml          ← SEMP settings, valid-tags (incl. envKey), processing rules
└── defaults/            ← Default object templates
    ├── queue.yaml
    ├── dmqueue.yaml
    ├── client-user.yaml
    ├── client-profile.yaml
    └── acl-profile.yaml

inventory/
├── <team>/              ← Per-team inventory (multi-env hosts)
│   └── <team>.yaml
├── sample-inventory-local.yaml  ← Legacy/sample inventory
└── sample-inventory-cloud.yaml

input/
├── csv/
│   ├── <team>/          ← Per-team CSV inputs
│   │   ├── queues.csv
│   │   ├── client-usernames.csv
│   │   ├── acl-profiles.csv
│   │   └── client-profiles.csv
│   └── queues.csv       ← Legacy flat path
├── yaml/                ← Generated YAML (build artifact, gitignored)
└── sample/              ← Sample YAML input files for reference

.github/workflows/       ← GitHub Actions automation workflows
```

## Team Onboarding

To add a new team to the self-service system:

1. **Create team input directory**:

   ```bash
   mkdir -p input/csv/<team-name>
   ```

2. **Create team inventory file** with environment entries:

   ```bash
   mkdir -p inventory/<team-name>
   ```

   Create `inventory/<team-name>/<team-name>.yaml`:

   ```yaml
   inventory:
       environment: "<team-name>"
       hosts:
       - name: "dev"
         host: "dev-broker.example.com"
         sempUrl: "https://dev-broker.example.com:8080"
         sempUser: "admin"
         vpn: "<TeamName>-DEV-VPN"
       - name: "uat"
         host: "uat-broker.example.com"
         sempUrl: "https://uat-broker.example.com:8080"
         sempUser: "admin"
         vpn: "<TeamName>-UAT-VPN"
   ```

3. **Create sample CSV** in the team directory:

   ```csv
   envKey,queueName,maxMsgSpoolUsage,accessType,permission,owner
   dev,example-queue,1000,exclusive,consume,default
   ```

4. **Test the pipeline**:

   ```bash
   export SEMP_PASSWORD=your_broker_password
   bash scripts/solace_self_service.sh --csv-file input/csv/<team-name>/queues.csv --verbose
   ```

## Operational Tasks

### Environment Management

- **Development**: Use `local/input/nram-dev.yaml` and `inventory/nram/nram-local.yaml`
- **Testing**: Use `inventory/nram/nram-cloud.yaml`
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

### Multi-Team Isolation (Phase 1)

- **Per-team directories**: `input/csv/<team>/` and `inventory/<team>/` for team isolation
- **envKey column**: New CSV column that selects target environment from team's inventory (replaces `inventoryKey` for team workflows)
- **Team-scoped inventory**: `csv_to_yaml.py` resolves team from CSV path and loads only that team's inventory file
- **Recursive inventory scanning**: `Inventory.py` uses `os.walk()` to discover inventory files in subdirectories
- **Team propagation**: Team context flows from `csv_to_yaml.py` through generated YAML to `yaml_to_semp.py` and `Inventory.py`
- **Workflow glob triggers**: All workflows use `input/csv/**/<type>.csv` patterns for multi-team support
- **Backward compatibility**: Legacy flat paths (`input/csv/queues.csv` with `inventoryKey`) continue to work unchanged

### Version 2.5.2 Updates

- **Custom JNDI Names**: Support for AUTO, custom, or skip JNDI mapping via `jndiQueueName` field
- **Max Redelivery Count**: Added `maxRedeliveryCount` queue configuration support
- **Manual Workflow Dispatch**: `workflow_dispatch` trigger for manual CSV processing
- **Enhanced CSV Parsing**: Fixed single entry handling for exception fields
- **Header Validation**: CSV headers validated against `config/system.yaml` valid-tags

### CSV Parsing Fixes

- Single topic exceptions now correctly formatted as lists
- Character list detection and correction for malformed CSV data
- Automatic list wrapping for exception fields (`clientConnectExceptions`, `publishTopicExceptions`, `subscribeTopicExceptions`)

## Limitations

- No support for object property updates (only create/delete)
- Subscription deletion not implemented
- Limited to supported Solace object types (queues, client usernames, profiles)
- No built-in backup/rollback functionality
- PR-based approval and validation guardrails planned for future phases

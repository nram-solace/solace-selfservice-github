# Team Setup

Each team gets their own isolated directory for CSV inputs and inventory. This prevents merge conflicts, provides clear ownership, and enables team-scoped workflow processing.

## Directory Layout

```text
input/csv/
├── team1/
│   ├── queues-dev.csv
│   ├── queues-uat.csv
│   ├── client-usernames-dev.csv
│   ├── acl-profiles-dev.csv
│   └── client-profiles-dev.csv
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

## How It Works

1. **Team auto-resolved from CSV path**: `input/csv/<team>/queues-dev.csv` extracts `team` from the directory name
2. **`--env` CLI parameter selects environment**: Specifies which environment (dev, uat, prod) to target
3. **Team-scoped inventory lookup**: Only the team's inventory file (`inventory/<team>.yaml`) is consulted — see [Inventory Setup](inventory-setup.md)
4. **Broker connection resolved**: The `--env` value is matched against `hosts[].environment` in the team's inventory to get VPN, SEMP URL, and credentials

## Team CSV Format

Team CSVs contain only object definitions — no environment column. The target environment is specified via the `--env` CLI parameter:

```csv
queueName,maxMsgSpoolUsage,accessType,permission,owner,redeliveryEnabled,maxRedeliveryCount,deliveryCountEnabled,jndiQueueName,subscriptions
team1-dev-queue1,1000,exclusive,consume,default,true,5,true,AUTO,team1/dev/orders/>
team1-dev-queue2,2000,non-exclusive,consume,default,false,10,true,,"team1/dev/events/*,team1/dev/notifications/*"
```

## Team Onboarding

To add a new team to the self-service system:

1. **Create team input directory**:

   ```bash
   mkdir -p input/csv/<team-name>
   ```

2. **Create team inventory file** `inventory/<team-name>.yaml` with environment entries.
   See [Inventory Setup](inventory-setup.md) for format and required fields.

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
│       ├── client-usernames-dev.csv
│       ├── acl-profiles-dev.csv
│       └── client-profiles-dev.csv
├── yaml/                ← Generated YAML (build artifact, gitignored)
└── sample/              ← Sample YAML input files for reference

scripts/
├── yaml_to_semp.py      ← Main automation script (YAML → SEMPv2)
├── csv_to_yaml.py       ← CSV to YAML converter
├── solace_self_service.sh ← Wrapper script (CSV → YAML → SEMP pipeline)
└── crypto_utils.py      ← Password encryption/decryption CLI tool

.github/workflows/       ← GitHub Actions automation workflows
```

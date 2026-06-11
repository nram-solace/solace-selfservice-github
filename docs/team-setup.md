# App Setup

CSV inputs are organized per client and environment, with one file per object type per application (app). This prevents merge conflicts, provides clear ownership, and lets a single per-environment inventory file serve hundreds of apps.

## Directory Layout

```text
input/csv/
├── NRAM/                       ← client
│   ├── dev/                    ← environment
│   │   ├── queues-xyz.csv      ← <object>-<app>.csv
│   │   ├── queues-abc.csv
│   │   ├── client-usernames-xyz.csv
│   │   ├── acl-profiles-xyz.csv
│   │   └── client-profiles-xyz.csv
│   ├── uat/
│   │   └── queues-xyz.csv
│   └── prod/
│       └── queues-xyz.csv
└── sample/
    ├── dev/
    │   └── queues-team1.csv
    ├── uat/
    │   └── queues-team1.csv
    └── prod/
        └── queues-team1.csv

inventory/
├── NRAM/
│   ├── dev.yml                 ← All NRAM apps in dev (keyed by app)
│   ├── uat.yml
│   └── prod.yml
└── sample/
    ├── dev.yml                 ← Sample inventory with password examples
    ├── uat.yml
    └── prod.yml
```

## How It Works

1. **Client and environment auto-resolved from CSV path**: `input/csv/<client>/<env>/...`
2. **App auto-resolved from CSV filename**: `queues-xyz.csv` → app `xyz`
3. **Inventory lookup**: `inventory/<client>/<env>.yml` is read and the entry matching `app` is used — see [Inventory Setup](inventory-setup.md)
4. **Broker connection resolved**: The app's entry provides VPN, SEMP URL, and credentials

The `--env` CLI parameter is optional; if given, it must match the `<env>` directory in the CSV path.

> Note: App names must not start with an object-type keyword (`queues`, `client-usernames`, `client-profiles`, `acl-profiles`, `subscriptions`).

## App CSV Format

CSVs contain only object definitions — no environment or app column. Both are derived from the file path:

```csv
queueName,maxMsgSpoolUsage,accessType,permission,owner,redeliveryEnabled,maxRedeliveryCount,deliveryCountEnabled,jndiQueueName,subscriptions
xyz-dev-queue1,1000,exclusive,consume,default,true,5,true,AUTO,xyz/dev/orders/>
xyz-dev-queue2,2000,non-exclusive,consume,default,false,10,true,,"xyz/dev/events/*,xyz/dev/notifications/*"
```

## App Onboarding

To add a new app to the self-service system:

1. **Add an inventory entry** for the app in each target environment file
   `inventory/<client>/<env>.yml`:

   ```yaml
   - app: "newapp"
     host: "dev-broker.example.com"
     sempUrl: "https://dev-broker.example.com:8080"
     sempUser: "admin"
     vpn: "NEWAPP-DEV-VPN"
   ```

2. **Create CSV files** under the client/env directory:

   ```bash
   mkdir -p input/csv/<client>/dev
   # input/csv/<client>/dev/queues-newapp.csv
   ```

3. **Test the pipeline**:

   ```bash
   export SEMP_PASSWORD=your_broker_password
   bash scripts/solace_self_service.sh --csv-file input/csv/<client>/dev/queues-newapp.csv --verbose
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
└── <client>/
    └── <env>.yml        ← Per-environment inventory (keyed by app)

input/
├── csv/
│   └── <client>/
│       └── <env>/       ← Per-env CSV inputs (one file per object type per app)
│           ├── queues-<app>.csv
│           ├── client-usernames-<app>.csv
│           ├── acl-profiles-<app>.csv
│           └── client-profiles-<app>.csv
└── yaml/                ← Generated YAML (build artifact, gitignored)

scripts/
├── yaml_to_semp.py      ← Main automation script (YAML → SEMPv2)
├── csv_to_yaml.py       ← CSV to YAML converter
├── solace_self_service.sh ← Wrapper script (CSV → YAML → SEMP pipeline)
└── crypto_utils.py      ← Password encryption/decryption CLI tool

.github/workflows/       ← GitHub Actions automation workflows
```

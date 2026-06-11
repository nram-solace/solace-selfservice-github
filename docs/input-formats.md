# Input Formats

## YAML Input

Direct configuration in `input/yaml/` directory:

```bash
python3 scripts/yaml_to_semp.py --input input/yaml/queues.yaml -v
```

## CSV Input

Convert CSV files to YAML format first, then process:

```bash
# Using wrapper script (recommended)
bash scripts/solace_self_service.sh --csv-file input/csv/sample/dev/queues-team1.csv --verbose

# Two-step process
python3 scripts/csv_to_yaml.py --csv-file input/csv/sample/dev/queues-team1.csv
python3 scripts/yaml_to_semp.py --input input/yaml/sample/dev/queues-team1.yaml -v
```

**CSV Format Support:**

- **Path layout**: `input/csv/<client>/<env>/<object>-<app>.csv` — client, environment, and app are derived from the path
- **Single entries**: Automatically converted to lists (e.g., `topic1` -> `["topic1"]`)
- **Multiple entries**: Comma-separated values (e.g., `topic1,topic2` -> `["topic1", "topic2"]`)
- **Exception fields**: `clientConnectExceptions`, `publishTopicExceptions`, `subscribeTopicExceptions` are always treated as lists
- **Header validation**: CSV column headers are validated against `config/system.yaml` valid-tags
- **Per-app CSVs**: Separate files per app under each environment directory (e.g., `dev/queues-xyz.csv`, `uat/queues-xyz.csv`)

**Queue CSV Example:**

```csv
queueName,maxMsgSpoolUsage,accessType,permission,owner,redeliveryEnabled,maxRedeliveryCount,deliveryCountEnabled,jndiQueueName,subscriptions
team1-queue-1,1000,exclusive,consume,default,true,5,true,AUTO,team1/orders/>
team1-queue-2,2000,non-exclusive,consume,default,false,10,true,,"team1/events/*,team1/alerts/*"
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

## Queue Features

- **JNDI Queue Name** (`jndiQueueName` field):
  - `AUTO` - Auto-generates JNDI name as `Q_{queueName}` (dots replaced with underscores)
  - Custom value - Uses the provided JNDI name directly
  - Empty/blank - Skips JNDI mapping entirely
  - Field absent - Legacy behavior, auto-generates JNDI name
- **Max Redelivery Count** (`maxRedeliveryCount`): Configurable redelivery count per queue
- **Subscriptions**: Single topic or comma-separated multiple topics

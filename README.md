# Solace PubSub+ Self service with Github Actions

Python-based automation tool for provisioning and managing Solace PubSub+ infrastructure using SEMPv2 API. Supports GitHub Actions workflow integration.

## Prerequisites

- Python 3.6+
- Solace PubSub+ broker access with SEMPv2 enabled
- Environment variable `SEMP_PASSWORD` set for broker authentication

## Installation

```bash
pip install -r requirements.txt
```

## Quick Start

1. **Configure broker connection** in `inventory/<environment>/` files
2. **Set authentication**: `export SEMP_PASSWORD=your_broker_password`  
3. **Run automation**:
   ```bash
   python3 scripts/yaml_to_semp.py --input input/default.yaml -v
   ```

## Input Formats

### YAML Input
Direct configuration in `input/` directory:
```bash
python3 scripts/yaml_to_semp.py --input input/test.yaml
```

### CSV Input
Convert CSV files to YAML format first:
```bash
python3 scripts/csv_to_yaml.py --csv-file input/csv/queues.csv
bash scripts/solace_self_service.sh  # Process all CSV files
```

## Supported Operations

### Create Operations
- **Queues**: Regular and dead message queues with JNDI mappings
- **Client Usernames**: With associated ACL and client profiles
- **Client Profiles**: Connection and messaging profiles
- **ACL Profiles**: Access control lists
- **Subscriptions**: Queue topic subscriptions with multiple topic subscriptions

### Delete Operations
- All object types except subscriptions

## Configuration Structure

- `config/system.yaml` - System-wide settings and SEMP configuration
- `config/defaults/` - Default object templates
- `inventory/` - Broker connection details by environment
- `input/` - User input files (YAML/CSV formats)

## Operational Tasks

### Environment Management
- **Development**: Use `input/nram/nram-dev.yaml` and `inventory/nram/nram-local.yaml`
- **Testing**: Use `input/nram/nram-test.yaml` and `inventory/nram/nram-cloud.yaml`
- **Production**: Use `input/nt/` files and `inventory/nt/nt-sys.yaml`

### Logging
- Logs written to `logs/` directory with timestamp
- Use `-v`, `-vv`, or `-vvv` for increasing verbosity levels

### Batch Processing
The tool handles object dependencies automatically:
1. Dead message queues created before regular queues
2. Client/ACL profiles created before client usernames
3. JNDI mappings auto-generated for queues

### Error Handling
- Objects are skipped if they already exist (configurable)
- Failed operations logged with detailed error messages
- System continues processing remaining objects on individual failures

## Limitations

- No support for object property updates
- Subscription deletion not implemented
- Limited to supported Solace object types (queues, client usernames, profiles)
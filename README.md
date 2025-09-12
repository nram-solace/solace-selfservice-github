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
python3 scripts/yaml_to_semp.py --input input/yaml/test.yaml
```

### CSV Input
Convert CSV files to YAML format first:
```bash
python3 scripts/csv_to_yaml.py --csv-file input/csv/queues.csv
bash scripts/solace_self_service.sh  # Process all CSV files
```

**CSV Format Support:**
- **Single entries**: Automatically converted to lists (e.g., `topic1` → `["topic1"]`)
- **Multiple entries**: Comma-separated values (e.g., `topic1,topic2` → `["topic1", "topic2"]`)
- **Exception fields**: `clientConnectExceptions`, `publishTopicExceptions`, `subscribeTopicExceptions` are always treated as lists

## Supported Operations

### Create Operations
- **Queues**: Regular and dead message queues with JNDI mappings
- **Client Usernames**: With associated ACL and client profiles
- **Client Profiles**: Connection and messaging profiles
- **ACL Profiles**: Access control lists
- **Subscriptions**: Queue topic subscriptions with multiple topic subscriptions

### Delete Operations
- All object types except subscriptions

## GitHub Actions Integration

Automated workflows trigger on CSV file changes:

### Available Workflows
- **`process-queues-csv.yml`**: Processes queue configurations when `input/csv/queues.csv` changes
- **`process-client-usernames-csv.yml`**: Processes client username configurations when `input/csv/client-usernames.csv` changes  
- **`process-acl-profiles-csv.yml`**: Processes ACL profile configurations when `input/csv/acl-profiles.csv` changes

### Workflow Features
- Automatic CSV to YAML conversion
- Sequential processing of related configurations (ACL → Client Profiles → Client Usernames)
- Environment variable support for SEMP authentication
- Comprehensive logging and error handling

### Setup Requirements
- GitHub repository secrets: `SEMP_PASSWORD`
- Optional: GitHub repository variables for `SEMP_USER`
- Workflow permissions: `workflow` scope required for Personal Access Tokens

## Configuration Structure

- `config/system.yaml` - System-wide settings and SEMP configuration
- `config/defaults/` - Default object templates
- `inventory/` - Broker connection details by environment
- `input/` - User input files (YAML/CSV formats)
- `.github/workflows/` - GitHub Actions automation workflows

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

## Recent Improvements

### Version 2.5.0+ Updates
- **Enhanced CSV Parsing**: Fixed single entry handling for exception fields
- **GitHub Actions Workflows**: Automated CSV processing with workflow triggers
- **Improved Error Handling**: Better debugging and verbose output options
- **Field Validation**: Enhanced validation for CSV input fields
- **Inventory Mapping**: Support for inventory key to VPN name mapping

### CSV Parsing Fixes
- Single topic exceptions now correctly formatted as lists
- Character list detection and correction for malformed CSV data
- Automatic list wrapping for exception fields (`clientConnectExceptions`, `publishTopicExceptions`, `subscribeTopicExceptions`)

## Limitations

- No support for object property updates
- Subscription deletion not implemented
- Limited to supported Solace object types (queues, client usernames, profiles)
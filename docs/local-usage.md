# Local Usage

Running the automation from the shell (outside of GitHub Actions).

| This was tested on MacOS and Linux. Not tested on Windows with WSL.

## Prerequisites

- Python 3.6+
- Solace PubSub+ broker access with SEMPv2 enabled
- Broker password configured (see Password Management)

## Installation

### Virtual env setup
This is optional, but recommended.

```
python3 -m venv venv
source venv/bin/activate
```

### Install required modules.

```bash
pip install -r requirements.txt
```

## Wrapper Script (Recommended)

The wrapper script runs the full CSV → YAML → SEMP pipeline in one command:

```bash
bash scripts/solace_self_service.sh --csv-file input/csv/sample/dev/queues-team1.csv --verbose
```

The environment is derived from the CSV path (`input/csv/<client>/<env>/<object>-<app>.csv`); `--env` is optional and only validated against the path.

## Two-Step Process

Run CSV conversion and SEMP operations separately:

```bash
# Step 1: Convert CSV to YAML
python3 scripts/csv_to_yaml.py --csv-file input/csv/sample/dev/queues-team1.csv

# Step 2: Apply YAML to broker via SEMP
python3 scripts/yaml_to_semp.py --input input/yaml/sample/dev/queues-team1.yaml -v
```

## YAML-Only (Skip CSV Conversion)

Process a hand-authored or pre-existing YAML file directly:

```bash
python3 scripts/yaml_to_semp.py --input input/yaml/queues.yaml -v
```

## Authentication

Set the broker password before running:

```bash
# Option 1: Environment variable (fallback for hosts without inventory passwords)
export SEMP_PASSWORD=your_broker_password

# Option 2: Encrypted password in inventory (recommended)
export PASSWORD_ENC_KEY="your-secret-key"
```

See [Password Management](password-management.md) for details.

## Verbosity

Use `-v` flags for increasing verbosity levels:

- `-v` — INFO level
- `-vv` — DEBUG level
- `-vvv` — TRACE level

```bash
bash scripts/solace_self_service.sh --csv-file input/csv/sample/dev/queues-team1.csv -vvv
```

Logs are written to the `logs/` directory with timestamps.

## Local Development with Docker

A Docker Compose setup is available for local testing with a Solace PubSub+ broker:

```bash
cd docker && docker compose up -d
```

The init container automatically provisions per-team VPNs (e.g., `test1-dev-vpn`, `test1-uat-vpn` for team1). See `docker/docker-compose.yaml` for details.
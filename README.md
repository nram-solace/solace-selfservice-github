# Solace PubSub+ Self Service with Github Actions

Github Actions based automation tool for provisioning Solace PubSub+ infrastructure using SEMPv2 API. 

- Supports creation of list of objects with custom properties from CSV files.
- Supports multi-team isolation with per-team directories.
- GitHub Actions workflow integration with manual workflow runs.
- Automatic detection of team and env based on pre-defined folder and file naming.
- Central inventory files with broker and access info for all environments.

## Prerequisites

- Python 3.6+
- Solace PubSub+ broker access with SEMPv2 enabled
- Broker password configured (see [Password Management](docs/password-management.md))


## Github Actions Workflow

1. User creates a feature branch (e.g., `feat/team1-queues`)
2. User creates or updates a CSV file with the list of objects and their properties.
   For example, to create queues in dev for team1, create/update:
   `input/csv/team1/queues-dev.csv` (see `input/csv/sample/queues-dev.csv` for format)
3. User commits and pushes to GitHub
4. The push triggers the corresponding GitHub Actions workflow automatically
   - Workflows fire on **feature branches only** (`branches-ignore: [main, master]`)
   - Path filters ensure only matching CSV files trigger each workflow (e.g., `input/csv/**/queues-*.csv`)
   - Environment is extracted from the CSV filename (e.g., `queues-dev.csv` → `dev`)
   - If multiple CSV files change in one push, all are processed in a single workflow run
5. GitHub Actions workflow will:
   1. Checkout the code
   2. Detect changed CSV files via `git diff` (push) or use the provided input (manual dispatch)
   3. Extract team from the CSV directory path (`input/csv/<team>/...`)
   4. Extract environment from the CSV filename suffix (`queues-dev.csv` → `dev`)
   5. Run `solace_self_service.sh` for each file: CSV → YAML → SEMPv2 broker operations
   6. Post a summary to GitHub step summary with trigger type, files processed, branch, and commit

Workflows can also be triggered manually via `workflow_dispatch` with explicit `csv_file` and `environment` inputs.

## Workflows and Triggers

All workflows support **dual-mode triggering**: automatic on push (feature branches only) and manual via `workflow_dispatch`.

| Workflow | Push trigger path filter | Manual dispatch inputs |
| -------- | ------------------------ | ---------------------- |
| `process-queues-csv.yml` | `input/csv/**/queues-*.csv` | `csv_file`, `environment` |
| `process-acl-profiles-csv.yml` | `input/csv/**/acl-profiles-*.csv` | `csv_file`, `environment` |
| `process-client-usernames-csv.yml` | `input/csv/**/client-usernames-*.csv`, `input/csv/**/client-profiles-*.csv` | `csv_file` (team dir), `environment` |

**Push (automatic):**

- Fires on feature branches only (`branches-ignore: [main, master]`)
- Detects changed CSV files via `git diff --diff-filter=ACM HEAD~1`
- Extracts environment from CSV filename suffix (e.g., `queues-dev.csv` → `dev`)
- Processes all matching changed files in a single run (multi-file support)
- Client-usernames workflow deduplicates by `(team_dir, env)` pair before running the dependency chain

**Manual (`workflow_dispatch`):**

- Works on any branch including main/master
- Requires explicit `csv_file` path and `environment` inputs
- Useful for re-runs, production deployments, or branches without push-trigger paths

### Setup Requirements

- GitHub repository secrets: `SEMP_PASSWORD` (or `PASSWORD_ENC_KEY` if using encrypted passwords in inventory)
- Optional: GitHub repository variables for `SEMP_USER`

## Object dependencies

The tool handles object dependencies automatically:

1. Dead message queues created before regular queues
2. Client/ACL profiles created before client usernames
3. JNDI mappings for Queues handled automatically based on `jndiQueueName` field
4. Topic subscriptions added after queue creation

## Error Handling

- Objects are skipped if they already exist (ALREADY_EXISTS treated as success)
- Failed operations logged with detailed error messages
- System continues processing remaining objects on individual failures

## Limitations

- No support for object property updates (create/delete only)
- Subscription deletion not implemented
- Limited to supported Solace object types (queues, client usernames, profiles)
- No built-in backup/rollback functionality

## Other Documentation

| Topic | Description |
| ----- | ----------- |
| [Password Management](docs/password-management.md) | Password priority, encryption CLI, inventory examples |
| [Team Setup](docs/team-setup.md) | Multi-team directory layout, team onboarding, configuration structure |
| [Inventory Setup](docs/inventory-setup.md) | Inventory file format, required fields, password fields, resolution flow |
| [Input files](docs/input-formats.md) | CSV and YAML input formats, supported operations, queue features |
| [Local Usage](docs/local-usage.md) | Running from shell, wrapper script, two-step process, verbosity |

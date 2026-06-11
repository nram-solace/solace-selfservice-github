# Solace PubSub+ Self Service with Github Actions

Github Actions based automation tool for provisioning Solace PubSub+ infrastructure using SEMPv2 API. 

- Supports creation of list of objects with custom properties from CSV files.
- Supports multi-app isolation with per-client/per-environment directories.
- GitHub Actions workflow integration with manual workflow runs.
- Automatic detection of client, env and app based on pre-defined folder and file naming
  (`input/csv/<client>/<env>/<object>-<app>.csv`).
- One inventory file per environment (`inventory/<client>/<env>.yml`) keyed by app.

## Prerequisites

- Python 3.6+
- Solace PubSub+ broker access with SEMPv2 enabled
- Broker password configured (see [Password Management](docs/password-management.md))


## Github Actions Workflow

Provisioning is **approval-gated**: changes are validated on a pull request and
applied to a broker only after the PR is merged into a protected **environment
branch** (`dev`, `int`, `sys`, `uat`, `prod`).

1. App team creates a feature branch (e.g., `feat/xyz-queues`)
2. App team creates or updates a CSV file under the client/environment directory,
   using the app name as the filename suffix. For example, to create queues in
   `sys` for app xyz, create/update:
   `input/csv/<client>/sys/queues-xyz.csv` (see `input/csv/sample/dev/queues-team1.csv` for format)
3. App team commits and pushes to the feature branch (no broker change occurs)
4. App team opens a **pull request into the target environment branch** (e.g. `sys`)
   - The `validate-csv-pr` workflow runs CSV → YAML validation only (headers,
     valid-tags, path layout, inventory lookup). It uses **no SEMP secrets** and
     does **not** touch a broker.
   - Validation warns if a file's env directory does not match the PR base branch.
5. Reviewers (EMS / platform team) review the diff and validation results, then
   approve and merge the PR.
6. The merge **pushes to the environment branch**, which triggers the matching
   provisioning workflow automatically:
   1. Checkout the code
   2. Detect changed CSV files via `git diff`
   3. Extract environment from the CSV directory path (`input/csv/<client>/<env>/...`)
   4. Extract app from the CSV filename suffix (`queues-xyz.csv` → `xyz`)
   5. **Branch/env guard**: skip any file whose env directory does not match the branch
   6. Run `solace_self_service.sh` for each file: CSV → YAML → SEMPv2 broker operations
   7. Post a summary to GitHub step summary with trigger type, files processed, branch, and commit

Provisioning workflows can also be triggered manually via `workflow_dispatch`
with an explicit `csv_file` input (operator-driven; the environment is derived
from the CSV path and the branch/env guard is not enforced for manual runs).

## Workflows and Triggers

| Workflow | Trigger | Path filter |
| -------- | ------- | ----------- |
| `validate-csv-pr.yml` | `pull_request` into `dev`/`int`/`sys`/`uat`/`prod` | `input/csv/**` |
| `process-queues-csv-NRAM.yml` | `push` to env branches + `workflow_dispatch` | `input/csv/NRAM/**/queues-*.csv` |
| `process-queues-csv-nt.yml` | `push` to env branches + `workflow_dispatch` | `input/csv/NT/**/queues-*.csv` |
| `process-acl-profiles-csv.yml` | `push` to env branches + `workflow_dispatch` | `input/csv/**/acl-profiles-*.csv` |
| `process-client-usernames-csv.yml` | `push` to env branches + `workflow_dispatch` | `input/csv/**/client-usernames-*.csv`, `input/csv/**/client-profiles-*.csv` |

**Validation (`pull_request`):**

- Runs on PRs into environment branches (`branches: [dev, int, sys, uat, prod]`)
- Validates changed CSVs via `csv_to_yaml.py` only — no broker calls, no secrets
- Fails the PR check on invalid CSVs; warns on env/branch mismatch

**Provisioning (push to environment branch):**

- Fires only on push to `dev`, `int`, `sys`, `uat`, `prod` (i.e. on merge)
- Detects changed CSV files via `git diff`
- Extracts environment from the CSV directory path (`input/csv/<client>/<env>/...`)
  and app from the filename suffix (e.g., `queues-xyz.csv` → `xyz`)
- Skips files whose env directory does not match the branch (branch/env guard)
- Processes all matching changed files in a single run (multi-file support)
- Client-usernames workflow deduplicates by `(env_dir, app)` pair before running the dependency chain

**Manual (`workflow_dispatch`):**

- Works on any branch, including environment branches
- Requires an explicit `csv_file` path (env derived from the path); the
  client-usernames workflow takes `csv_dir` and `app` inputs
- Useful for re-runs or operator-driven deployments; branch/env guard not enforced

### Setup Requirements

- GitHub repository secrets: `SEMP_PASSWORD` (or `PASSWORD_ENC_KEY` if using encrypted passwords in inventory)
- Optional per-environment secrets: `SEMP_<ENV>_PASSWORD` (e.g. `SEMP_SYS_PASSWORD`,
  `SEMP_PROD_PASSWORD`). When set, the deploy uses the env-specific password for that
  environment; otherwise it falls back to `SEMP_PASSWORD`. See
  [docs/password-management.md](docs/password-management.md).
- Optional: GitHub repository variables for `SEMP_USER`
- Protected environment branches (`dev`, `int`, `sys`, `uat`, `prod`) with required PR
  reviews and (recommended) the `validate-csv-pr` status check required before merge

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
| [App Setup](docs/team-setup.md) | Per-client/env directory layout, app onboarding, configuration structure |
| [Inventory Setup](docs/inventory-setup.md) | Per-environment inventory format, required fields, password fields, resolution flow |
| [Input files](docs/input-formats.md) | CSV and YAML input formats, supported operations, queue features |
| [Local Usage](docs/local-usage.md) | Running from shell, wrapper script, two-step process, verbosity |

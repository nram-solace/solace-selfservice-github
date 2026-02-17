#!/bin/bash
#
# Solace Self Service Script
# Takes absolute path of CSV file, converts to YAML, and processes with yaml_to_semp
#
# Usage:
#     ./scripts/solace_self_service.sh --csv-file <path/to/file.csv> --env <environment> [--verbose]
#
# Example:
#     ./scripts/solace_self_service.sh --csv-file input/csv/queues.csv --env dev --verbose
#     ./scripts/solace_self_service.sh --csv-file input/csv/team1/queues.csv --env uat --verbose
#

set -e  # Exit on any error

# Script configuration
SCRIPT_PREFIX="Solace_Self_Service"
VERSION="2.5.2-1009"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

# Color-coded prefixes for different components
WRAPPER_COLOR=$BLUE
CSV2YAML_COLOR=$MAGENTA
YAML2SEMP_COLOR=$CYAN

# Logging function
log() {
    echo -e "${WRAPPER_COLOR}[${SCRIPT_PREFIX}]${NC} $1"
}

error() {
    echo -e "${RED}[${SCRIPT_PREFIX}] ERROR:${NC} $1" >&2
}

success() {
    echo -e "${GREEN}[${SCRIPT_PREFIX}]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[${SCRIPT_PREFIX}] WARNING:${NC} $1"
}

# Note: Colorization is handled directly in the Python scripts
# Scripts: csv_to_yaml.py and yaml_to_semp.py

# Parse command line arguments
CSV_FILE=""
ENV_VALUE=""
VERBOSE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --csv-file)
            CSV_FILE="$2"
            shift 2
            ;;
        --env)
            ENV_VALUE="$2"
            shift 2
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 --csv-file <csv-file> --env <environment> [--verbose]"
            echo ""
            echo "Arguments:"
            echo "  --csv-file    Path to CSV file to process"
            echo "  --env         Target environment (inventory host name, e.g., dev, uat, prod)"
            echo "  --verbose     Enable verbose output"
            echo "  -h, --help    Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0 --csv-file input/csv/queues.csv --env dev"
            echo "  $0 --csv-file input/csv/team1/queues.csv --env uat --verbose"
            exit 0
            ;;
        *)
            error "Unknown option: $1"
            echo "Use -h or --help for usage information"
            exit 1
            ;;
    esac
done

# Validate required arguments
if [[ -z "$CSV_FILE" ]]; then
    error "CSV file path is required. Use --csv-file <path>"
    exit 1
fi

if [[ -z "$ENV_VALUE" ]]; then
    error "Environment is required. Use --env <environment>"
    exit 1
fi


# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Change to project root
cd "$PROJECT_ROOT"

# Validate CSV file
if [[ ! -f "$CSV_FILE" ]]; then
    error "CSV file not found: $CSV_FILE"
    exit 1
fi

if [[ ! "$CSV_FILE" =~ \.csv$ ]]; then
    error "File must have .csv extension: $CSV_FILE"
    exit 1
fi

log "Version $VERSION"
log "Processing CSV file: $CSV_FILE"
log "Target environment: $ENV_VALUE"
log "Project root: $PROJECT_ROOT"

# Step 1: Convert CSV to YAML
log "Step 1: Converting CSV to YAML..."

CSV_TO_YAML_CMD=(
    python3 "$SCRIPT_DIR/csv_to_yaml.py"
    --csv-file "$CSV_FILE"
    --env "$ENV_VALUE"
)

if [[ "$VERBOSE" == "true" ]]; then
    CSV_TO_YAML_CMD+=(--verbose)
fi

log "Running: ${CSV_TO_YAML_CMD[*]}"

if ! "${CSV_TO_YAML_CMD[@]}"; then
    error "CSV to YAML conversion failed"
    exit 1
fi

# Step 2: Generate YAML file path
CSV_DIR="$(dirname "$CSV_FILE")"
CSV_BASENAME="$(basename "$CSV_FILE" .csv)"
YAML_DIR="$(echo "$CSV_DIR" | sed 's/csv/yaml/g')"
YAML_FILE="$YAML_DIR/$CSV_BASENAME.yaml"

# Ensure YAML directory exists
mkdir -p "$YAML_DIR"

if [[ ! -f "$YAML_FILE" ]]; then
    error "Generated YAML file not found: $YAML_FILE"
    exit 1
fi

log "Generated YAML file: $YAML_FILE"

# Step 3: Process with solace-service-manager
log "Step 3: Processing with solace-service-manager..."

SOLACE_CMD=(
    python3 "$SCRIPT_DIR/yaml_to_semp.py"
    --input "$YAML_FILE"
)

if [[ "$VERBOSE" == "true" ]]; then
    SOLACE_CMD+=(--verbose)
fi

log "Running: ${SOLACE_CMD[*]}"

if ! "${SOLACE_CMD[@]}"; then
    error "Solace service manager processing failed"
    exit 1
fi

success "Processing completed successfully!" 
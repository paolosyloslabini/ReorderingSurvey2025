#!/usr/bin/env bash
# load_modules.sh - Load modules based on technique configuration
# Usage: source load_modules.sh <technique_type> <technique_name>
#   technique_type: "reorder" or "multiply"
#   technique_name: name of the technique (e.g. "rcm", "cucsrspmm")

set -euo pipefail

if [[ $# -ne 2 ]]; then
    echo "Usage: source $0 <technique_type> <technique_name>" >&2
    return 1 2>/dev/null || exit 1
fi

TECHNIQUE_TYPE="$1"
TECHNIQUE_NAME="$2"

# Ensure PROJECT_ROOT is set
if [[ -z "${PROJECT_ROOT:-}" ]]; then
    export PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
fi

# Determine config file based on technique type
case "$TECHNIQUE_TYPE" in
    "reorder")
        CONFIG_FILE="$PROJECT_ROOT/config/reorder.yml"
        ;;
    "multiply")
        CONFIG_FILE="$PROJECT_ROOT/config/multiply.yml"
        ;;
    *)
        echo "Error: Unknown technique type '$TECHNIQUE_TYPE'. Must be 'reorder' or 'multiply'." >&2
        return 1 2>/dev/null || exit 1
        ;;
esac

if [[ ! -f "$CONFIG_FILE" ]]; then
    echo "Error: Configuration file $CONFIG_FILE not found" >&2
    return 1 2>/dev/null || exit 1
fi

# Check if yq is available, otherwise try python yaml parsing
if command -v yq >/dev/null 2>&1; then
    MODULE_SET=$(yq eval ".[\"$TECHNIQUE_NAME\"].modules // \"basic\"" "$CONFIG_FILE")
else
    # Fallback to python for YAML parsing
    MODULE_SET=$(python3 -c "
import yaml, sys
try:
    with open('$CONFIG_FILE', 'r') as f:
        config = yaml.safe_load(f)
    print(config.get('$TECHNIQUE_NAME', {}).get('modules', 'basic'))
except Exception as e:
    print('basic')
")
fi

# Remove quotes if present
MODULE_SET=$(echo "$MODULE_SET" | tr -d '"')

if [[ "$MODULE_SET" == "null" || -z "$MODULE_SET" ]]; then
    MODULE_SET="basic"
fi

echo "Loading module set: $MODULE_SET for technique $TECHNIQUE_NAME" >&2

# Load module configuration
MODULE_CONFIG="$PROJECT_ROOT/config/modules/${MODULE_SET}.yml"
if [[ ! -f "$MODULE_CONFIG" ]]; then
    echo "Warning: Module configuration $MODULE_CONFIG not found, using basic" >&2
    MODULE_CONFIG="$PROJECT_ROOT/config/modules/basic.yml"
fi

# Function to load modules if module command is available
load_modules_if_available() {
    if command -v module >/dev/null 2>&1; then
        echo "Module system detected, loading modules..." >&2
        
        # Parse and load modules from config
        if command -v yq >/dev/null 2>&1; then
            yq eval '.modules[]' "$MODULE_CONFIG" | while read -r mod; do
                echo "  Loading module: $mod" >&2
                module load "$mod" || echo "    Warning: Failed to load module $mod" >&2
            done
        else
            python3 -c "
import yaml
with open('$MODULE_CONFIG', 'r') as f:
    config = yaml.safe_load(f)
for mod in config.get('modules', []):
    print(mod)
" | while read -r mod; do
                echo "  Loading module: $mod" >&2
                module load "$mod" || echo "    Warning: Failed to load module $mod" >&2
            done
        fi
    else
        echo "No module system available, skipping module loading" >&2
    fi
}

# Function to set environment variables
set_environment() {
    echo "Setting environment variables..." >&2
    
    if command -v yq >/dev/null 2>&1; then
        # Use yq to extract environment variables
        yq eval '.environment | to_entries | .[] | .key + "=" + .value' "$MODULE_CONFIG" 2>/dev/null | while IFS='=' read -r key value; do
            # Expand variables in the value, using set +u to handle unset variables
            set +u
            expanded_value=$(eval echo "$value")
            set -u
            export "$key"="$expanded_value"
            echo "  $key=$expanded_value" >&2
        done
    else
        # Use python to extract environment variables
        python3 -c "
import yaml, os
with open('$MODULE_CONFIG', 'r') as f:
    config = yaml.safe_load(f)
env_vars = config.get('environment', {})
for key, value in env_vars.items():
    # Simple variable expansion with fallback for missing vars
    try:
        expanded_value = os.path.expandvars(str(value))
    except:
        expanded_value = str(value)
    os.environ[key] = expanded_value
    print(f'{key}={expanded_value}')
" | while IFS='=' read -r key value; do
            export "$key"="$value"
            echo "  $key=$value" >&2
        done
    fi
}

# Function to run post-load commands
run_post_load() {
    echo "Running post-load verification..." >&2
    
    if command -v yq >/dev/null 2>&1; then
        yq eval '.post_load[]' "$MODULE_CONFIG" 2>/dev/null | while read -r cmd; do
            if [[ -n "$cmd" && "$cmd" != "null" ]]; then
                echo "  Running: $cmd" >&2
                eval "$cmd" || echo "    Warning: Command failed: $cmd" >&2
            fi
        done
    else
        python3 -c "
import yaml
with open('$MODULE_CONFIG', 'r') as f:
    config = yaml.safe_load(f)
for cmd in config.get('post_load', []):
    print(cmd)
" | while read -r cmd; do
            if [[ -n "$cmd" ]]; then
                echo "  Running: $cmd" >&2
                eval "$cmd" || echo "    Warning: Command failed: $cmd" >&2
            fi
        done
    fi
}

# Execute the module loading process
load_modules_if_available
set_environment  
run_post_load

echo "Module loading completed for $TECHNIQUE_TYPE/$TECHNIQUE_NAME" >&2
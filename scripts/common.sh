#!/bin/bash
# Common utilities for demo scripts

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_header() {
    echo -e "${BLUE}"
    echo "════════════════════════════════════════════════════════════"
    echo "$1"
    echo "════════════════════════════════════════════════════════════"
    echo -e "${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Check for required commands
require_cmd() {
    for cmd in "$@"; do
        if ! command -v "$cmd" &> /dev/null; then
            print_error "Required command not found: $cmd"
            case "$cmd" in
                opa) echo "  Install with: brew install opa" ;;
                jq) echo "  Install with: brew install jq" ;;
                python3) echo "  Install with: brew install python3" ;;
                git) echo "  Install with: brew install git" ;;
            esac
            exit 1
        fi
    done
}

# Check if inside git repository
require_git_repo() {
    if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
        print_error "Not inside a git repository"
        exit 1
    fi
}

# Get OPA deny violations length safely
opa_deny_len() {
    local result_file="$1"
    jq -r '(.result[0].expressions[0].value // []) | length' "$result_file"
}

# Print OPA policy result
print_policy_result() {
    local policy_name="$1"
    local violations="$2"
    local result_file="$3"
    
    if [ "$violations" -eq 0 ]; then
        print_success "✓ $policy_name"
        return 0
    else
        print_error "✗ $policy_name - $violations violation(s)"
        jq -r '(.result[0].expressions[0].value // [])[]' "$result_file" 2>/dev/null | while read -r line; do
            echo "    → $line"
        done
        return 1
    fi
}

# Interactive prompt that respects CI mode
interactive_prompt() {
    if [ "${CI:-}" != "true" ] && [ "${NON_INTERACTIVE:-}" != "true" ]; then
        read -r -p "$1"
    fi
}

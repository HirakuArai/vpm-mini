#!/bin/bash
set -euo pipefail

# Autopilot L1 - Limited Autonomous Loop
# Purpose: Safe, constrained autonomous improvements in low-risk areas

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Configuration
PROJECT="vpm-mini"
MAX_CHANGES=3
DRY_RUN=true
TARGET_AREAS="docs,comments"
OUTPUT_JSON=""
APPLY_CHANGES=false

# Allowlisted file patterns for safe changes
ALLOWLIST_DOCS=(
    "*.md"
    "docs/**"
    "README*"
    "CHANGELOG*"
    "LICENSE*"
)

ALLOWLIST_COMMENTS=(
    "*.py"
    "*.js"
    "*.ts"
    "*.yaml"
    "*.yml"
    "*.sh"
)

ALLOWLIST_FORMATTING=(
    "*.py"
    "*.js"
    "*.ts"
    "*.json"
    "*.yaml"
    "*.yml"
)

# Scan results
declare -a CHANGES=()
CHANGES_COUNT=0

log() {
    echo "[autopilot-l1] $*" >&2
}

usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Options:
    --project NAME       Project namespace (default: vpm-mini)
    --max-changes N      Maximum number of changes to make (default: 3)
    --dry-run BOOL       Dry run mode - no actual changes (default: true)
    --target-areas LIST  Comma-separated areas: docs,comments,formatting (default: docs,comments)
    --output-json FILE   Output scan results to JSON file
    --apply-changes      Apply the changes (requires dry-run=false)
    --help              Show this help

Examples:
    $0 --project=other-sample --dry-run=true --max-changes=5
    $0 --target-areas=docs,formatting --apply-changes
EOF
    exit 1
}

parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --project=*)
                PROJECT="${1#*=}"
                shift
                ;;
            --max-changes=*)
                MAX_CHANGES="${1#*=}"
                shift
                ;;
            --dry-run=*)
                DRY_RUN="${1#*=}"
                shift
                ;;
            --target-areas=*)
                TARGET_AREAS="${1#*=}"
                shift
                ;;
            --output-json=*)
                OUTPUT_JSON="${1#*=}"
                shift
                ;;
            --apply-changes)
                APPLY_CHANGES=true
                shift
                ;;
            --help)
                usage
                ;;
            *)
                log "Unknown option: $1"
                usage
                ;;
        esac
    done
}

add_change() {
    local type="$1"
    local file="$2"
    local description="$3"

    if [[ $CHANGES_COUNT -ge $MAX_CHANGES ]]; then
        log "Maximum changes ($MAX_CHANGES) reached, skipping: $description"
        return 1
    fi

    CHANGES+=("{\"type\":\"$type\",\"file\":\"$file\",\"description\":\"$description\"}")
    ((CHANGES_COUNT++))
    log "Change $CHANGES_COUNT/$MAX_CHANGES: $type in $file - $description"
    return 0
}

is_file_allowed() {
    local file="$1"
    local area="$2"

    case "$area" in
        docs)
            for pattern in "${ALLOWLIST_DOCS[@]}"; do
                if [[ "$file" == $pattern ]]; then
                    return 0
                fi
            done
            ;;
        comments)
            for pattern in "${ALLOWLIST_COMMENTS[@]}"; do
                if [[ "$file" == $pattern ]]; then
                    return 0
                fi
            done
            ;;
        formatting)
            for pattern in "${ALLOWLIST_FORMATTING[@]}"; do
                if [[ "$file" == $pattern ]]; then
                    return 0
                fi
            done
            ;;
    esac
    return 1
}

scan_docs_improvements() {
    log "Scanning for documentation improvements..."

    # Find README files without proper headers
    while IFS= read -r -d '' file; do
        if [[ ! -s "$file" ]]; then continue; fi

        local relative_file="${file#$REPO_ROOT/}"
        if ! is_file_allowed "$relative_file" "docs"; then continue; fi

        # Check if README lacks a title
        if [[ "$(basename "$file")" =~ ^README ]]; then
            if ! head -1 "$file" | grep -q "^#"; then
                add_change "docs" "$relative_file" "Add title header to README" || break
            fi
        fi

        # Check for TODOs that should be in proper format
        if grep -q "TODO:" "$file"; then
            if ! grep -q "## TODO" "$file"; then
                add_change "docs" "$relative_file" "Convert TODO comments to proper TODO section" || break
            fi
        fi

    done < <(find "$REPO_ROOT" -name "*.md" -type f -print0)
}

scan_comment_improvements() {
    log "Scanning for comment improvements..."

    # Find files with missing function docstrings
    while IFS= read -r -d '' file; do
        local relative_file="${file#$REPO_ROOT/}"
        if ! is_file_allowed "$relative_file" "comments"; then continue; fi

        case "$file" in
            *.py)
                # Check for functions without docstrings
                if grep -q "^def " "$file" && ! grep -q '"""' "$file"; then
                    add_change "comments" "$relative_file" "Add missing function docstrings" || break
                fi
                ;;
            *.sh)
                # Check for scripts without description comments
                if ! head -5 "$file" | grep -q "^#.*Purpose\|^#.*Description"; then
                    add_change "comments" "$relative_file" "Add script purpose comment" || break
                fi
                ;;
            *.js|*.ts)
                # Check for functions without JSDoc
                if grep -q "^function\|^const.*=.*function" "$file" && ! grep -q "/\*\*" "$file"; then
                    add_change "comments" "$relative_file" "Add JSDoc comments to functions" || break
                fi
                ;;
        esac

    done < <(find "$REPO_ROOT" -type f \( -name "*.py" -o -name "*.js" -o -name "*.ts" -o -name "*.sh" \) -print0)
}

scan_formatting_improvements() {
    log "Scanning for formatting improvements..."

    # Find files with trailing whitespace
    while IFS= read -r -d '' file; do
        local relative_file="${file#$REPO_ROOT/}"
        if ! is_file_allowed "$relative_file" "formatting"; then continue; fi

        if grep -q "[[:space:]]$" "$file"; then
            add_change "formatting" "$relative_file" "Remove trailing whitespace" || break
        fi

        # Check for inconsistent indentation in YAML
        if [[ "$file" == *.yaml || "$file" == *.yml ]]; then
            if grep -q $'^\t' "$file"; then
                add_change "formatting" "$relative_file" "Convert tabs to spaces in YAML" || break
            fi
        fi

    done < <(find "$REPO_ROOT" -type f \( -name "*.py" -o -name "*.js" -o -name "*.ts" -o -name "*.json" -o -name "*.yaml" -o -name "*.yml" \) -print0)
}

apply_docs_improvements() {
    log "Applying documentation improvements..."

    for change in "${CHANGES[@]}"; do
        local type=$(echo "$change" | python3 -c "import json,sys; print(json.load(sys.stdin)['type'])")
        local file=$(echo "$change" | python3 -c "import json,sys; print(json.load(sys.stdin)['file'])")
        local desc=$(echo "$change" | python3 -c "import json,sys; print(json.load(sys.stdin)['description'])")

        if [[ "$type" != "docs" ]]; then continue; fi

        local full_path="$REPO_ROOT/$file"

        case "$desc" in
            "Add title header to README")
                local title="# $(basename "$(dirname "$file")" | tr '[:lower:]' '[:upper:]')"
                if [[ "$(basename "$file")" == "README.md" ]]; then
                    title="# $(basename "$REPO_ROOT")"
                fi
                sed -i.bak "1i\\
$title\\
" "$full_path"
                log "Added title header to $file"
                ;;
            "Convert TODO comments to proper TODO section")
                echo -e "\n## TODO\n\n$(grep "TODO:" "$full_path" | sed 's/.*TODO: */- /')" >> "$full_path"
                sed -i.bak '/TODO:/d' "$full_path"
                log "Converted TODO comments in $file"
                ;;
        esac
    done
}

apply_comment_improvements() {
    log "Applying comment improvements..."

    for change in "${CHANGES[@]}"; do
        local type=$(echo "$change" | python3 -c "import json,sys; print(json.load(sys.stdin)['type'])")
        local file=$(echo "$change" | python3 -c "import json,sys; print(json.load(sys.stdin)['file'])")
        local desc=$(echo "$change" | python3 -c "import json,sys; print(json.load(sys.stdin)['description'])")

        if [[ "$type" != "comments" ]]; then continue; fi

        local full_path="$REPO_ROOT/$file"

        case "$desc" in
            "Add script purpose comment")
                if [[ "$file" == *.sh ]]; then
                    local purpose="# Purpose: $(basename "$file" .sh) script"
                    sed -i.bak "2i\\
$purpose" "$full_path"
                    log "Added purpose comment to $file"
                fi
                ;;
        esac
    done
}

apply_formatting_improvements() {
    log "Applying formatting improvements..."

    for change in "${CHANGES[@]}"; do
        local type=$(echo "$change" | python3 -c "import json,sys; print(json.load(sys.stdin)['type'])")
        local file=$(echo "$change" | python3 -c "import json,sys; print(json.load(sys.stdin)['file'])")
        local desc=$(echo "$change" | python3 -c "import json,sys; print(json.load(sys.stdin)['description'])")

        if [[ "$type" != "formatting" ]]; then continue; fi

        local full_path="$REPO_ROOT/$file"

        case "$desc" in
            "Remove trailing whitespace")
                sed -i.bak 's/[[:space:]]*$//' "$full_path"
                log "Removed trailing whitespace from $file"
                ;;
            "Convert tabs to spaces in YAML")
                sed -i.bak 's/\t/  /g' "$full_path"
                log "Converted tabs to spaces in $file"
                ;;
        esac
    done
}

generate_output() {
    if [[ -n "$OUTPUT_JSON" ]]; then
        local changes_json="[]"
        if [[ ${#CHANGES[@]} -gt 0 ]]; then
            changes_json="[$(IFS=,; echo "${CHANGES[*]}")]"
        fi

        cat > "$OUTPUT_JSON" << EOF
{
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "project": "$PROJECT",
  "max_changes": $MAX_CHANGES,
  "changes_found": $CHANGES_COUNT,
  "target_areas": "$TARGET_AREAS",
  "dry_run": $DRY_RUN,
  "changes": $changes_json
}
EOF
        log "Results written to $OUTPUT_JSON"
    fi
}

main() {
    cd "$REPO_ROOT"

    log "Starting Autopilot L1 scan..."
    log "Config: project=$PROJECT, max_changes=$MAX_CHANGES, dry_run=$DRY_RUN, areas=$TARGET_AREAS"

    # Scan for improvements based on target areas
    IFS=',' read -ra AREAS <<< "$TARGET_AREAS"
    for area in "${AREAS[@]}"; do
        case "$area" in
            docs)
                scan_docs_improvements
                ;;
            comments)
                scan_comment_improvements
                ;;
            formatting)
                scan_formatting_improvements
                ;;
            *)
                log "Unknown target area: $area"
                ;;
        esac
    done

    log "Scan complete: found $CHANGES_COUNT changes (max: $MAX_CHANGES)"

    # Apply changes if requested and not in dry run
    if [[ "$APPLY_CHANGES" == "true" && "$DRY_RUN" == "false" ]]; then
        log "Applying changes..."

        for area in "${AREAS[@]}"; do
            case "$area" in
                docs)
                    apply_docs_improvements
                    ;;
                comments)
                    apply_comment_improvements
                    ;;
                formatting)
                    apply_formatting_improvements
                    ;;
            esac
        done

        # Clean up backup files
        find "$REPO_ROOT" -name "*.bak" -delete 2>/dev/null || true

        log "Changes applied successfully"
    else
        log "Dry run mode - no changes applied"
    fi

    generate_output

    log "Autopilot L1 complete"
}

# Parse arguments and run
parse_args "$@"
main
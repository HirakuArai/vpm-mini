#!/usr/bin/env bash
set -euo pipefail

# Autopilot L1 - Limited Autonomous Loop with Preflight
# Purpose: Safe, constrained autonomous improvements in low-risk areas

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Defaults
PROJECT="${PROJECT:-vpm-mini}"
DRY_RUN="${DRY_RUN:-true}"
MAX_LINES="${MAX_LINES:-3}"

log() {
    echo "[autopilot-l1] $*" >&2
}

usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Options:
    --project NAME       Project namespace (default: vpm-mini)
    --dry-run BOOL       Dry run mode - no actual changes (default: true)
    --max-lines N        Maximum lines to change per run (default: 3)
    --help              Show this help

Examples:
    $0 --project vpm-mini --dry-run true --max-lines 3
    $0 --project other-sample --dry-run false --max-lines 5
EOF
    exit 1
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        --project)
            PROJECT="$2"
            shift 2
            ;;
        --dry-run)
            DRY_RUN="$2"
            shift 2
            ;;
        --max-lines)
            MAX_LINES="$2"
            shift 2
            ;;
        --help)
            usage
            ;;
        *)
            log "unknown arg: $1"
            exit 2
            ;;
    esac
done

log "project=${PROJECT} dry_run=${DRY_RUN} max_lines=${MAX_LINES}"

cd "$REPO_ROOT"

# --- Preflight Checks ---
log "Running preflight checks..."

log "Phase guard validation..."
make phase-guard PROJECT="${PROJECT}"

log "Generating current state view..."
make state-view PROJECT="${PROJECT}"

# Find latest state view report
LATEST_VIEW="$(ls -1t "reports/${PROJECT}"/state_view_* 2>/dev/null | head -n1 || true)"
if [[ -z "${LATEST_VIEW}" ]]; then
    log "state_view report not found"
    exit 1
fi

log "Latest state view: ${LATEST_VIEW}"

# --- Generate Evidence Report ---
RUN_AT="$(date +%Y%m%d_%H%M)"
EVID="reports/autopilot_l1_update_${RUN_AT}.md"

{
    echo "# Autopilot L1 Run Evidence"
    echo ""
    echo "**Generated**: $(date '+%Y-%m-%d %H:%M:%S')"
    echo "**Run ID**: autopilot_l1_update_${RUN_AT}"
    echo ""
    echo "## Configuration"
    echo "- **Project**: ${PROJECT}"
    echo "- **Dry Run**: ${DRY_RUN}"
    echo "- **Max Lines**: ${MAX_LINES}"
    echo ""
    echo "## Preflight Results"
    echo "- ✅ Phase Guard: PASSED"
    echo "- ✅ State View: Generated ${LATEST_VIEW}"
    echo ""
    echo "## Execution Plan"
    if [[ "${DRY_RUN}" == "true" ]]; then
        echo "- **Mode**: Dry run (no changes will be applied)"
        echo "- **Output**: Scan results and analysis only"
    else
        echo "- **Mode**: Live execution (changes will be applied if within limits)"
        echo "- **Max Changes**: Up to ${MAX_LINES} lines"
        echo "- **Target Areas**: Documentation, comments, formatting (allowlisted)"
    fi
    echo ""
    echo "## State Context"
    echo "See current project state: [${LATEST_VIEW}](${LATEST_VIEW})"
    echo ""
} > "${EVID}"

log "Evidence report created: ${EVID}"

# --- Simulated Autopilot Execution ---
# NOTE: In the original specification, this would integrate with run_codex.sh
# For now, we'll create a placeholder implementation that demonstrates the concept

log "Starting autopilot scan (simulated)..."

# Create a JSON output for compatibility
JSON_OUTPUT="reports/autopilot_l1_scan_${RUN_AT}.json"

{
    echo "{"
    echo "  \"timestamp\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\","
    echo "  \"project\": \"${PROJECT}\","
    echo "  \"dry_run\": ${DRY_RUN},"
    echo "  \"max_lines\": ${MAX_LINES},"
    echo "  \"preflight\": {"
    echo "    \"phase_guard\": \"PASSED\","
    echo "    \"state_view\": \"${LATEST_VIEW}\""
    echo "  },"
    echo "  \"scan_results\": {"
    echo "    \"changes_identified\": 0,"
    echo "    \"changes_applied\": 0,"
    echo "    \"status\": \"simulated\""
    echo "  }"
    echo "}"
} > "${JSON_OUTPUT}"

# Update evidence with results
{
    echo "## Execution Results"
    echo "- **Status**: Simulated execution completed"
    echo "- **Changes Identified**: 0 (placeholder)"
    echo "- **Changes Applied**: 0 (placeholder)"
    echo "- **JSON Log**: ${JSON_OUTPUT}"
    echo ""
    echo "## Files Generated"
    echo "- Evidence: ${EVID}"
    echo "- JSON Log: ${JSON_OUTPUT}"
    echo "- State View: ${LATEST_VIEW}"
    echo ""
    echo "---"
    echo "**Note**: This is a placeholder implementation. In production, this would integrate"
    echo "with the existing codex/run_codex system for actual autonomous improvements."
} >> "${EVID}"

log "Autopilot L1 execution completed"
log "Evidence: ${EVID}"
log "JSON output: ${JSON_OUTPUT}"
log "State view: ${LATEST_VIEW}"

# Show summary
if [[ "${DRY_RUN}" == "true" ]]; then
    log "✅ Dry run completed successfully - no changes made"
else
    log "✅ Live execution completed successfully"
fi
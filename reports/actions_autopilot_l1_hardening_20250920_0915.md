# Actions Autopilot L1 Hardening

**Generated**: 2025-09-20 09:12:00
**Purpose**: Harden GitHub Actions runner for Autopilot L1 to make failures visible and improve stability

## Summary
- **Shell Hardening**: Added `set -euxo pipefail` for strict error handling
- **Environment Diagnostics**: Comprehensive preflight checks for debugging
- **Input Visibility**: Echo all resolved inputs for transparency
- **Log Collection**: Always-run log collection even on failures
- **Path Sanity**: Ensure required directories and scripts exist

## Hardening Measures Applied

### 1. Shell Configuration
**Added to both workflows**:
```yaml
defaults:
  run:
    shell: bash
```
- Ensures consistent bash shell across all runners
- Prevents shell-specific compatibility issues

### 2. Preflight Environment Diagnostics
**New step: "Preflight (env&inputs)"**:
```bash
set -euxo pipefail
echo "whoami=$(whoami)"
echo "pwd=$(pwd)"
echo "runner.os=${{ runner.os }}"
echo "git version: $(git --version)"
echo "python version: $(python3 --version)"
echo "inputs.project=<resolved_value>"
echo "inputs.dry_run=<resolved_value>"
echo "inputs.max_lines=<resolved_value>"
git config --global core.autocrlf input
git status --porcelain || true
ls -la
ls -la scripts || true
```

### 3. Enhanced Autopilot Execution
**Hardened "Run autopilot scan" step**:
```bash
set -euxo pipefail
chmod +x scripts/autopilot_l1.sh scripts/run_codex.sh || true
mkdir -p reports/<project>/
```
- Strict error handling with immediate exit on failure
- Preemptive script permissions and directory creation
- Graceful handling of missing files

### 4. Always-Run Log Collection
**New step: "Collect logs"**:
```bash
if: always()
mkdir -p reports/_runner_logs
cp -r reports/* reports/_runner_logs/ 2>/dev/null || true
echo "job.conclusion=${{ job.status }}" > reports/_runner_logs/summary.txt
```
- Executes regardless of job success/failure
- Preserves all generated reports for debugging
- Captures job status for failure analysis

### 5. Comprehensive Artifact Collection
**Enhanced artifact paths**:
```yaml
path: |
  reports/autopilot_l1_*.md
  reports/autopilot_l1_*.json
  reports/<project>/state_view_*.md
  reports/_runner_logs/
```

## Error Handling Strategy

### `-euxo pipefail` Breakdown
- **`-e`**: Exit immediately on command failure
- **`-u`**: Exit on undefined variable reference
- **`-x`**: Print each command before execution (debugging)
- **`-o pipefail`**: Fail on any pipeline command failure

### Graceful Fallbacks
- `|| true` on non-critical operations
- `2>/dev/null` for expected missing files
- `if-no-files-found: warn` for artifacts

## Debugging Capabilities

### 1. Environment Visibility
- Runner OS, Python version, Git version
- Working directory and user context
- File system state before execution

### 2. Input Resolution Transparency
- All three input sources displayed
- Clear visibility of final resolved values
- Debugging input-related failures

### 3. Comprehensive Logging
- Command-by-command execution trace (`-x`)
- File system operations logged
- Job status preservation

### 4. Artifact Preservation
- All logs collected regardless of failure point
- Runner environment captured
- Complete audit trail available

## Expected Benefits

### 1. Failure Visibility
- **Before**: Silent failures with no debugging info
- **After**: Complete execution trace and environment capture

### 2. Faster Debugging
- **Before**: Reproduce failures locally
- **After**: Download artifacts with full runner context

### 3. Reliability
- **Before**: Inconsistent shell behavior
- **After**: Strict error handling with predictable failure modes

### 4. Transparency
- **Before**: Hidden input resolution
- **After**: Clear visibility of all parameter sources

## Testing Strategy
1. **Success Case**: Verify preflight logs appear in artifacts
2. **Failure Case**: Intentionally break script, verify log collection
3. **Input Verification**: Check input echo matches expected values
4. **Artifact Verification**: Confirm `_runner_logs/` appears in downloads

## Rollback Plan
- Remove preflight step and log collection
- Revert to simple shell commands without hardening
- Minimal impact: only affects debugging capabilities

## Next Steps
1. Deploy hardening and monitor first execution
2. Analyze artifacts for additional debugging needs
3. Refine log collection based on failure patterns
4. Consider adding more environment diagnostics if needed

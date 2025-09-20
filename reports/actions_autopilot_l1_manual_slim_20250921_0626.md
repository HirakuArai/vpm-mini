# Manual Shim Simplified to Single Direct-Exec Job

**Generated**: 2025-09-21 06:26:00
**Purpose**: Eliminate workflow_call structural conflicts with single-job implementation

## Summary
- **Removed**: workflow_call usage and multi-job structure
- **Runner**: ubuntu-22.04, shell: bash (aligned with debug)
- **Steps**: checkout → setup-python → preflight → direct exec → always-on artifacts
- **Reason**: Persistent "workflow file issue" suspected due to mixed reusable/direct structure

## Technical Changes

### Before: Complex Multi-Job Structure
```yaml
jobs:
  call-l1:       # Attempted workflow_call (failed)
  call-direct:   # Plan-B direct execution (also failed)
```

### After: Simple Single-Job Structure
```yaml
jobs:
  run:           # Single direct execution job
```

## Key Improvements

### 1. Structural Simplification
- Eliminated all workflow_call references
- Removed job interdependencies
- Single execution path with no branching

### 2. Debug Workflow Alignment
- Identical runner: ubuntu-22.04
- Same shell: bash with defaults
- Matching preflight diagnostics
- Consistent artifact collection

### 3. Enhanced Diagnostics
- Comprehensive environment info
- Input resolution logging
- Directory structure inspection
- Always-run artifact collection

## Implementation Details

### Job Configuration
```yaml
runs-on: ubuntu-22.04
permissions:
  contents: write
  pull-requests: write
  actions: read
defaults:
  run:
    shell: bash
```

### Execution Flow
1. **Checkout**: Full history with fetch-depth: 0
2. **Python Setup**: Version 3.x via actions/setup-python
3. **Dependencies**: PyYAML and requests installation
4. **Preflight**: Environment and input diagnostics
5. **Direct Execution**: autopilot_l1.sh with tee to logs
6. **Log Collection**: Always-run with metadata
7. **Artifact Upload**: Always-run with 7-day retention

## Expected Behavior

### Success Path
- Workflow parses without errors
- Job executes completely
- Artifacts generated regardless of script outcome
- Logs captured in _runner_logs/

### Failure Handling
- Always-run steps ensure artifact collection
- stdout captured via tee
- Summary metadata preserved
- 7-day artifact retention for debugging

## Testing Instructions

### Phase 1: Dry Run Test
```bash
gh workflow run autopilot_l1_manual.yml -r main \
  -f project=vpm-mini -f dry_run=true -f max_lines=3
```

### Phase 2: Live Execution (if dry run succeeds)
```bash
gh workflow run autopilot_l1_manual.yml -r main \
  -f project=vpm-mini -f dry_run=false -f max_lines=3
```

### Expected Artifacts
- `reports/_runner_logs/autopilot_l1_stdout.log`
- `reports/_runner_logs/summary.txt`
- `reports/vpm-mini/state_view_*.md`
- `reports/autopilot_l1_update_*.md`
- `reports/autopilot_l1_*.json`

## Benefits

### 1. Elimination of Complexity
- No workflow_call mechanism
- No job dependencies
- No structural conflicts

### 2. Proven Pattern
- Matches successful debug workflow structure
- Single responsibility principle
- Clear execution path

### 3. Maintainability
- Simple to debug
- Easy to modify
- No hidden dependencies

## Exit Criteria
- ✅ Workflow parses successfully (no "workflow file issue")
- ✅ Job executes to completion
- ✅ Artifacts generated with expected structure
- ✅ UI-triggered execution works reliably

## Rollback Plan
Previous workflow versions preserved in git history. To restore:
```bash
git revert HEAD
```

## Conclusion
This simplified single-job implementation eliminates all workflow_call complexity and structural conflicts. It follows the proven pattern from the debug workflow, ensuring reliable execution and artifact generation.

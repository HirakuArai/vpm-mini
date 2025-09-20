# Autopilot L1 Debug Workflow

**Generated**: 2025-09-20 09:22:00
**Purpose**: Dedicated diagnostic workflow for isolating Autopilot L1 failures

## Summary
- **Workflow**: `.github/workflows/autopilot_l1_debug.yml`
- **Name**: `Autopilot L1 — Debug`
- **Function**: Runs only preflight checks with comprehensive diagnostics
- **Benefit**: Isolates issues without affecting production workflows

## Design Principles

### 1. Minimal Execution Path
- Only runs essential preflight checks (phase-guard, state-view)
- No actual autopilot script execution
- Quick failure identification

### 2. Maximum Visibility
- Comprehensive environment diagnostics
- Input resolution transparency
- Directory structure inspection
- Git configuration visibility

### 3. Fixed Environment
- Runner: `ubuntu-22.04` (locked version for consistency)
- Python: `3.x` via setup-python action
- Shell: `bash` with strict error handling

## Debug Workflow Components

### Environment Diagnostics
```bash
set -euxo pipefail
echo "Runner OS: ${{ runner.os }}"
echo "whoami: $(whoami)"
echo "pwd: $(pwd)"
echo "git version: $(git --version)"
echo "python version: $(python3 --version)"
```

### Input Resolution Check
```bash
echo "project=${{ github.event.inputs.project }}"
echo "dry_run=${{ github.event.inputs.dry_run }}"
echo "max_lines=${{ github.event.inputs.max_lines }}"
```

### Directory Structure Validation
```bash
ls -la scripts/ || echo "scripts/ directory not found"
ls -la STATE/${{ github.event.inputs.project }}/ || echo "STATE/$project/ not found"
```

### Preflight Execution with Error Handling
```bash
make phase-guard PROJECT="${{ github.event.inputs.project }}" || {
    echo "ERROR: Phase guard failed with exit code $?"
    # Additional diagnostics on failure
}
```

### Always-Run Artifact Collection
```yaml
- name: Upload Debug Artifacts
  if: always()
  uses: actions/upload-artifact@v4
  with:
    name: autopilot-l1-debug-${{ github.run_id }}
    path: reports/**
```

## Common Failure Patterns Addressed

### 1. Line Ending / Permissions
- **Fix**: `git config --global core.autocrlf input`
- **Fix**: Scripts use `chmod +x` in main workflow

### 2. Working Directory Issues
- **Debug**: `pwd` and `ls` commands show exact location
- **Debug**: Full directory tree inspection

### 3. Boolean Input Type Issues  
- **Note**: `true/false` as strings work fine for shell arguments
- **Debug**: Input values explicitly echoed

### 4. Python Environment
- **Fix**: `setup-python@v5` ensures Python availability
- **Debug**: Python version and module checks

### 5. Runner Differences
- **Fix**: Locked to `ubuntu-22.04` (avoiding 24.04 issues)
- **Debug**: Runner info explicitly displayed

## Usage Instructions

### Running the Debug Workflow
1. Go to Actions tab in GitHub
2. Select "Autopilot L1 — Debug"
3. Click "Run workflow"
4. Set parameters (project, dry_run, max_lines)
5. Run and wait for completion

### Analyzing Results
1. Download artifacts from workflow run
2. Check `reports/_debug/debug_summary.txt` for overview
3. Review execution logs for specific failure points
4. Check `reports/_debug/` for state_view outputs

### Interpreting Common Failures

#### Phase Guard Failure
```
ERROR: Phase guard failed with exit code 1
```
- Check if STATE/<project>/current_state.md exists
- Verify phase value matches expected format

#### State View Failure
```
ERROR: State view failed with exit code 1  
```
- Check if scripts/state_view.py exists
- Verify Python environment is properly set up

#### Missing Files
```
scripts/ directory not found
```
- Indicates checkout failure or wrong working directory
- Check git status and repository structure

## Benefits

### 1. Fast Diagnosis
- Runs in under 30 seconds
- Immediate visibility into environment state
- Clear error messages with context

### 2. Non-Invasive
- Doesn't affect main workflow
- No code execution, only validation
- Safe to run repeatedly

### 3. Comprehensive Output
- Full environment dump
- All relevant file paths checked
- Complete execution trace

### 4. Always Gets Artifacts
- `if: always()` ensures artifact upload
- Debug info available even on total failure
- Persistent 7-day retention

## Next Steps After Diagnosis

### If Phase Guard Fails
1. Check STATE directory structure
2. Verify current_state.md format
3. Ensure phase value is correct

### If State View Fails
1. Check Python dependencies
2. Verify scripts exist and are readable
3. Check for syntax errors in Python scripts

### If Environment Issues
1. Review runner version compatibility
2. Check git configuration
3. Verify checkout succeeded

## Exit Criteria Verification
- ✅ Workflow accessible from GitHub Actions UI
- ✅ Always produces downloadable artifacts
- ✅ Clear indication of phase-guard vs state-view failures
- ✅ Debug directory contains state_view on success
- ✅ Comprehensive environment diagnostics available

## Conclusion
This debug workflow provides a surgical tool for diagnosing Autopilot L1 issues without
the complexity of the full execution path. It focuses on the most common failure points
and provides maximum visibility into the execution environment.

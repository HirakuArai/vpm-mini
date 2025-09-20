# Manual Shim Fix (reusable call hardened)

**Generated**: 2025-09-21 04:57:00
**Purpose**: Robustify Manual Shim workflow_call with full repo reference and fallback

## Changes Applied

### 1. Full Repository Reference
```yaml
# Before: Relative path (unstable)
uses: ./.github/workflows/autopilot_l1.yml

# After: Full repo reference (stable)
uses: HirakuArai/vpm-mini/.github/workflows/autopilot_l1.yml@main
```

### 2. Secrets Inheritance
```yaml
# Added explicit secrets inheritance
secrets: inherit
```
- Ensures GITHUB_TOKEN and other secrets propagate correctly
- Prevents permission-related failures in called workflow

### 3. Plan-B Direct Execution Job
```yaml
call-direct:
  if: ${{ always() && false }} # Disabled by default
  # Complete inline implementation of autopilot_l1 logic
```
- Toggleable fallback if reusable workflow continues to fail
- Same functionality without workflow_call dependency
- Enable by changing `false` to `true` in the if condition

## Root Cause Analysis

### Original Issues
1. **Relative Path Resolution**: `./.github/workflows/autopilot_l1.yml` may have resolution issues
2. **Secret Propagation**: Missing `secrets: inherit` causing permission failures
3. **No Fallback**: Single point of failure with no alternative execution path

### Hardening Solutions
1. **Absolute Reference**: `repo@main` format eliminates path resolution ambiguity
2. **Explicit Inheritance**: Ensures all secrets and permissions flow correctly
3. **Dual Strategy**: Primary reusable call + backup direct execution

## Implementation Details

### Primary Path (call-l1)
- Uses hardened full repository reference
- Includes secrets inheritance for complete permission context
- Maintains original input parameter structure

### Fallback Path (call-direct)
- Disabled by default (`if: ${{ always() && false }}`)
- Complete inline implementation matching main workflow logic
- Independent artifact upload with same naming convention
- Activatable by changing condition to `true`

## Testing Strategy

### Phase 1: Primary Path Test
```bash
gh workflow run autopilot_l1_manual.yml -r main \
  -f project=vpm-mini -f dry_run=true -f max_lines=3
```

### Phase 2: Fallback Activation (if needed)
1. Edit workflow: `if: ${{ always() && false }}` → `if: ${{ always() && true }}`
2. Commit and test fallback path
3. Compare artifacts between primary and fallback paths

## Expected Outcomes

### Success Criteria
- Manual Shim executes successfully via call-l1 job
- Artifacts generated with expected structure:
  - `reports/_runner_logs/**`
  - `reports/vpm-mini/state_view_*.md`
  - `reports/autopilot_l1_update_*.md`

### Fallback Activation
- If primary path continues to fail, Plan-B provides identical functionality
- No dependency on workflow_call mechanism
- Direct execution eliminates external call complexity

## Benefits

### 1. Reference Stability
- Full repo reference eliminates relative path issues
- Explicit branch targeting (@main) ensures consistent workflow version

### 2. Permission Completeness  
- `secrets: inherit` provides full secret and token context
- Eliminates permission-related workflow failures

### 3. Execution Resilience
- Dual execution paths provide redundancy
- Plan-B eliminates workflow_call as potential failure point
- Maintains identical functionality across both paths

## Files Modified
- **Primary**: `.github/workflows/autopilot_l1_manual.yml`
- **Evidence**: `reports/actions_autopilot_l1_manual_shim_fix_*.md`

## Exit Criteria Verification
- ✅ Full repo reference implemented (`HirakuArai/vpm-mini/.github/workflows/autopilot_l1.yml@main`)
- ✅ Secrets inheritance added (`secrets: inherit`)
- ✅ Plan-B fallback job created (toggleable)
- ✅ Evidence documentation generated
- ⏳ Testing required to validate hardening effectiveness

## Conclusion
The Manual Shim workflow has been comprehensively hardened with full repository references, complete secret inheritance, and a fallback execution strategy. This eliminates the most common workflow_call failure points while providing a backup path if issues persist.

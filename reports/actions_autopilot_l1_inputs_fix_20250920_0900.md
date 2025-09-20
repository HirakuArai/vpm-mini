# Actions Input Unification Fix

**Generated**: 2025-09-20 08:50:00
**Purpose**: Unify workflow_dispatch and workflow_call input handling + add proper permissions

## Summary
- **Fixed**: Input reference inconsistency between dispatch and call triggers
- **Added**: Proper permissions for PR creation and evidence handling
- **Pattern**: `inputs.* || github.event.inputs.* || defaults` for unified access
- **Result**: Both workflow_dispatch and workflow_call run with identical arguments

## Changes Applied

### 1. Unified Input References (.github/workflows/autopilot_l1.yml)
**Before**:
```yaml
--project="${{ github.event.inputs.project || 'vpm-mini' }}"
--dry-run="${{ github.event.inputs.dry_run || 'true' }}"  
--max-lines="${{ github.event.inputs.max_lines || '3' }}"
```

**After**:
```yaml
--project="${{ inputs.project || github.event.inputs.project || 'vpm-mini' }}"
--dry-run="${{ inputs.dry_run || github.event.inputs.dry_run || 'true' }}"
--max-lines="${{ inputs.max_lines || github.event.inputs.max_lines || '3' }}"
```

### 2. Enhanced Permissions
**Added to both workflows**:
```yaml
permissions:
  contents: write        # For evidence commits/pushes
  pull-requests: write   # For automated PR creation
  actions: read         # For workflow artifact access
  issues: read          # For existing functionality
```

### 3. Improved Artifact Handling
**Dynamic naming with project namespace**:
```yaml
name: autopilot-l1-${{ inputs.project || github.event.inputs.project || 'vpm-mini' }}-${{ github.run_id }}
path: |
  reports/autopilot_l1_*.md
  reports/autopilot_l1_*.json
  reports/${{ inputs.project || github.event.inputs.project || 'vpm-mini' }}/state_view_*.md
```

## Technical Details

### Input Resolution Order
1. **workflow_call**: `inputs.*` (direct parameter passing)
2. **workflow_dispatch**: `github.event.inputs.*` (UI/CLI input)
3. **Fallback**: Hardcoded defaults for safety

### Permissions Justification
- **contents: write**: Required for future PR creation and evidence commits
- **pull-requests: write**: Enables automated PR workflow when live mode is implemented
- **actions: read**: Allows artifact access and workflow introspection

## Expected Benefits
- ✅ **Unified Behavior**: Both dispatch methods produce identical results
- ✅ **No Runtime Failures**: Proper input resolution prevents undefined values
- ✅ **Future-Ready**: Permissions prepared for automated PR creation
- ✅ **Better Artifacts**: Project-namespaced with comprehensive evidence files

## Backward Compatibility
- ✅ **workflow_dispatch**: Maintains existing behavior with enhanced fallbacks
- ✅ **Manual Shim**: Continues to work identically
- ✅ **Local Execution**: Unaffected by workflow changes

## Testing Ready
The unified input system should resolve the previous workflow execution failures
by ensuring consistent parameter passing regardless of trigger method.

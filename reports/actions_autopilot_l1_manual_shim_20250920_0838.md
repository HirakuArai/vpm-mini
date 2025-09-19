# Actions Manual Shim for Autopilot L1

**Generated**: 2025-09-20 05:47:00
**Purpose**: Enable immediate UI dispatch for Autopilot L1 workflow

## Summary
- **Added**: `.github/workflows/autopilot_l1_manual.yml` (manual dispatch shim)
- **Updated**: `.github/workflows/autopilot_l1.yml` (now supports workflow_call)
- **Benefit**: Immediate availability in GitHub Actions UI

## Implementation Details

### Reusable Workflow Support
- **File**: `.github/workflows/autopilot_l1.yml`
- **Change**: Added `workflow_call` trigger with matching inputs
- **Compatibility**: Maintains existing `workflow_dispatch` for backward compatibility
- **Inputs**: project, dry_run, max_lines (consistent across both triggers)

### Manual Shim Workflow
- **File**: `.github/workflows/autopilot_l1_manual.yml`
- **Name**: `Autopilot L1 — Manual Shim`
- **Purpose**: Dedicated UI-visible workflow that calls the main workflow
- **Pattern**: Shim pattern for immediate UI availability

## How to Use

### Via GitHub Actions UI
1. Navigate to Actions tab
2. Select "Autopilot L1 — Manual Shim" from workflow list
3. Click "Run workflow"
4. Configure parameters:
   - **project**: vpm-mini (default)
   - **dry_run**: true (default) / false for live run
   - **max_lines**: 3 (default)
5. Click "Run workflow" button

### Via GitHub CLI
```bash
gh workflow run "Autopilot L1 — Manual Shim" --ref main \
  --field project=vpm-mini \
  --field dry_run=true \
  --field max_lines=3
```

### Direct Invocation (Alternative)
```bash
./scripts/autopilot_l1.sh \
  --project vpm-mini \
  --dry-run true \
  --max-lines 3
```

## Expected Artifacts
After successful execution:
- `reports/autopilot_l1_update_*.md` - Execution evidence
- `reports/<project>/state_view_*.md` - Project state snapshot
- `reports/autopilot_l1_scan_*.json` - JSON results

## Architecture Benefits
1. **Immediate Availability**: Manual shim appears in UI instantly
2. **Reusability**: Main workflow can be called from other workflows
3. **Separation of Concerns**: UI dispatch separated from logic
4. **Maintainability**: Single source of truth for autopilot logic

## Rollback Plan
If issues arise:
1. Delete `.github/workflows/autopilot_l1_manual.yml`
2. Remove `workflow_call` section from `.github/workflows/autopilot_l1.yml`
3. No impact on existing operations

## Status: Ready for Deployment
- ✅ Reusable workflow configuration complete
- ✅ Manual shim workflow created
- ✅ Evidence documentation generated
- ✅ Ready for PR and testing

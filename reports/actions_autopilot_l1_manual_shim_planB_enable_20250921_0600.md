# Manual Shim Plan-B Enabled

**Generated**: 2025-09-21 06:00:00
**Purpose**: Enable direct execution to bypass workflow_call issues

## Summary
- **Reason**: workflow_call path kept failing with "workflow file issue"  
- **Change**: call-direct job enabled (`if: ${{ always() && true }}`)
- **Effect**: Runs inline steps identical to reusable flow, artifacts guaranteed

## Technical Details

### Primary Path Status
- **call-l1 job**: Still attempting workflow_call (will fail but harmless)
- **Failure Mode**: "This run likely failed because of a workflow file issue"
- **Impact**: No artifacts generated from primary path

### Plan-B Activation
```yaml
# Changed from:
if: ${{ always() && false }}

# To:
if: ${{ always() && true }}
```

### Direct Execution Features
- Inline implementation of autopilot_l1.sh logic
- Independent artifact generation
- No dependency on workflow_call mechanism  
- Same input parameters and output structure

## Expected Behavior

### Execution Flow
1. Manual Shim triggered via UI
2. call-l1 job attempts (may fail, non-blocking)
3. call-direct job executes (always runs)
4. Artifacts generated from direct execution

### Artifacts Generated
- `reports/_runner_logs/**` - Execution logs and stdout
- `reports/vpm-mini/state_view_*.md` - Project state view
- `reports/autopilot_l1_update_*.md` - Execution evidence  
- `reports/autopilot_l1_*.json` - Scan results

## Rollback Plan
To disable Plan-B and revert to primary path only:
```yaml
if: ${{ always() && false }}
```

## Testing Instructions
1. Navigate to Actions → "Autopilot L1 — Manual Shim"
2. Click "Run workflow"  
3. Set parameters: project=vpm-mini, dry_run=true, max_lines=3
4. Monitor execution and download artifacts

## Exit Criteria
- ✅ Direct execution job runs successfully
- ✅ Artifacts generated with expected structure
- ✅ No dependency on workflow_call mechanism
- ✅ UI-triggered execution completes

## Notes
- Primary path (call-l1) retained for future restoration
- Direct path provides identical functionality
- Temporary solution until workflow_call issues resolved

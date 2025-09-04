# CD Canary Deployment Runbook

## Overview

This runbook provides guidance for monitoring and troubleshooting the CD Canary deployment workflow.

## Monitoring

### Grafana Dashboard

Access the CD metrics dashboard:
1. Navigate to Grafana: `http://grafana.hyper-swarm.svc.cluster.local:3000`
2. Open dashboard: `CD Canary Deployment Metrics` (uid: `cd-canary-metrics`)

### Key Metrics to Watch

- **Success Rate**: Should be >99% over 24h period
- **Freeze Count**: Indicates manual interventions
- **Duration**: P95 should be <30s for both clusters

## Troubleshooting

### Failed Deployment

1. **Check Grafana Dashboard**
   - Look at "Last Run Status" panel
   - Check individual cluster durations
   - Review freeze indicator

2. **Examine GitHub Actions Logs**
   ```bash
   gh run list --workflow=cd_canary_multicluster --limit=5
   gh run view <run-id> --log
   ```

3. **Check NDJSON Reports**
   ```bash
   # Find recent failures
   grep '"status":"failed"' reports/cd_runs.ndjson | tail -5 | jq .
   
   # Check specific run
   jq 'select(.run_id == "RUN_ID")' reports/cd_runs.ndjson
   ```

### Freeze Detection

When deployment is frozen:
1. Check freeze status:
   ```bash
   cat .ops/deploy_freeze.json
   ```

2. Monitor freeze metric in Grafana
3. Review freeze count over time

### Performance Issues

For slow deployments:
1. **Compare Cluster Durations**
   - Check if one cluster is consistently slower
   - Review duration trends in Grafana

2. **Analyze Historical Data**
   ```bash
   # Average duration for cluster A
   jq -s 'map(select(.status == "success") | .clusters.A.duration_sec) | add/length' reports/cd_runs.ndjson
   
   # P95 duration
   jq -s 'map(select(.status == "success") | .clusters.A.duration_sec) | sort | .[length * 0.95 | floor]' reports/cd_runs.ndjson
   ```

## Alerts

### Critical Alerts

- **Success Rate <95%**: Multiple deployment failures
- **Duration >60s**: Significant performance degradation
- **No metrics for >2h**: Monitoring system failure

### Response Actions

1. **For Failures**:
   - Check recent commits for breaking changes
   - Verify cluster health
   - Review deployment logs

2. **For Performance Issues**:
   - Check cluster resource utilization
   - Review network latency
   - Analyze deployment parallelism

## Recovery Procedures

### Manual Deployment

If automated deployment fails:
```bash
# Trigger manual deployment
gh workflow run cd_canary_multicluster

# Monitor progress
gh run watch
```

### Rollback

For critical issues:
```bash
# Revert to last known good commit
git revert HEAD
git push

# Or trigger deployment of specific commit
gh workflow run cd_canary_multicluster --ref <commit-sha>
```

## Maintenance

### Metrics Cleanup

Pushgateway metrics persist indefinitely. To clean old metrics:
```bash
# Delete metrics older than 7 days (run from Pushgateway pod)
curl -X DELETE http://localhost:9091/metrics/job/cd_canary
```

### Report Rotation

When NDJSON file grows too large:
```bash
# Archive old reports
mv reports/cd_runs.ndjson reports/cd_runs_$(date +%Y%m%d).ndjson
echo '[]' > reports/cd_runs.ndjson

# Update summary
python scripts/cd_report_summary.py
```

## Contact

- **On-call**: Check PagerDuty schedule
- **Escalation**: Platform team lead
- **Documentation**: `/docs/cd/README.md`
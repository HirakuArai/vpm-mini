# Autopilot L1 Policy - Limited Autonomous Loop

## Policy Statement

The Autopilot L1 system is authorized to perform limited, low-risk improvements to the codebase within strict safety constraints. This policy defines the boundaries, procedures, and oversight requirements for autonomous operations.

## Authority & Scope

### Authorized Actions

**ALLOWED**:
- ✅ Documentation improvements (README files, markdown formatting)
- ✅ Comment additions and improvements (docstrings, purpose comments)
- ✅ Code formatting fixes (whitespace, indentation)
- ✅ TODO comment standardization
- ✅ File extension and naming convention fixes

**PROHIBITED**:
- ❌ Any functional code changes
- ❌ Logic modifications
- ❌ Dependency updates
- ❌ Configuration changes that affect behavior
- ❌ File deletions or major restructuring
- ❌ Security-related modifications
- ❌ Database schema or data changes

### File Type Allowlists

**Documentation Files** (`docs` area):
```
*.md, docs/**, README*, CHANGELOG*, LICENSE*
```

**Comment Improvements** (`comments` area):
```
*.py, *.js, *.ts, *.yaml, *.yml, *.sh
```

**Formatting Fixes** (`formatting` area):
```
*.py, *.js, *.ts, *.json, *.yaml, *.yml
```

**Explicitly Excluded**:
```
*.sql, *.env*, **/secrets/**, **/config/production/**
Dockerfile*, docker-compose*, package.json, requirements.txt
```

## Operational Constraints

### Execution Limits

| Constraint | Limit | Enforcement |
|------------|-------|-------------|
| Max Changes per Run | 3 | Script enforcement |
| Max Files Modified | 5 | Script enforcement |
| Max Line Changes per File | 20 | Script validation |
| Execution Timeout | 10 minutes | GitHub Actions |
| Daily Executions | 3 | Schedule constraint |

### Safety Mechanisms

1. **Dry Run Default**: All executions default to dry-run mode unless explicitly overridden
2. **Change Validation**: Every change validated against allowlists before application
3. **Human Review**: All PRs require human approval before merge
4. **Rollback Capability**: Git-based versioning enables instant rollback
5. **Emergency Stop**: Workflow can be manually cancelled at any time

### Quality Gates

**Pre-execution**:
- Repository state validation
- Branch protection verification
- Change limit validation

**During execution**:
- File type allowlist checking
- Content change validation
- Progress monitoring and logging

**Post-execution**:
- Change summary generation
- Quality assessment
- Audit trail creation

## Procedures

### Normal Operation

1. **Trigger**: Manual workflow dispatch or scheduled execution
2. **Scan**: Autopilot scans for improvements within target areas
3. **Validate**: Changes validated against policies and constraints
4. **Apply**: Changes applied if within limits and not in dry-run mode
5. **PR Creation**: Pull request created with comprehensive description
6. **Review**: Human review and approval required for merge
7. **Audit**: Full audit trail captured and stored

### Emergency Procedures

**Immediate Stop**:
```bash
# Cancel running workflow
gh workflow list
gh run cancel <RUN_ID>
```

**Rollback Changes**:
```bash
# Revert autopilot PR
gh pr view <PR_NUMBER>
gh pr close <PR_NUMBER>
git branch -D autopilot/l1-<timestamp>
```

**Disable System**:
```bash
# Disable workflow
gh workflow disable autopilot_l1.yml
```

### Incident Response

**Level 1 - Quality Issue**:
- Review and close problematic PR
- Update allowlists to prevent recurrence
- Continue normal operations

**Level 2 - Policy Violation**:
- Immediately stop all autopilot operations
- Investigate constraint failure
- Update safety mechanisms before resuming

**Level 3 - Security/Safety Issue**:
- Emergency shutdown of all autopilot systems
- Full investigation and external review
- Management approval required to resume

## Governance

### Roles & Responsibilities

**System Owner**: VPM-Mini Trial Team
- Policy maintenance and updates
- System configuration and deployment
- Incident response coordination

**Operations Team**: Development Team
- Daily monitoring and oversight
- Quality review of autopilot PRs
- Feedback and improvement suggestions

**Review Authority**: Technical Lead
- Policy change approval
- Incident escalation decisions
- System enable/disable authority

### Review & Updates

**Regular Review Schedule**:
- **Weekly**: Execution metrics and quality assessment
- **Monthly**: Policy effectiveness and constraint review
- **Quarterly**: System expansion and improvement planning

**Trigger-based Review**:
- After any Level 2+ incident
- When change patterns shift significantly
- Before expanding to new target areas

### Metrics & Monitoring

**Key Performance Indicators**:
- Constraint violation rate (target: 0%)
- Change quality score (target: >90%)
- Time to merge (target: <24 hours)
- Manual intervention rate (target: <10%)

**Monitoring Dashboard**:
- Real-time execution status
- Historical performance trends
- Quality metrics tracking
- Constraint violation alerts

## Compliance & Audit

### Audit Requirements

**Execution Audit**:
- Every autopilot run fully logged
- Change details captured with reasoning
- Approval chain documented
- Timestamps and actor identification

**Change Audit**:
- Before/after diffs preserved
- Change rationale documented
- Quality assessment recorded
- Rollback procedures verified

**Policy Audit**:
- Constraint adherence verified
- Exception handling documented
- Review cycle compliance checked
- Training and awareness confirmed

### Documentation Requirements

**Execution Records**:
- Autopilot scan results (JSON format)
- Applied changes with justification
- PR creation and review process
- Merge status and timing

**Quality Records**:
- Change accuracy assessment
- False positive analysis
- Developer feedback collection
- Improvement recommendations

**Compliance Records**:
- Policy adherence verification
- Constraint violation reports
- Exception approvals and rationale
- System configuration changes

## Training & Awareness

### Required Training

**All Developers**:
- Autopilot system overview
- Policy boundaries and constraints
- PR review procedures for autopilot changes
- Emergency stop procedures

**Operations Team**:
- Detailed system operation
- Monitoring and alerting
- Incident response procedures
- Quality assessment methods

**System Administrators**:
- Configuration management
- Security implications
- Audit trail maintenance
- Emergency procedures

### Communication Plan

**System Status**:
- Weekly status updates to development team
- Monthly summary to management
- Quarterly system review meetings
- Incident notifications as required

**Policy Changes**:
- 48-hour advance notice for policy updates
- Team review and feedback period
- Formal approval process
- Updated training as needed

## Risk Management

### Identified Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Policy Violation | Low | High | Multiple constraint layers |
| Quality Degradation | Medium | Medium | Human review requirement |
| System Abuse | Low | High | Audit trail and monitoring |
| Technical Failure | Medium | Low | Rollback and recovery procedures |

### Risk Monitoring

**Continuous Monitoring**:
- Constraint violation detection
- Quality metrics tracking
- Usage pattern analysis
- Security event monitoring

**Periodic Assessment**:
- Monthly risk review
- Quarterly threat modeling
- Annual security assessment
- External audit preparation

### Escalation Matrix

| Severity | Response Time | Escalation Path |
|----------|---------------|-----------------|
| Info | 24 hours | Operations Team |
| Warning | 4 hours | Technical Lead |
| Critical | 1 hour | System Owner + Management |
| Emergency | Immediate | All stakeholders + Emergency stop |

## Appendices

### A. Change Pattern Examples

**Acceptable Documentation Change**:
```diff
+ # Project Name
+
  This is a project description...
```

**Acceptable Comment Addition**:
```diff
  def process_data(data):
+     """Process input data and return results."""
      return data.upper()
```

**Acceptable Formatting Fix**:
```diff
- def func( a,b ):
+ def func(a, b):
```

### B. Configuration Reference

**Workflow Configuration**:
```yaml
max_changes: 3
dry_run: true
target_areas: "docs,comments"
timeout: 600  # 10 minutes
```

**Script Parameters**:
```bash
--max-changes=3
--dry-run=true
--target-areas=docs,comments,formatting
```

### C. Emergency Contacts

- **System Owner**: VPM-Mini Trial Team
- **Technical Lead**: [Contact Information]
- **Operations Team**: [Contact Information]
- **Security Team**: [Contact Information]

---

**Policy Version**: 1.0
**Effective Date**: 2025-09-19
**Review Date**: 2025-10-19
**Approval Authority**: VPM-Mini Trial Team
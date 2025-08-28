#!/bin/bash
set -euo pipefail

# Sample PROV Workflow
# Demonstrates admission decision logging with signed audit trails

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "📋 Running sample PROV workflow..."

# Load configuration
export PROV_SCHEMA_PATH="$PROJECT_ROOT/schema/prov_event.schema.json"
export PROV_CONTEXT_PATH="$PROJECT_ROOT/schema/prov_context.json"
export SIGNING_PRIVATE_KEY_PATH="$PROJECT_ROOT/config/keys/signing_key.pem"
export SIGNING_PUBLIC_KEY_PATH="$PROJECT_ROOT/config/keys/signing_key.pub"
export S3_ENDPOINT_URL="http://localhost:9000"
export S3_ACCESS_KEY_ID="vpm-audit"
export S3_SECRET_ACCESS_KEY="vpm-audit-secret-key" # pragma: allowlist secret

# Check if MinIO port-forward is running
if ! curl -s http://localhost:9000/minio/health/live > /dev/null; then
    echo "⚠️  MinIO not accessible at localhost:9000"
    echo "Run: kubectl port-forward -n minio-system svc/minio 9000:9000"
    exit 1
fi

# Generate sample admission decisions
echo "🧪 Generating sample admission decisions..."

python3 -c "
import sys
import json
import uuid
from datetime import datetime, timezone
sys.path.append('$PROJECT_ROOT/src')

from ops.prov_logger import ProvLogger
from ops.signing import ProvSigner  
from ops.s3_uploader import S3AuditUploader

# Initialize components
logger = ProvLogger()
signer = ProvSigner('$PROJECT_ROOT/config/keys/signing_key.pem', '$PROJECT_ROOT/config/keys/signing_key.pub')
uploader = S3AuditUploader(
    endpoint_url='http://localhost:9000',
    aws_access_key_id='vpm-audit', 
    aws_secret_access_key='vpm-audit-secret-key'  # pragma: allowlist secret
)

# Sample admission decisions
sample_decisions = [
    {
        'pod_name': 'compliant-pod-1',
        'namespace': 'hyper-swarm',
        'decision': 'allow',
        'violated_constraints': [],
        'spiffe_id': 'spiffe://vpm-mini.local/gatekeeper'
    },
    {
        'pod_name': 'non-compliant-pod-1', 
        'namespace': 'hyper-swarm',
        'decision': 'deny',
        'violated_constraints': ['require-spire-socket', 'require-service-account'],
        'spiffe_id': 'spiffe://vpm-mini.local/gatekeeper'
    },
    {
        'pod_name': 'test-pod-2',
        'namespace': 'default',
        'decision': 'allow',
        'violated_constraints': [],
        'spiffe_id': 'spiffe://vpm-mini.local/gatekeeper'
    },
    {
        'pod_name': 'privileged-pod-1',
        'namespace': 'kube-system', 
        'decision': 'deny',
        'violated_constraints': ['require-network-policy'],
        'spiffe_id': 'spiffe://vpm-mini.local/gatekeeper'
    },
    {
        'pod_name': 'system-pod-1',
        'namespace': 'gatekeeper-system',
        'decision': 'allow',
        'violated_constraints': [],
        'spiffe_id': 'spiffe://vpm-mini.local/gatekeeper'
    }
]

print(f'📊 Processing {len(sample_decisions)} admission decisions...')

signed_records = []
for i, decision in enumerate(sample_decisions, 1):
    print(f'  {i}/{len(sample_decisions)}: {decision[\"pod_name\"]} -> {decision[\"decision\"]}')
    
    # Generate PROV record
    prov_record = logger.log_admission_decision(**decision)
    
    # Sign record
    signed_record = signer.sign_prov_record(prov_record)
    signed_records.append(signed_record)

print(f'✅ Generated {len(signed_records)} signed PROV records')

# Upload batch to S3
print('☁️  Uploading batch to MinIO...')
batch_id = f'sample-workflow-{uuid.uuid4().hex[:8]}'
s3_key, upload_info = uploader.upload_batch(
    signed_records, 
    batch_id=batch_id,
    metadata={
        'workflow': 'sample-admission-decisions',
        'source': 'sample_prov_workflow.sh'
    }
)

print(f'✅ Uploaded batch: {batch_id}')
print(f'  S3 Key: {s3_key}')
print(f'  Records: {upload_info[\"record_count\"]}')
print(f'  Compressed Size: {upload_info[\"compressed_size_bytes\"]} bytes')

# List recent batches
print('')
print('📂 Recent audit batches:')
batches = uploader.list_batches()
for batch in batches[:5]:
    print(f'  {batch[\"batch_id\"]:20} | {batch[\"record_count\"]:3} records | {batch[\"upload_timestamp\"]}')

# Get storage stats
print('')
print('📊 Storage statistics:')
stats = uploader.get_storage_stats()
print(f'  Total Batches: {stats[\"total_batches\"]}')
print(f'  Total Size: {stats[\"total_size_mb\"]} MB')
print(f'  Oldest Batch: {stats[\"oldest_batch\"]}')
print(f'  Newest Batch: {stats[\"newest_batch\"]}')

print('')
print('🎉 Sample workflow completed successfully!')
print(f'Generated batch ID: {batch_id}')
"

echo ""
echo "✅ Sample PROV workflow completed!"
echo ""
echo "🔍 To verify the results:"
echo "  1. Check MinIO console: http://localhost:9001"  
echo "  2. Browse bucket: vpm-audit-logs"
echo "  3. Run verification: ./scripts/verify_prov_ops.sh $batch_id"
echo ""
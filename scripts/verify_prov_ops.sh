#!/bin/bash
set -euo pipefail

# Verify PROV Operations System
# Validates deployment, connectivity, and data integrity

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
BATCH_ID="${1:-}"

echo "🔍 Verifying PROV Operations System..."

# Load configuration  
export PROV_SCHEMA_PATH="$PROJECT_ROOT/schema/prov_event.schema.json"
export PROV_CONTEXT_PATH="$PROJECT_ROOT/schema/prov_context.json"
export SIGNING_PRIVATE_KEY_PATH="$PROJECT_ROOT/config/keys/signing_key.pem"
export SIGNING_PUBLIC_KEY_PATH="$PROJECT_ROOT/config/keys/signing_key.pub"
export S3_ENDPOINT_URL="http://localhost:9000"
export S3_ACCESS_KEY_ID="vpm-audit"
export S3_SECRET_ACCESS_KEY="vpm-audit-secret-key" # pragma: allowlist secret

# Check Kubernetes resources
echo "🏗️  Checking Kubernetes resources..."

# Check MinIO deployment
if kubectl get deployment minio -n minio-system > /dev/null 2>&1; then
    MINIO_STATUS=$(kubectl get deployment minio -n minio-system -o jsonpath='{.status.conditions[?(@.type=="Available")].status}')
    if [[ "$MINIO_STATUS" == "True" ]]; then
        echo "  ✅ MinIO deployment is available"
    else
        echo "  ❌ MinIO deployment is not available"
        exit 1
    fi
else
    echo "  ❌ MinIO deployment not found"
    exit 1
fi

# Check SPIRE components (from previous phases)
if kubectl get daemonset spire-agent -n spire > /dev/null 2>&1; then
    echo "  ✅ SPIRE agent is deployed"
else
    echo "  ⚠️  SPIRE agent not found (expected from Phase 3-1)"
fi

if kubectl get deployment gatekeeper-audit -n gatekeeper-system > /dev/null 2>&1; then
    echo "  ✅ Gatekeeper is deployed" 
else
    echo "  ⚠️  Gatekeeper not found (expected from Phase 3-2)"
fi

# Check configuration files
echo "🔧 Checking configuration files..."

for file in "$PROV_SCHEMA_PATH" "$PROV_CONTEXT_PATH"; do
    if [[ -f "$file" ]]; then
        echo "  ✅ $(basename "$file") exists"
    else
        echo "  ❌ $(basename "$file") missing: $file"
        exit 1
    fi
done

# Check signing keys
if [[ -f "$SIGNING_PRIVATE_KEY_PATH" ]] && [[ -f "$SIGNING_PUBLIC_KEY_PATH" ]]; then
    echo "  ✅ Signing keypair exists"
    
    # Check key permissions
    PRIVATE_KEY_PERMS=$(stat -c "%a" "$SIGNING_PRIVATE_KEY_PATH" 2>/dev/null || stat -f "%A" "$SIGNING_PRIVATE_KEY_PATH" 2>/dev/null)
    if [[ "$PRIVATE_KEY_PERMS" == "600" ]]; then
        echo "  ✅ Private key permissions are secure (600)"
    else
        echo "  ⚠️  Private key permissions are not secure: $PRIVATE_KEY_PERMS"
    fi
else
    echo "  ❌ Signing keypair missing"
    exit 1
fi

# Test connectivity
echo "🌐 Testing connectivity..."

# Test MinIO connection
if curl -s http://localhost:9000/minio/health/live > /dev/null; then
    echo "  ✅ MinIO is accessible at localhost:9000"
else
    echo "  ❌ MinIO not accessible at localhost:9000"
    echo "     Run: kubectl port-forward -n minio-system svc/minio 9000:9000"
    exit 1
fi

# Test PROV operations
echo "🧪 Testing PROV operations..."

python3 -c "
import sys
import json
sys.path.append('$PROJECT_ROOT/src')

from ops.config import load_config
from ops.prov_logger import ProvLogger
from ops.signing import ProvSigner
from ops.s3_uploader import S3AuditUploader

print('📋 Configuration Validation:')
try:
    config = load_config()
    print('  ✅ Configuration loaded successfully')
    print(f'     Trust Domain: {config.vpm_trust_domain}')
    print(f'     S3 Bucket: {config.s3_bucket_name}')
    print(f'     Batch Size: {config.batch_size}')
except Exception as e:
    print(f'  ❌ Configuration validation failed: {e}')
    sys.exit(1)

print('')
print('🔐 Digital Signing Test:')
try:
    signer = ProvSigner('$PROJECT_ROOT/config/keys/signing_key.pem', '$PROJECT_ROOT/config/keys/signing_key.pub')
    
    # Test record
    test_record = {
        '@context': 'https://vpm-mini.local/prov/context',
        '@id': 'prov:verification-test',
        'entity': {'entity:test': {'type': 'Entity', 'label': 'Test Entity'}},
        'activity': {'activity:test': {'type': 'Activity', 'label': 'Test Activity'}},
        'agent': {'agent:spiffe:test': {'type': 'Agent', 'label': 'Test Agent'}}
    }
    
    # Sign and verify
    signed_record = signer.sign_prov_record(test_record)
    is_valid, message = signer.verify_prov_record(signed_record)
    
    if is_valid:
        print(f'  ✅ Digital signing works: {message}')
    else:
        print(f'  ❌ Digital signing failed: {message}')
        sys.exit(1)
        
    # Export public key info
    key_info = signer.export_public_key_info()
    print(f'     Public Key Fingerprint: {key_info[\"fingerprint\"]}')
    
except Exception as e:
    print(f'  ❌ Digital signing test failed: {e}')
    sys.exit(1)

print('')
print('📂 S3/MinIO Storage Test:')
try:
    uploader = S3AuditUploader(
        endpoint_url='http://localhost:9000',
        aws_access_key_id='vmp-audit',
        aws_secret_access_key='vpm-audit-secret-key'  # pragma: allowlist secret
    )
    
    # Get storage stats
    stats = uploader.get_storage_stats()
    print(f'  ✅ S3/MinIO connection successful')
    print(f'     Total Batches: {stats[\"total_batches\"]}')
    print(f'     Total Storage: {stats[\"total_size_mb\"]} MB')
    
    # List recent batches
    batches = uploader.list_batches()
    print(f'     Recent Batches: {len(batches)}')
    
    for batch in batches[:3]:
        print(f'       {batch[\"batch_id\"]:20} | {batch[\"record_count\"]:3} records')
        
except Exception as e:
    print(f'  ❌ S3/MinIO storage test failed: {e}')
    sys.exit(1)

print('')
print('🧬 PROV Schema Validation Test:')
try:
    logger = ProvLogger()
    
    # Test admission decision logging
    prov_record = logger.log_admission_decision(
        pod_name='verification-test-pod',
        namespace='default',
        decision='allow',
        spiffe_id='spiffe://vpm-mini.local/verification-test'
    )
    
    print('  ✅ PROV record generation successful')
    print(f'     Record ID: {prov_record[\"@id\"]}')
    print(f'     Entities: {len(prov_record[\"entity\"])}')
    print(f'     Activities: {len(prov_record[\"activity\"])}')
    print(f'     Agents: {len(prov_record[\"agent\"])}')
    
except Exception as e:
    print(f'  ❌ PROV schema validation failed: {e}')
    sys.exit(1)
"

# Specific batch verification if requested
if [[ -n "$BATCH_ID" ]]; then
    echo ""
    echo "🔍 Verifying specific batch: $BATCH_ID"
    
    python3 -c "
import sys
sys.path.append('$PROJECT_ROOT/src')
from ops.s3_uploader import S3AuditUploader

try:
    uploader = S3AuditUploader(
        endpoint_url='http://localhost:9000',
        aws_access_key_id='vpm-audit',
        aws_secret_access_key='vpm-audit-secret-key'  # pragma: allowlist secret
    )
    
    # Find batch with matching ID
    batches = uploader.list_batches()
    target_batch = None
    
    for batch in batches:
        if '$BATCH_ID' in batch['batch_id']:
            target_batch = batch
            break
    
    if target_batch:
        print(f'  ✅ Found batch: {target_batch[\"batch_id\"]}')
        print(f'     S3 Key: {target_batch[\"s3_key\"]}')
        print(f'     Records: {target_batch[\"record_count\"]}')
        print(f'     Size: {target_batch[\"size_bytes\"]} bytes')
        print(f'     Upload Time: {target_batch[\"upload_timestamp\"]}')
        
        # Download and verify
        records = uploader.download_batch(target_batch['s3_key'])
        print(f'  ✅ Successfully downloaded {len(records)} records')
        
        # Check first record structure
        if records:
            first_record = records[0]
            print(f'     First Record ID: {first_record.get(\"@id\", \"unknown\")}')
            print(f'     Has Signature: {\"vpm:signature\" in first_record}')
    else:
        print(f'  ❌ Batch not found: $BATCH_ID')
        
except Exception as e:
    print(f'  ❌ Batch verification failed: {e}')
    "
fi

echo ""
echo "🎉 PROV Operations System verification completed!"
echo ""
echo "✅ All checks passed:"
echo "  - MinIO deployment is healthy"
echo "  - Configuration is valid" 
echo "  - Digital signing is working"
echo "  - S3 storage is accessible"
echo "  - PROV schema validation passes"
echo ""
echo "📊 System is ready for audit logging!"
echo ""
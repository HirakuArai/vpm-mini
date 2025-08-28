#!/bin/bash
set -euo pipefail

# Bootstrap PROV Operations System
# Deploys MinIO, generates signing keys, and initializes audit infrastructure

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "🚀 Bootstrapping PROV Operations System..."

# Check prerequisites
if ! command -v kubectl &> /dev/null; then
    echo "❌ kubectl is required but not installed"
    exit 1
fi

if ! command -v python3 &> /dev/null; then
    echo "❌ python3 is required but not installed" 
    exit 1
fi

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip3 install -r "$PROJECT_ROOT/requirements-ops.txt"

# Deploy MinIO
echo "🗄️  Deploying MinIO storage..."
kubectl apply -f "$PROJECT_ROOT/infra/observability/minio/minio.yaml"

# Wait for MinIO to be ready
echo "⏳ Waiting for MinIO to be ready..."
kubectl wait --for=condition=available --timeout=300s deployment/minio -n minio-system

# Generate signing keypair
echo "🔐 Generating Ed25519 signing keypair..."
KEYS_DIR="$PROJECT_ROOT/config/keys"
mkdir -p "$KEYS_DIR"

python3 -c "
import sys
sys.path.append('$PROJECT_ROOT/src')
from ops.signing import ProvSigner

signer = ProvSigner()
private_pem, public_pem = signer.generate_keypair(
    '$KEYS_DIR/signing_key.pem',
    '$KEYS_DIR/signing_key.pub'
)

print('✅ Generated signing keypair:')
print(f'  Private key: $KEYS_DIR/signing_key.pem')
print(f'  Public key: $KEYS_DIR/signing_key.pub')

# Export public key info
key_info = ProvSigner('$KEYS_DIR/signing_key.pem', '$KEYS_DIR/signing_key.pub').export_public_key_info()
print(f'  Fingerprint: {key_info[\"fingerprint\"]}')
"

# Set restrictive permissions on private key
chmod 600 "$KEYS_DIR/signing_key.pem"
chmod 644 "$KEYS_DIR/signing_key.pub"

# Create audit log directory
echo "📁 Creating audit log directory..."
mkdir -p "$PROJECT_ROOT/var/log/prov"

# Test configuration
echo "⚙️  Testing configuration..."
cd "$PROJECT_ROOT"
export PROV_SCHEMA_PATH="$PROJECT_ROOT/schema/prov_event.schema.json"
export PROV_CONTEXT_PATH="$PROJECT_ROOT/schema/prov_context.json"
export SIGNING_PRIVATE_KEY_PATH="$KEYS_DIR/signing_key.pem"
export SIGNING_PUBLIC_KEY_PATH="$KEYS_DIR/signing_key.pub"

python3 -c "
import sys
sys.path.append('$PROJECT_ROOT/src')
from ops.config import load_config

try:
    config = load_config()
    print('✅ Configuration validation passed')
    print(f'  Trust Domain: {config.vpm_trust_domain}')
    print(f'  S3 Bucket: {config.s3_bucket_name}')
    print(f'  Batch Size: {config.batch_size}')
except Exception as e:
    print(f'❌ Configuration validation failed: {e}')
    sys.exit(1)
"

# Port-forward MinIO for testing
echo "🌐 Setting up MinIO port-forward for testing..."
kubectl port-forward -n minio-system svc/minio 9000:9000 &
MINIO_PF_PID=$!

# Wait for port-forward to establish
sleep 5

# Test S3 connection
echo "🔗 Testing S3/MinIO connection..."
export S3_ENDPOINT_URL="http://localhost:9000"
export S3_ACCESS_KEY_ID="vpm-audit"
export S3_SECRET_ACCESS_KEY="vpm-audit-secret-key" # pragma: allowlist secret

python3 -c "
import sys
sys.path.append('$PROJECT_ROOT/src')
from ops.s3_uploader import S3AuditUploader
from ops.prov_logger import ProvLogger
from ops.signing import ProvSigner
import json

try:
    # Test full pipeline
    print('🧪 Testing full PROV pipeline...')
    
    # Create PROV record
    logger = ProvLogger()
    prov_record = logger.log_admission_decision(
        pod_name='bootstrap-test-pod',
        namespace='default',
        decision='allow',
        spiffe_id='spiffe://vpm-mini.local/bootstrap-test'
    )
    
    # Sign record
    signer = ProvSigner('$KEYS_DIR/signing_key.pem', '$KEYS_DIR/signing_key.pub')
    signed_record = signer.sign_prov_record(prov_record)
    
    # Upload to S3
    uploader = S3AuditUploader(
        endpoint_url='http://localhost:9000',
        aws_access_key_id='vpm-audit',
        aws_secret_access_key='vpm-audit-secret-key'  # pragma: allowlist secret
    )
    
    s3_key, upload_info = uploader.upload_batch([signed_record])
    print(f'✅ Successfully uploaded test batch: {s3_key}')
    print(f'  Records: {upload_info[\"record_count\"]}')
    print(f'  Size: {upload_info[\"compressed_size_bytes\"]} bytes')
    
    # Verify upload
    downloaded_records = uploader.download_batch(s3_key)
    print(f'✅ Successfully downloaded and verified batch')
    print(f'  Downloaded {len(downloaded_records)} records')
    
except Exception as e:
    print(f'❌ Pipeline test failed: {e}')
    sys.exit(1)
"

# Clean up port-forward
kill $MINIO_PF_PID 2>/dev/null || true

echo ""
echo "🎉 PROV Operations System bootstrap completed successfully!"
echo ""
echo "📋 Summary:"
echo "  ✅ MinIO deployed and running"
echo "  ✅ Ed25519 signing keypair generated"
echo "  ✅ Configuration validated"
echo "  ✅ Full pipeline tested"
echo ""
echo "🔧 Next steps:"
echo "  1. Run: kubectl port-forward -n minio-system svc/minio 9000:9000"
echo "  2. Access MinIO console: http://localhost:9001 (vpm-audit/vpm-audit-secret-key)"
echo "  3. Run sample workflow: ./scripts/sample_prov_workflow.sh"
echo "  4. Verify deployment: ./scripts/verify_prov_ops.sh"
echo ""
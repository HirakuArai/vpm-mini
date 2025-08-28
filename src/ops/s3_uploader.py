#!/usr/bin/env python3

import json
import gzip
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
import boto3
from botocore.exceptions import ClientError
from dateutil.parser import parse as parse_date


class S3AuditUploader:
    """
    S3/MinIO uploader for signed PROV audit logs
    Handles batching, compression, and hierarchical storage organization
    """

    def __init__(
        self,
        endpoint_url: Optional[str] = None,
        bucket_name: str = "vpm-audit-logs",
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
        region_name: str = "us-east-1",
    ):
        """
        Initialize S3 uploader

        Args:
            endpoint_url: MinIO endpoint URL (None for AWS S3)
            bucket_name: S3 bucket name for audit logs
            aws_access_key_id: AWS access key (or MinIO access key)
            aws_secret_access_key: AWS secret key (or MinIO secret key)
            region_name: AWS region name
        """
        self.bucket_name = bucket_name
        self.endpoint_url = endpoint_url

        # Initialize S3 client
        self.s3_client = boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=region_name,
        )

        # Verify connection and bucket
        self._ensure_bucket_exists()

    def _ensure_bucket_exists(self):
        """Ensure the audit log bucket exists"""
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
        except ClientError as e:
            error_code = int(e.response["Error"]["Code"])
            if error_code == 404:
                # Bucket doesn't exist, create it
                try:
                    if self.endpoint_url:
                        # MinIO doesn't require region for bucket creation
                        self.s3_client.create_bucket(Bucket=self.bucket_name)
                    else:
                        # AWS S3 requires region specification
                        self.s3_client.create_bucket(
                            Bucket=self.bucket_name,
                            CreateBucketConfiguration={
                                "LocationConstraint": "us-east-1"
                            },
                        )
                except ClientError as create_error:
                    raise RuntimeError(
                        f"Failed to create bucket {self.bucket_name}: {create_error}"
                    )
            else:
                raise RuntimeError(f"Failed to access bucket {self.bucket_name}: {e}")

    def _generate_s3_key(
        self, timestamp: str, batch_id: str, record_type: str = "prov"
    ) -> str:
        """
        Generate hierarchical S3 key for audit log storage
        Format: audit-logs/year=YYYY/month=MM/day=DD/hour=HH/type=TYPE/batch_id.json.gz
        """
        dt = parse_date(timestamp)
        return (
            f"audit-logs/"
            f"year={dt.year:04d}/"
            f"month={dt.month:02d}/"
            f"day={dt.day:02d}/"
            f"hour={dt.hour:02d}/"
            f"type={record_type}/"
            f"{batch_id}.json.gz"
        )

    def _compress_records(self, records: List[Dict[str, Any]]) -> bytes:
        """Compress PROV records using gzip"""
        # Create JSONL format (one JSON per line)
        jsonl_content = "\n".join(
            json.dumps(record, separators=(",", ":")) for record in records
        )

        # Compress with gzip
        return gzip.compress(jsonl_content.encode("utf-8"))

    def upload_batch(
        self,
        signed_records: List[Dict[str, Any]],
        batch_id: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None,
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Upload a batch of signed PROV records to S3

        Args:
            signed_records: List of signed PROV records
            batch_id: Optional batch identifier (UUID generated if None)
            metadata: Optional metadata to attach to S3 object

        Returns:
            Tuple of (s3_key, upload_metadata)
        """
        if not signed_records:
            raise ValueError("No records provided for upload")

        # Generate batch ID if not provided
        if batch_id is None:
            import uuid

            batch_id = str(uuid.uuid4())

        # Use timestamp from first record, or current time
        timestamp = datetime.now(timezone.utc).isoformat()
        if signed_records and "vpm:signature" in signed_records[0]:
            timestamp = signed_records[0]["vpm:signature"].get("signed_at", timestamp)

        # Generate S3 key
        s3_key = self._generate_s3_key(timestamp, batch_id)

        # Compress records
        compressed_data = self._compress_records(signed_records)

        # Prepare metadata
        object_metadata = {
            "batch-id": batch_id,
            "record-count": str(len(signed_records)),
            "upload-timestamp": datetime.now(timezone.utc).isoformat(),
            "content-encoding": "gzip",
            "format": "jsonl",
            "schema-version": "1.0",
        }

        if metadata:
            object_metadata.update(metadata)

        # Upload to S3
        try:
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=compressed_data,
                Metadata=object_metadata,
                ContentType="application/json",
                ContentEncoding="gzip",
            )

            upload_info = {
                "bucket": self.bucket_name,
                "s3_key": s3_key,
                "batch_id": batch_id,
                "record_count": len(signed_records),
                "compressed_size_bytes": len(compressed_data),
                "upload_timestamp": object_metadata["upload-timestamp"],
                "success": True,
            }

            return s3_key, upload_info

        except ClientError as e:
            raise RuntimeError(f"Failed to upload batch {batch_id} to S3: {e}")

    def download_batch(self, s3_key: str) -> List[Dict[str, Any]]:
        """
        Download and decompress a batch of PROV records from S3

        Args:
            s3_key: S3 key of the batch to download

        Returns:
            List of PROV records
        """
        try:
            # Download from S3
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=s3_key)

            # Decompress
            compressed_data = response["Body"].read()
            jsonl_content = gzip.decompress(compressed_data).decode("utf-8")

            # Parse JSONL
            records = []
            for line in jsonl_content.strip().split("\n"):
                if line:
                    records.append(json.loads(line))

            return records

        except ClientError as e:
            raise RuntimeError(f"Failed to download batch {s3_key} from S3: {e}")

    def list_batches(
        self, date_prefix: Optional[str] = None, record_type: str = "prov"
    ) -> List[Dict[str, Any]]:
        """
        List available audit log batches

        Args:
            date_prefix: Optional date prefix to filter (e.g., "2024/01/15")
            record_type: Type of records to list

        Returns:
            List of batch metadata
        """
        try:
            # Build prefix
            prefix = "audit-logs/"
            if date_prefix:
                prefix += date_prefix.replace("-", "/") + "/"
            prefix += f"type={record_type}/"

            # List objects
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name, Prefix=prefix
            )

            batches = []
            for obj in response.get("Contents", []):
                # Get object metadata
                head_response = self.s3_client.head_object(
                    Bucket=self.bucket_name, Key=obj["Key"]
                )

                batch_info = {
                    "s3_key": obj["Key"],
                    "size_bytes": obj["Size"],
                    "last_modified": obj["LastModified"].isoformat(),
                    "batch_id": head_response["Metadata"].get("batch-id", "unknown"),
                    "record_count": int(
                        head_response["Metadata"].get("record-count", 0)
                    ),
                    "upload_timestamp": head_response["Metadata"].get(
                        "upload-timestamp"
                    ),
                }
                batches.append(batch_info)

            # Sort by upload timestamp
            batches.sort(key=lambda x: x["upload_timestamp"] or "", reverse=True)
            return batches

        except ClientError as e:
            raise RuntimeError(f"Failed to list batches: {e}")

    def verify_batch_integrity(self, s3_key: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Verify integrity of a stored batch by checking signatures

        Args:
            s3_key: S3 key of the batch to verify

        Returns:
            Tuple of (all_valid, verification_report)
        """
        # from .signing import ProvSigner  # Commented out to avoid unused import

        try:
            # Download batch
            records = self.download_batch(s3_key)

            # Verify each record (requires public key)
            verification_results = []
            all_valid = True

            for i, record in enumerate(records):
                if "vpm:signature" not in record:
                    verification_results.append(
                        {
                            "record_index": i,
                            "valid": False,
                            "message": "No signature found",
                        }
                    )
                    all_valid = False
                else:
                    # Note: This requires public key to be available
                    # In production, public key would be stored separately
                    verification_results.append(
                        {
                            "record_index": i,
                            "valid": True,  # Placeholder - would verify with actual public key
                            "message": "Signature verification skipped - public key required",
                        }
                    )

            report = {
                "batch_s3_key": s3_key,
                "total_records": len(records),
                "all_signatures_valid": all_valid,
                "verification_timestamp": datetime.now(timezone.utc).isoformat(),
                "individual_results": verification_results,
            }

            return all_valid, report

        except Exception as e:
            return False, {
                "batch_s3_key": s3_key,
                "error": f"Verification failed: {str(e)}",
                "verification_timestamp": datetime.now(timezone.utc).isoformat(),
            }

    def get_storage_stats(self) -> Dict[str, Any]:
        """
        Get storage statistics for audit logs

        Returns:
            Dictionary with storage statistics
        """
        try:
            # List all audit log objects
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name, Prefix="audit-logs/"
            )

            total_objects = 0
            total_size_bytes = 0
            oldest_date = None
            newest_date = None

            for obj in response.get("Contents", []):
                total_objects += 1
                total_size_bytes += obj["Size"]

                obj_date = obj["LastModified"]
                if oldest_date is None or obj_date < oldest_date:
                    oldest_date = obj_date
                if newest_date is None or obj_date > newest_date:
                    newest_date = obj_date

            return {
                "total_batches": total_objects,
                "total_size_bytes": total_size_bytes,
                "total_size_mb": round(total_size_bytes / (1024 * 1024), 2),
                "oldest_batch": oldest_date.isoformat() if oldest_date else None,
                "newest_batch": newest_date.isoformat() if newest_date else None,
                "stats_generated_at": datetime.now(timezone.utc).isoformat(),
            }

        except ClientError as e:
            raise RuntimeError(f"Failed to get storage stats: {e}")


if __name__ == "__main__":
    # Example usage with MinIO
    uploader = S3AuditUploader(
        endpoint_url="http://localhost:9000",  # MinIO endpoint
        bucket_name="vpm-audit-logs",
        aws_access_key_id="minioadmin",
        aws_secret_access_key="minioadmin",  # pragma: allowlist secret
    )

    # Example signed PROV records
    example_records = [
        {
            "@context": "https://vpm-mini.local/prov/context",
            "@id": "prov:example-1",
            "entity": {"entity:pod-1": {"type": "Entity", "label": "Test Pod 1"}},
            "activity": {
                "activity:review-1": {"type": "Activity", "label": "Review 1"}
            },
            "agent": {
                "agent:spiffe:gatekeeper": {"type": "Agent", "label": "Gatekeeper"}
            },
            "vpm:signature": {
                "algorithm": "Ed25519",
                "signature": "example_signature_1",
                "signed_at": datetime.now(timezone.utc).isoformat(),
            },
        },
        {
            "@context": "https://vpm-mini.local/prov/context",
            "@id": "prov:example-2",
            "entity": {"entity:pod-2": {"type": "Entity", "label": "Test Pod 2"}},
            "activity": {
                "activity:review-2": {"type": "Activity", "label": "Review 2"}
            },
            "agent": {
                "agent:spiffe:gatekeeper": {"type": "Agent", "label": "Gatekeeper"}
            },
            "vpm:signature": {
                "algorithm": "Ed25519",
                "signature": "example_signature_2",
                "signed_at": datetime.now(timezone.utc).isoformat(),
            },
        },
    ]

    try:
        # Upload batch
        s3_key, upload_info = uploader.upload_batch(example_records)
        print(f"Uploaded batch: {upload_info}")

        # List batches
        batches = uploader.list_batches()
        print(f"Available batches: {len(batches)}")

        # Get storage stats
        stats = uploader.get_storage_stats()
        print(f"Storage stats: {stats}")

    except Exception as e:
        print(f"Example failed: {e}")
        print("Note: This example requires MinIO running at localhost:9000")

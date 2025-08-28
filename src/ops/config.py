#!/usr/bin/env python3

import os
from pathlib import Path
from dataclasses import dataclass


@dataclass
class ProvOpsConfig:
    """Configuration class for PROV operations system"""

    # S3/MinIO Configuration
    s3_endpoint_url: str
    s3_bucket_name: str
    s3_access_key_id: str
    s3_secret_access_key: str
    s3_region: str

    # Digital Signing Configuration
    signing_private_key_path: str
    signing_public_key_path: str

    # PROV Schema Configuration
    prov_schema_path: str
    prov_context_path: str

    # Logging Configuration
    log_level: str
    log_format: str
    audit_log_path: str

    # Batch Processing Configuration
    batch_size: int
    batch_timeout_seconds: int
    compression_enabled: bool

    # SPIFFE/SPIRE Configuration
    spiffe_socket_path: str
    vpm_trust_domain: str

    # Application Configuration
    app_name: str
    app_version: str
    environment: str

    @classmethod
    def from_env(cls) -> "ProvOpsConfig":
        """Load configuration from environment variables"""
        return cls(
            # S3/MinIO Configuration
            s3_endpoint_url=os.getenv("S3_ENDPOINT_URL", "http://minio:9000"),
            s3_bucket_name=os.getenv("S3_BUCKET_NAME", "vpm-audit-logs"),
            s3_access_key_id=os.getenv("S3_ACCESS_KEY_ID", "vpm-audit"),
            s3_secret_access_key=os.getenv(
                "S3_SECRET_ACCESS_KEY", "vpm-audit-secret-key"
            ),
            s3_region=os.getenv("S3_REGION", "us-east-1"),
            # Digital Signing Configuration
            signing_private_key_path=os.getenv(
                "SIGNING_PRIVATE_KEY_PATH", "/config/keys/signing_key.pem"
            ),
            signing_public_key_path=os.getenv(
                "SIGNING_PUBLIC_KEY_PATH", "/config/keys/signing_key.pub"
            ),
            # PROV Schema Configuration
            prov_schema_path=os.getenv(
                "PROV_SCHEMA_PATH", "/app/schema/prov_event.schema.json"
            ),
            prov_context_path=os.getenv(
                "PROV_CONTEXT_PATH", "/app/schema/prov_context.json"
            ),
            # Logging Configuration
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            log_format=os.getenv("LOG_FORMAT", "json"),
            audit_log_path=os.getenv("AUDIT_LOG_PATH", "/var/log/prov/audit.log"),
            # Batch Processing Configuration
            batch_size=int(os.getenv("BATCH_SIZE", "100")),
            batch_timeout_seconds=int(os.getenv("BATCH_TIMEOUT_SECONDS", "300")),
            compression_enabled=os.getenv("COMPRESSION_ENABLED", "true").lower()
            == "true",
            # SPIFFE/SPIRE Configuration
            spiffe_socket_path=os.getenv(
                "SPIFFE_SOCKET_PATH", "/tmp/spire-agent/public/api.sock"
            ),
            vmp_trust_domain=os.getenv("VPM_TRUST_DOMAIN", "vpm-mini.local"),
            # Application Configuration
            app_name=os.getenv("APP_NAME", "vpm-prov-ops"),
            app_version=os.getenv("APP_VERSION", "1.0.0"),
            environment=os.getenv("ENVIRONMENT", "production"),
        )

    def validate(self) -> list:
        """Validate configuration and return list of errors"""
        errors = []

        # Check required paths exist
        if not Path(self.prov_schema_path).exists():
            errors.append(f"PROV schema file not found: {self.prov_schema_path}")

        if not Path(self.prov_context_path).exists():
            errors.append(f"PROV context file not found: {self.prov_context_path}")

        # Check signing key paths (they may not exist yet if we need to generate them)
        signing_key_dir = Path(self.signing_private_key_path).parent
        if not signing_key_dir.exists():
            try:
                signing_key_dir.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                errors.append(
                    f"Cannot create signing key directory {signing_key_dir}: {e}"
                )

        # Validate batch configuration
        if self.batch_size <= 0:
            errors.append("Batch size must be positive")

        if self.batch_timeout_seconds <= 0:
            errors.append("Batch timeout must be positive")

        # Validate log level
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.log_level.upper() not in valid_levels:
            errors.append(
                f"Invalid log level: {self.log_level}. Must be one of {valid_levels}"
            )

        return errors

    def get_s3_config(self) -> dict:
        """Get S3 configuration as dictionary"""
        return {
            "endpoint_url": self.s3_endpoint_url,
            "bucket_name": self.s3_bucket_name,
            "aws_access_key_id": self.s3_access_key_id,
            "aws_secret_access_key": self.s3_secret_access_key,
            "region_name": self.s3_region,
        }

    def get_signing_config(self) -> dict:
        """Get signing configuration as dictionary"""
        return {
            "private_key_path": self.signing_private_key_path,
            "public_key_path": self.signing_public_key_path,
        }


def load_config() -> ProvOpsConfig:
    """Load and validate configuration"""
    config = ProvOpsConfig.from_env()

    # Validate configuration
    errors = config.validate()
    if errors:
        raise ValueError(
            "Configuration validation failed:\n"
            + "\n".join(f"- {error}" for error in errors)
        )

    return config


if __name__ == "__main__":
    # Test configuration loading
    try:
        config = load_config()
        print("Configuration loaded successfully:")
        print(f"  App: {config.app_name} v{config.app_version}")
        print(f"  Environment: {config.environment}")
        print(f"  S3 Endpoint: {config.s3_endpoint_url}")
        print(f"  S3 Bucket: {config.s3_bucket_name}")
        print(f"  Batch Size: {config.batch_size}")
        print(f"  Log Level: {config.log_level}")
        print(f"  Trust Domain: {config.vpm_trust_domain}")
    except Exception as e:
        print(f"Configuration error: {e}")

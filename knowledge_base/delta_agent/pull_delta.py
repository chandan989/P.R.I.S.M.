"""
P.R.I.S.M. Knowledge Base Update Agent

Secure, batched delta-update protocol for maintaining clinical knowledge base
while maintaining zero-data-egress HIPAA compliance.

This agent runs nightly at 02:00 local time to pull encrypted delta bundles
from an upstream server, verify signatures, and apply updates to the local index.
"""

import os
import json
import hashlib
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import requests
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.exceptions import InvalidSignature

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('delta_update.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class DeltaUpdateAgent:
    """
    Manages secure delta updates for the P.R.I.S.M. knowledge base.

    The agent:
    1. Pulls encrypted delta bundles from upstream server
    2. Verifies Ed25519 signatures
    3. Decrypts AES-256-GCM payloads
    4. Applies atomic delta updates to local index
    5. Validates index integrity
    6. Writes audit logs
    """

    def __init__(self, config_path: str = "config.yaml"):
        """Initialize the delta update agent with configuration."""
        self.config = self._load_config(config_path)
        self.kb_root = Path(self.config['knowledge_base']['root_path'])
        self.index_path = self.kb_root / "index"
        self.sources_path = self.kb_root / "sources"
        self.audit_log_path = self.kb_root / "audit" / "updates.log"

        # Ensure directories exist
        self.audit_log_path.parent.mkdir(parents=True, exist_ok=True)

        # Load public key for signature verification
        self.public_key = self._load_public_key()

        # Load decryption key
        self.decryption_key = self._load_decryption_key()

    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from YAML file."""
        import yaml
        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            logger.warning(f"Config file {config_path} not found, using defaults")
            return self._default_config()

    def _default_config(self) -> Dict:
        """Return default configuration."""
        return {
            'knowledge_base': {
                'root_path': './knowledge_base',
                'max_staleness_days': 7
            },
            'upstream': {
                'url': 'https://upstream.example.com/delta',
                'verify_ssl': True
            },
            'update_schedule': {
                'enabled': True,
                'time': '02:00'
            }
        }

    def _load_public_key(self) -> ed25519.Ed25519PublicKey:
        """Load Ed25519 public key for signature verification."""
        key_path = Path(self.config.get('keys', {}).get('public_key_path', 'keys/public_key.pem'))
        try:
            with open(key_path, 'rb') as f:
                key_data = f.read()
            return serialization.load_pem_public_key(key_data)
        except FileNotFoundError:
            logger.error(f"Public key not found at {key_path}")
            raise

    def _load_decryption_key(self) -> bytes:
        """Load AES-256-GCM decryption key."""
        key_path = Path(self.config.get('keys', {}).get('decryption_key_path', 'keys/decryption_key.bin'))
        try:
            with open(key_path, 'rb') as f:
                return f.read()
        except FileNotFoundError:
            logger.error(f"Decryption key not found at {key_path}")
            raise

    def pull_delta_bundle(self) -> Optional[Dict]:
        """
        Pull the latest delta bundle from upstream server.

        Returns:
            Delta manifest if successful, None otherwise
        """
        upstream_url = self.config['upstream']['url']
        verify_ssl = self.config['upstream'].get('verify_ssl', True)

        try:
            logger.info(f"Pulling delta bundle from {upstream_url}")
            response = requests.get(
                upstream_url,
                verify=verify_ssl,
                timeout=300  # 5 minute timeout
            )
            response.raise_for_status()

            bundle = response.json()
            logger.info(f"Successfully pulled delta bundle with {len(bundle.get('deltas', []))} operations")
            return bundle

        except requests.RequestException as e:
            logger.error(f"Failed to pull delta bundle: {e}")
            return None

    def verify_signature(self, bundle: Dict) -> bool:
        """
        Verify Ed25519 signature of the delta bundle.

        Args:
            bundle: Delta bundle with signature field

        Returns:
            True if signature is valid, False otherwise
        """
        signature_str = bundle.get('signature', '')
        if not signature_str.startswith('ed25519:'):
            logger.error("Invalid signature format")
            return False

        signature_b64 = signature_str[8:]  # Remove 'ed25519:' prefix

        try:
            import base64
            signature = base64.b64decode(signature_b64)

            # Create message to verify (manifest without signature)
            message = json.dumps({
                k: v for k, v in bundle.items()
                if k != 'signature'
            }, sort_keys=True).encode()

            self.public_key.verify(signature, message)
            logger.info("Signature verification successful")
            return True

        except InvalidSignature:
            logger.error("Signature verification failed - bundle may be tampered")
            return False
        except Exception as e:
            logger.error(f"Error during signature verification: {e}")
            return False

    def decrypt_payload(self, encrypted_data: str) -> Optional[bytes]:
        """
        Decrypt AES-256-GCM encrypted payload.

        Args:
            encrypted_data: Base64-encoded encrypted data

        Returns:
            Decrypted bytes if successful, None otherwise
        """
        try:
            import base64
            encrypted = base64.b64decode(encrypted_data)

            # Extract nonce (first 12 bytes) and ciphertext
            nonce = encrypted[:12]
            ciphertext = encrypted[12:]

            aesgcm = AESGCM(self.decryption_key)
            decrypted = aesgcm.decrypt(nonce, ciphertext, None)

            logger.info("Payload decryption successful")
            return decrypted

        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            return None

    def apply_delta(self, delta: Dict) -> bool:
        """
        Apply a single delta operation to the local index.

        Args:
            delta: Delta operation (ADD, MODIFY, or REMOVE)

        Returns:
            True if successful, False otherwise
        """
        op = delta.get('op')
        doc_id = delta.get('doc_id')

        if op == 'ADD':
            return self._apply_add(delta)
        elif op == 'MODIFY':
            return self._apply_modify(delta)
        elif op == 'REMOVE':
            return self._apply_remove(delta)
        else:
            logger.error(f"Unknown operation: {op}")
            return False

    def _apply_add(self, delta: Dict) -> bool:
        """Add a new document to the knowledge base."""
        doc_id = delta['doc_id']
        source = delta['source']
        category = delta['category']

        # Determine target directory
        target_dir = self.sources_path / source.lower() / category
        target_dir.mkdir(parents=True, exist_ok=True)

        # Decrypt and write content
        encrypted_content = delta.get('encrypted_content')
        if not encrypted_content:
            logger.error(f"No encrypted content for ADD operation {doc_id}")
            return False

        decrypted = self.decrypt_payload(encrypted_content)
        if not decrypted:
            return False

        target_path = target_dir / f"{doc_id}.json"
        try:
            with open(target_path, 'wb') as f:
                f.write(decrypted)

            logger.info(f"Added document {doc_id} to {target_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to add document {doc_id}: {e}")
            return False

    def _apply_modify(self, delta: Dict) -> bool:
        """Modify an existing document in the knowledge base."""
        doc_id = delta['doc_id']

        # Find existing document
        existing_path = self._find_document(doc_id)
        if not existing_path:
            logger.error(f"Document {doc_id} not found for MODIFY operation")
            return False

        # Verify previous hash
        previous_hash = delta.get('previous_hash')
        if previous_hash:
            with open(existing_path, 'rb') as f:
                current_hash = hashlib.sha256(f.read()).hexdigest()
            if current_hash != previous_hash:
                logger.error(f"Hash mismatch for {doc_id}, refusing to modify")
                return False

        # Decrypt and write new content
        encrypted_content = delta.get('encrypted_content')
        if not encrypted_content:
            logger.error(f"No encrypted content for MODIFY operation {doc_id}")
            return False

        decrypted = self.decrypt_payload(encrypted_content)
        if not decrypted:
            return False

        try:
            with open(existing_path, 'wb') as f:
                f.write(decrypted)

            logger.info(f"Modified document {doc_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to modify document {doc_id}: {e}")
            return False

    def _apply_remove(self, delta: Dict) -> bool:
        """Remove a document from the knowledge base."""
        doc_id = delta['doc_id']
        reason = delta.get('reason', 'unknown')

        # Find and remove document
        existing_path = self._find_document(doc_id)
        if not existing_path:
            logger.warning(f"Document {doc_id} not found for REMOVE operation")
            return True  # Already removed

        try:
            os.remove(existing_path)
            logger.info(f"Removed document {doc_id} (reason: {reason})")
            return True

        except Exception as e:
            logger.error(f"Failed to remove document {doc_id}: {e}")
            return False

    def _find_document(self, doc_id: str) -> Optional[Path]:
        """Find a document by ID in the sources directory."""
        for source_dir in self.sources_path.iterdir():
            if source_dir.is_dir():
                for category_dir in source_dir.iterdir():
                    if category_dir.is_dir():
                        doc_path = category_dir / f"{doc_id}.json"
                        if doc_path.exists():
                            return doc_path
        return None

    def validate_index(self) -> bool:
        """
        Validate the integrity of the local index.

        Returns:
            True if index is valid, False otherwise
        """
        # Check if index directory exists
        if not self.index_path.exists():
            logger.warning("Index directory does not exist, will be created on next rebuild")
            return True

        # Count documents in sources
        doc_count = sum(1 for _ in self.sources_path.rglob('*.json'))

        # Load index metadata
        metadata_path = self.index_path / 'metadata.json'
        if metadata_path.exists():
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)

            if metadata.get('document_count') != doc_count:
                logger.error(f"Index document count mismatch: index={metadata.get('document_count')}, actual={doc_count}")
                return False

        logger.info(f"Index validation successful: {doc_count} documents")
        return True

    def write_audit_log(self, bundle: Dict, success: bool, error: Optional[str] = None):
        """
        Write an audit log entry for the update operation.

        Args:
            bundle: Delta bundle that was processed
            success: Whether the update was successful
            error: Error message if unsuccessful
        """
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'manifest_version': bundle.get('manifest_version'),
            'generated_at': bundle.get('generated_at'),
            'base_index_hash': bundle.get('base_index_hash'),
            'target_index_hash': bundle.get('target_index_hash'),
            'delta_count': len(bundle.get('deltas', [])),
            'success': success,
            'error': error
        }

        with open(self.audit_log_path, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')

        logger.info(f"Audit log entry written: success={success}")

    def check_staleness(self) -> Tuple[bool, int]:
        """
        Check if the knowledge base is stale.

        Returns:
            Tuple of (is_stale, days_since_update)
        """
        if not self.audit_log_path.exists():
            return True, 999  # Never updated

        # Read last audit log entry
        with open(self.audit_log_path, 'r') as f:
            lines = f.readlines()

        if not lines:
            return True, 999

        last_entry = json.loads(lines[-1])
        last_update = datetime.fromisoformat(last_entry['timestamp'])
        days_since = (datetime.utcnow() - last_update).days

        max_staleness = self.config['knowledge_base'].get('max_staleness_days', 7)
        is_stale = days_since > max_staleness

        return is_stale, days_since

    def run_update(self) -> bool:
        """
        Execute the complete delta update pipeline.

        Returns:
            True if update was successful, False otherwise
        """
        logger.info("Starting delta update process")

        # Pull delta bundle
        bundle = self.pull_delta_bundle()
        if not bundle:
            logger.error("Failed to pull delta bundle")
            return False

        # Verify signature
        if not self.verify_signature(bundle):
            logger.error("Signature verification failed, aborting update")
            self.write_audit_log(bundle, False, "Signature verification failed")
            return False

        # Apply deltas
        deltas = bundle.get('deltas', [])
        success_count = 0
        failure_count = 0

        for delta in deltas:
            if self.apply_delta(delta):
                success_count += 1
            else:
                failure_count += 1
                logger.error(f"Failed to apply delta: {delta}")

        logger.info(f"Applied {success_count} deltas, {failure_count} failures")

        # Validate index
        if not self.validate_index():
            logger.error("Index validation failed")
            self.write_audit_log(bundle, False, "Index validation failed")
            return False

        # Write audit log
        self.write_audit_log(bundle, failure_count == 0)

        if failure_count == 0:
            logger.info("Delta update completed successfully")
            return True
        else:
            logger.warning(f"Delta update completed with {failure_count} failures")
            return False


def main():
    """Main entry point for the delta update agent."""
    import argparse

    parser = argparse.ArgumentParser(description='P.R.I.S.M. Knowledge Base Delta Update Agent')
    parser.add_argument('--config', default='config.yaml', help='Path to configuration file')
    parser.add_argument('--check-staleness', action='store_true', help='Check if knowledge base is stale')
    parser.add_argument('--force', action='store_true', help='Force update regardless of schedule')

    args = parser.parse_args()

    agent = DeltaUpdateAgent(args.config)

    if args.check_staleness:
        is_stale, days = agent.check_staleness()
        if is_stale:
            print(f"⚠️  Knowledge base is stale: {days} days since last update")
            exit(1)
        else:
            print(f"✅ Knowledge base is current: {days} days since last update")
            exit(0)

    # Run update
    success = agent.run_update()
    exit(0 if success else 1)


if __name__ == '__main__':
    main()

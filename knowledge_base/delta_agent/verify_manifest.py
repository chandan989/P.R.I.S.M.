"""
P.R.I.S.M. Knowledge Base Manifest Verification

Handles Ed25519 signature verification and hash chain validation
for delta update bundles.
"""

import json
import hashlib
import logging
from pathlib import Path
from typing import Dict, Optional, Tuple
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.exceptions import InvalidSignature
import base64

logger = logging.getLogger(__name__)


class ManifestVerifier:
    """
    Verifies the integrity and authenticity of delta update manifests.

    Performs:
    1. Ed25519 signature verification
    2. Hash chain validation
    3. Schema validation
    4. Content hash verification
    """

    def __init__(self, public_key_path: str):
        """
        Initialize the manifest verifier.

        Args:
            public_key_path: Path to Ed25519 public key PEM file
        """
        self.public_key = self._load_public_key(public_key_path)

    def _load_public_key(self, key_path: str) -> ed25519.Ed25519PublicKey:
        """Load Ed25519 public key from PEM file."""
        try:
            with open(key_path, 'rb') as f:
                key_data = f.read()
            return serialization.load_pem_public_key(key_data)
        except FileNotFoundError:
            logger.error(f"Public key not found at {key_path}")
            raise
        except Exception as e:
            logger.error(f"Failed to load public key: {e}")
            raise

    def verify_signature(self, bundle: Dict) -> Tuple[bool, Optional[str]]:
        """
        Verify Ed25519 signature of the delta bundle.

        Args:
            bundle: Delta bundle with signature field

        Returns:
            Tuple of (is_valid, error_message)
        """
        signature_str = bundle.get('signature', '')
        if not signature_str:
            return False, "No signature present in bundle"

        if not signature_str.startswith('ed25519:'):
            return False, "Invalid signature format, expected 'ed25519:<base64>'"

        try:
            signature_b64 = signature_str[8:]  # Remove 'ed25519:' prefix
            signature = base64.b64decode(signature_b64)

            # Create message to verify (manifest without signature)
            message = json.dumps({
                k: v for k, v in bundle.items()
                if k != 'signature'
            }, sort_keys=True).encode()

            self.public_key.verify(signature, message)
            logger.info("Signature verification successful")
            return True, None

        except InvalidSignature:
            return False, "Signature verification failed - bundle may be tampered"
        except Exception as e:
            return False, f"Error during signature verification: {e}"

    def verify_hash_chain(self, bundle: Dict, current_index_hash: Optional[str] = None) -> Tuple[bool, Optional[str]]:
        """
        Verify the hash chain from current index to target index.

        Args:
            bundle: Delta bundle with base and target hashes
            current_index_hash: Current local index hash (if exists)

        Returns:
            Tuple of (is_valid, error_message)
        """
        base_hash = bundle.get('base_index_hash')
        target_hash = bundle.get('target_index_hash')

        if not base_hash or not target_hash:
            return False, "Missing base_index_hash or target_index_hash in bundle"

        # If we have a current index, verify it matches the base hash
        if current_index_hash:
            if current_index_hash != base_hash:
                return False, f"Hash chain mismatch: current={current_index_hash}, base={base_hash}"

        logger.info(f"Hash chain valid: {base_hash[:16]}... → {target_hash[:16]}...")
        return True, None

    def verify_schema(self, bundle: Dict) -> Tuple[bool, Optional[str]]:
        """
        Verify the bundle conforms to expected schema.

        Args:
            bundle: Delta bundle to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        required_fields = [
            'manifest_version',
            'generated_at',
            'base_index_hash',
            'target_index_hash',
            'signature',
            'deltas'
        ]

        for field in required_fields:
            if field not in bundle:
                return False, f"Missing required field: {field}"

        # Validate manifest version
        version = bundle['manifest_version']
        if not isinstance(version, str) or not version.startswith('1.'):
            return False, f"Unsupported manifest version: {version}"

        # Validate deltas array
        deltas = bundle['deltas']
        if not isinstance(deltas, list):
            return False, "Deltas must be an array"

        for i, delta in enumerate(deltas):
            valid, error = self._validate_delta(delta)
            if not valid:
                return False, f"Invalid delta at index {i}: {error}"

        logger.info(f"Schema validation successful: {len(deltas)} deltas")
        return True, None

    def _validate_delta(self, delta: Dict) -> Tuple[bool, Optional[str]]:
        """Validate a single delta operation."""
        op = delta.get('op')
        doc_id = delta.get('doc_id')

        if not op or not doc_id:
            return False, "Missing 'op' or 'doc_id' field"

        if op not in ['ADD', 'MODIFY', 'REMOVE']:
            return False, f"Invalid operation: {op}"

        # Operation-specific validation
        if op == 'ADD':
            required = ['source', 'category', 'content_hash', 'encrypted_content']
            for field in required:
                if field not in delta:
                    return False, f"ADD operation missing field: {field}"

        elif op == 'MODIFY':
            required = ['source', 'category', 'previous_hash', 'content_hash', 'encrypted_content']
            for field in required:
                if field not in delta:
                    return False, f"MODIFY operation missing field: {field}"

        elif op == 'REMOVE':
            if 'reason' not in delta:
                return False, "REMOVE operation missing 'reason' field"

        return True, None

    def verify_content_hashes(self, bundle: Dict) -> Tuple[bool, Optional[str]]:
        """
        Verify content hashes for all deltas in the bundle.

        Args:
            bundle: Delta bundle with content hashes

        Returns:
            Tuple of (is_valid, error_message)
        """
        deltas = bundle.get('deltas', [])

        for delta in deltas:
            op = delta.get('op')
            doc_id = delta.get('doc_id')

            if op in ['ADD', 'MODIFY']:
                encrypted_content = delta.get('encrypted_content')
                expected_hash = delta.get('content_hash')

                if not encrypted_content or not expected_hash:
                    return False, f"Missing encrypted_content or content_hash for {doc_id}"

                # Compute hash of encrypted content
                try:
                    content_bytes = base64.b64decode(encrypted_content)
                    actual_hash = hashlib.sha256(content_bytes).hexdigest()

                    if actual_hash != expected_hash:
                        return False, f"Content hash mismatch for {doc_id}: expected={expected_hash[:16]}..., actual={actual_hash[:16]}..."

                except Exception as e:
                    return False, f"Failed to compute content hash for {doc_id}: {e}"

        logger.info(f"Content hash verification successful: {len(deltas)} deltas")
        return True, None

    def verify_all(self, bundle: Dict, current_index_hash: Optional[str] = None) -> Tuple[bool, list]:
        """
        Perform all verification checks on the bundle.

        Args:
            bundle: Delta bundle to verify
            current_index_hash: Current local index hash (if exists)

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []

        # Schema validation
        valid, error = self.verify_schema(bundle)
        if not valid:
            errors.append(f"Schema: {error}")

        # Signature verification
        valid, error = self.verify_signature(bundle)
        if not valid:
            errors.append(f"Signature: {error}")

        # Hash chain validation
        valid, error = self.verify_hash_chain(bundle, current_index_hash)
        if not valid:
            errors.append(f"Hash chain: {error}")

        # Content hash verification
        valid, error = self.verify_content_hashes(bundle)
        if not valid:
            errors.append(f"Content hashes: {error}")

        is_valid = len(errors) == 0

        if is_valid:
            logger.info("All verification checks passed")
        else:
            logger.error(f"Verification failed with {len(errors)} errors")

        return is_valid, errors


def load_current_index_hash(index_path: Path) -> Optional[str]:
    """
    Load the current index hash from metadata file.

    Args:
        index_path: Path to the index directory

    Returns:
        Current index hash, or None if not found
    """
    metadata_path = index_path / 'metadata.json'

    if not metadata_path.exists():
        return None

    try:
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
        return metadata.get('current_hash')
    except Exception as e:
        logger.error(f"Failed to load current index hash: {e}")
        return None


def main():
    """Main entry point for manifest verification."""
    import argparse

    parser = argparse.ArgumentParser(description='P.R.I.S.M. Manifest Verification')
    parser.add_argument('bundle_path', help='Path to delta bundle JSON file')
    parser.add_argument('--public-key', default='keys/public_key.pem', help='Path to public key')
    parser.add_argument('--index-path', help='Path to current index directory')

    args = parser.parse_args()

    # Load bundle
    with open(args.bundle_path, 'r') as f:
        bundle = json.load(f)

    # Load current index hash
    current_hash = None
    if args.index_path:
        current_hash = load_current_index_hash(Path(args.index_path))

    # Verify
    verifier = ManifestVerifier(args.public_key)
    is_valid, errors = verifier.verify_all(bundle, current_hash)

    if is_valid:
        print("✅ Bundle verification successful")
        exit(0)
    else:
        print("❌ Bundle verification failed:")
        for error in errors:
            print(f"  - {error}")
        exit(1)


if __name__ == '__main__':
    main()

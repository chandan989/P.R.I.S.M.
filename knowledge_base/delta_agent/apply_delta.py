"""
P.R.I.S.M. Knowledge Base Delta Application

Handles atomic delta application with rollback support for the
clinical knowledge base.
"""

import os
import json
import shutil
import hashlib
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import tempfile

logger = logging.getLogger(__name__)


class DeltaApplier:
    """
    Applies delta operations to the local knowledge base with
    atomic updates and rollback support.

    Features:
    - Atomic operations (all-or-nothing)
    - Automatic rollback on failure
    - Backup creation before modification
    - Content hash verification
    """

    def __init__(self, kb_root: Path):
        """
        Initialize the delta applier.

        Args:
            kb_root: Root path of the knowledge base
        """
        self.kb_root = Path(kb_root)
        self.sources_path = self.kb_root / "sources"
        self.index_path = self.kb_root / "index"
        self.backup_path = self.kb_root / "backups"

        # Ensure directories exist
        self.backup_path.mkdir(parents=True, exist_ok=True)

    def apply_bundle(self, bundle: Dict, decryption_key: bytes) -> Tuple[bool, List[str]]:
        """
        Apply all deltas in a bundle atomically.

        Args:
            bundle: Delta bundle with deltas array
            decryption_key: AES-256-GCM decryption key

        Returns:
            Tuple of (success, list_of_errors)
        """
        deltas = bundle.get('deltas', [])
        errors = []

        if not deltas:
            logger.info("No deltas to apply")
            return True, []

        # Create backup before applying
        backup_id = self._create_backup()
        logger.info(f"Created backup: {backup_id}")

        try:
            # Apply each delta
            for i, delta in enumerate(deltas):
                success, error = self.apply_delta(delta, decryption_key)
                if not success:
                    errors.append(f"Delta {i} ({delta.get('doc_id')}): {error}")
                    logger.error(f"Failed to apply delta {i}: {error}")

                    # Rollback on failure
                    logger.info("Rolling back due to failure")
                    self._rollback(backup_id)
                    return False, errors

            # Update index metadata
            self._update_index_metadata(bundle)

            logger.info(f"Successfully applied {len(deltas)} deltas")
            return True, []

        except Exception as e:
            errors.append(f"Unexpected error: {e}")
            logger.error(f"Unexpected error during delta application: {e}")

            # Rollback on exception
            logger.info("Rolling back due to exception")
            self._rollback(backup_id)
            return False, errors

    def apply_delta(self, delta: Dict, decryption_key: bytes) -> Tuple[bool, Optional[str]]:
        """
        Apply a single delta operation.

        Args:
            delta: Delta operation (ADD, MODIFY, or REMOVE)
            decryption_key: AES-256-GCM decryption key

        Returns:
            Tuple of (success, error_message)
        """
        op = delta.get('op')
        doc_id = delta.get('doc_id')

        if op == 'ADD':
            return self._apply_add(delta, decryption_key)
        elif op == 'MODIFY':
            return self._apply_modify(delta, decryption_key)
        elif op == 'REMOVE':
            return self._apply_remove(delta)
        else:
            return False, f"Unknown operation: {op}"

    def _apply_add(self, delta: Dict, decryption_key: bytes) -> Tuple[bool, Optional[str]]:
        """Add a new document to the knowledge base."""
        doc_id = delta['doc_id']
        source = delta['source']
        category = delta['category']
        expected_hash = delta['content_hash']

        # Determine target directory
        target_dir = self.sources_path / source.lower() / category
        target_dir.mkdir(parents=True, exist_ok=True)

        # Check if document already exists
        target_path = target_dir / f"{doc_id}.json"
        if target_path.exists():
            return False, f"Document {doc_id} already exists"

        # Decrypt and write content
        encrypted_content = delta.get('encrypted_content')
        if not encrypted_content:
            return False, "No encrypted content provided"

        decrypted = self._decrypt_content(encrypted_content, decryption_key)
        if not decrypted:
            return False, "Failed to decrypt content"

        # Verify content hash
        actual_hash = hashlib.sha256(decrypted).hexdigest()
        if actual_hash != expected_hash:
            return False, f"Content hash mismatch: expected={expected_hash[:16]}..., actual={actual_hash[:16]}..."

        try:
            with open(target_path, 'wb') as f:
                f.write(decrypted)

            logger.info(f"Added document {doc_id} to {target_path}")
            return True, None

        except Exception as e:
            return False, f"Failed to write document: {e}"

    def _apply_modify(self, delta: Dict, decryption_key: bytes) -> Tuple[bool, Optional[str]]:
        """Modify an existing document in the knowledge base."""
        doc_id = delta['doc_id']
        source = delta['source']
        category = delta['category']
        previous_hash = delta['previous_hash']
        expected_hash = delta['content_hash']

        # Find existing document
        target_dir = self.sources_path / source.lower() / category
        target_path = target_dir / f"{doc_id}.json"

        if not target_path.exists():
            return False, f"Document {doc_id} not found"

        # Verify previous hash
        with open(target_path, 'rb') as f:
            current_content = f.read()
        current_hash = hashlib.sha256(current_content).hexdigest()

        if current_hash != previous_hash:
            return False, f"Hash mismatch: expected={previous_hash[:16]}..., actual={current_hash[:16]}..."

        # Decrypt and write new content
        encrypted_content = delta.get('encrypted_content')
        if not encrypted_content:
            return False, "No encrypted content provided"

        decrypted = self._decrypt_content(encrypted_content, decryption_key)
        if not decrypted:
            return False, "Failed to decrypt content"

        # Verify new content hash
        actual_hash = hashlib.sha256(decrypted).hexdigest()
        if actual_hash != expected_hash:
            return False, f"Content hash mismatch: expected={expected_hash[:16]}..., actual={actual_hash[:16]}..."

        try:
            with open(target_path, 'wb') as f:
                f.write(decrypted)

            logger.info(f"Modified document {doc_id}")
            return True, None

        except Exception as e:
            return False, f"Failed to write document: {e}"

    def _apply_remove(self, delta: Dict) -> Tuple[bool, Optional[str]]:
        """Remove a document from the knowledge base."""
        doc_id = delta['doc_id']
        reason = delta.get('reason', 'unknown')

        # Find and remove document
        existing_path = self._find_document(doc_id)
        if not existing_path:
            logger.warning(f"Document {doc_id} not found for REMOVE operation")
            return True, None  # Already removed

        try:
            os.remove(existing_path)

            # Clean up empty directories
            parent = existing_path.parent
            while parent != self.sources_path and not any(parent.iterdir()):
                parent.rmdir()
                parent = parent.parent

            logger.info(f"Removed document {doc_id} (reason: {reason})")
            return True, None

        except Exception as e:
            return False, f"Failed to remove document: {e}"

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

    def _decrypt_content(self, encrypted_content: str, decryption_key: bytes) -> Optional[bytes]:
        """
        Decrypt AES-256-GCM encrypted content.

        Args:
            encrypted_content: Base64-encoded encrypted data
            decryption_key: AES-256-GCM decryption key

        Returns:
            Decrypted bytes if successful, None otherwise
        """
        try:
            import base64
            from cryptography.hazmat.primitives.ciphers.aead import AESGCM

            encrypted = base64.b64decode(encrypted_content)

            # Extract nonce (first 12 bytes) and ciphertext
            nonce = encrypted[:12]
            ciphertext = encrypted[12:]

            aesgcm = AESGCM(decryption_key)
            decrypted = aesgcm.decrypt(nonce, ciphertext, None)

            return decrypted

        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            return None

    def _create_backup(self) -> str:
        """
        Create a backup of the current knowledge base state.

        Returns:
            Backup ID (timestamp-based)
        """
        backup_id = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        backup_dir = self.backup_path / backup_id

        # Copy sources directory
        if self.sources_path.exists():
            shutil.copytree(self.sources_path, backup_dir / 'sources')

        # Copy index metadata
        if self.index_path.exists():
            shutil.copytree(self.index_path, backup_dir / 'index')

        # Create backup manifest
        manifest = {
            'backup_id': backup_id,
            'created_at': datetime.utcnow().isoformat(),
            'document_count': sum(1 for _ in self.sources_path.rglob('*.json'))
        }

        with open(backup_dir / 'manifest.json', 'w') as f:
            json.dump(manifest, f, indent=2)

        logger.info(f"Created backup {backup_id}")
        return backup_id

    def _rollback(self, backup_id: str) -> bool:
        """
        Rollback to a previous backup.

        Args:
            backup_id: Backup ID to restore

        Returns:
            True if rollback was successful, False otherwise
        """
        backup_dir = self.backup_path / backup_id

        if not backup_dir.exists():
            logger.error(f"Backup {backup_id} not found")
            return False

        try:
            # Remove current sources
            if self.sources_path.exists():
                shutil.rmtree(self.sources_path)

            # Remove current index
            if self.index_path.exists():
                shutil.rmtree(self.index_path)

            # Restore from backup
            if (backup_dir / 'sources').exists():
                shutil.copytree(backup_dir / 'sources', self.sources_path)

            if (backup_dir / 'index').exists():
                shutil.copytree(backup_dir / 'index', self.index_path)

            logger.info(f"Successfully rolled back to backup {backup_id}")
            return True

        except Exception as e:
            logger.error(f"Rollback failed: {e}")
            return False

    def _update_index_metadata(self, bundle: Dict):
        """
        Update index metadata after successful delta application.

        Args:
            bundle: Delta bundle that was applied
        """
        self.index_path.mkdir(parents=True, exist_ok=True)

        # Count documents
        doc_count = sum(1 for _ in self.sources_path.rglob('*.json'))

        # Compute index hash
        index_hash = self._compute_index_hash()

        # Update metadata
        metadata_path = self.index_path / 'metadata.json'
        metadata = {
            'current_hash': bundle.get('target_index_hash', index_hash),
            'document_count': doc_count,
            'last_updated': datetime.utcnow().isoformat(),
            'manifest_version': bundle.get('manifest_version'),
            'delta_count': len(bundle.get('deltas', []))
        }

        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)

        logger.info(f"Updated index metadata: {doc_count} documents, hash={index_hash[:16]}...")

    def _compute_index_hash(self) -> str:
        """
        Compute a hash of the entire knowledge base.

        Returns:
            SHA256 hash of all document contents
        """
        hasher = hashlib.sha256()

        # Hash all documents in sorted order
        for doc_path in sorted(self.sources_path.rglob('*.json')):
            with open(doc_path, 'rb') as f:
                hasher.update(f.read())

        return hasher.hexdigest()

    def cleanup_old_backups(self, keep_count: int = 5):
        """
        Clean up old backups, keeping only the most recent ones.

        Args:
            keep_count: Number of recent backups to keep
        """
        backups = sorted(self.backup_path.iterdir(), reverse=True)

        for backup_dir in backups[keep_count:]:
            if backup_dir.is_dir():
                try:
                    shutil.rmtree(backup_dir)
                    logger.info(f"Removed old backup: {backup_dir.name}")
                except Exception as e:
                    logger.error(f"Failed to remove backup {backup_dir.name}: {e}")


def main():
    """Main entry point for delta application."""
    import argparse
    import yaml

    parser = argparse.ArgumentParser(description='P.R.I.S.M. Delta Application')
    parser.add_argument('bundle_path', help='Path to delta bundle JSON file')
    parser.add_argument('--kb-root', default='./knowledge_base', help='Knowledge base root path')
    parser.add_argument('--key-path', default='keys/decryption_key.bin', help='Decryption key path')
    parser.add_argument('--cleanup-backups', action='store_true', help='Clean up old backups')

    args = parser.parse_args()

    # Load decryption key
    with open(args.key_path, 'rb') as f:
        decryption_key = f.read()

    # Load bundle
    with open(args.bundle_path, 'r') as f:
        bundle = json.load(f)

    # Apply deltas
    applier = DeltaApplier(args.kb_root)
    success, errors = applier.apply_bundle(bundle, decryption_key)

    if success:
        print("✅ Delta application successful")

        # Cleanup old backups if requested
        if args.cleanup_backups:
            applier.cleanup_old_backups()

        exit(0)
    else:
        print("❌ Delta application failed:")
        for error in errors:
            print(f"  - {error}")
        exit(1)


if __name__ == '__main__':
    main()

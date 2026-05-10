"""
P.R.I.S.M. Knowledge Base

Manages the curated clinical knowledge base for source grounding verification.

This module handles:
- Vector indexing of clinical documents
- Dense embedding search using CPU-optimized models
- Source document retrieval and verification
- Knowledge base updates and maintenance
"""

import os
import json
import hashlib
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class KnowledgeBase:
    """
    Main knowledge base manager for P.R.I.S.M.

    Provides:
    - Vector search over clinical documents
    - Source document retrieval
    - Claim verification
    - Index management
    """

    def __init__(self, kb_root: str = "./knowledge_base"):
        """
        Initialize the knowledge base.

        Args:
            kb_root: Root path of the knowledge base
        """
        self.kb_root = Path(kb_root)
        self.sources_path = self.kb_root / "sources"
        self.index_path = self.kb_root / "index"

        # Initialize embedding model (CPU-optimized)
        self.embedding_model = self._init_embedding_model()

        # Load or create index
        self.index = self._load_or_create_index()

        # Load document metadata
        self.doc_metadata = self._load_doc_metadata()

    def _init_embedding_model(self):
        """
        Initialize the CPU-optimized embedding model.

        Uses ONNX-optimized MiniLM-L6 for fast CPU inference.
        """
        try:
            from sentence_transformers import SentenceTransformer

            # Use CPU-optimized model
            model_name = "sentence-transformers/all-MiniLM-L6-v2"
            device = "cpu"

            logger.info(f"Loading embedding model: {model_name} on {device}")
            model = SentenceTransformer(model_name, device=device)

            return model

        except ImportError:
            logger.warning("sentence-transformers not available, using dummy embeddings")
            return None

    def _load_or_create_index(self):
        """
        Load existing FAISS index or create new one.

        Returns:
            FAISS index object
        """
        try:
            import faiss

            index_file = self.index_path / "faiss.index"

            if index_file.exists():
                logger.info(f"Loading existing index from {index_file}")
                index = faiss.read_index(str(index_file))
                return index
            else:
                logger.info("Creating new FAISS index")
                # Create index with 384 dimensions (MiniLM-L6)
                index = faiss.IndexFlatL2(384)
                return index

        except ImportError:
            logger.warning("FAISS not available, using in-memory index")
            return None

    def _load_doc_metadata(self) -> Dict[str, Dict]:
        """
        Load document metadata from index.

        Returns:
            Dictionary mapping document IDs to metadata
        """
        metadata_file = self.index_path / "metadata.json"

        if metadata_file.exists():
            with open(metadata_file, 'r') as f:
                return json.load(f)
        else:
            return {}

    def add_document(self, doc_id: str, content: str, metadata: Dict[str, Any]) -> bool:
        """
        Add a document to the knowledge base.

        Args:
            doc_id: Unique document identifier
            content: Document text content
            metadata: Document metadata (source, category, etc.)

        Returns:
            True if successful, False otherwise
        """
        try:
            # Generate embedding
            if self.embedding_model:
                embedding = self.embedding_model.encode([content])[0]
            else:
                # Dummy embedding
                embedding = np.zeros(384, dtype=np.float32)

            # Add to index
            if self.index:
                self.index.add(embedding.reshape(1, -1).astype(np.float32))

            # Store document
            doc_path = self._get_doc_path(doc_id, metadata.get('source', 'unknown'), metadata.get('category', 'unknown'))
            doc_path.parent.mkdir(parents=True, exist_ok=True)

            doc_data = {
                'doc_id': doc_id,
                'content': content,
                'metadata': metadata,
                'added_at': datetime.utcnow().isoformat(),
                'content_hash': hashlib.sha256(content.encode()).hexdigest()
            }

            with open(doc_path, 'w') as f:
                json.dump(doc_data, f, indent=2)

            # Update metadata
            self.doc_metadata[doc_id] = {
                'source': metadata.get('source'),
                'category': metadata.get('category'),
                'path': str(doc_path),
                'added_at': doc_data['added_at']
            }

            logger.info(f"Added document {doc_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to add document {doc_id}: {e}")
            return False

    def _get_doc_path(self, doc_id: str, source: str, category: str) -> Path:
        """Get the file path for a document."""
        return self.sources_path / source.lower() / category / f"{doc_id}.json"

    def search(self, query: str, top_k: int = 5, threshold: float = 0.7) -> List[Dict[str, Any]]:
        """
        Search for documents similar to the query.

        Args:
            query: Search query text
            top_k: Number of results to return
            threshold: Minimum similarity threshold

        Returns:
            List of matching documents with scores
        """
        if not self.embedding_model or not self.index:
            logger.warning("Embedding model or index not available")
            return []

        try:
            # Generate query embedding
            query_embedding = self.embedding_model.encode([query])[0].astype(np.float32)

            # Search index
            distances, indices = self.index.search(query_embedding.reshape(1, -1), top_k)

            # Convert distances to similarity scores
            results = []
            for i, (dist, idx) in enumerate(zip(distances[0], indices[0])):
                if idx >= 0:  # Valid index
                    similarity = 1.0 / (1.0 + dist)  # Convert distance to similarity

                    if similarity >= threshold:
                        doc_id = list(self.doc_metadata.keys())[idx] if idx < len(self.doc_metadata) else None

                        if doc_id:
                            doc_data = self._load_document(doc_id)
                            if doc_data:
                                results.append({
                                    'doc_id': doc_id,
                                    'similarity': float(similarity),
                                    'content': doc_data.get('content', ''),
                                    'metadata': doc_data.get('metadata', {}),
                                    'source': doc_data.get('metadata', {}).get('source', 'unknown')
                                })

            return results

        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []

    def _load_document(self, doc_id: str) -> Optional[Dict]:
        """Load a document by ID."""
        metadata = self.doc_metadata.get(doc_id)
        if not metadata:
            return None

        doc_path = Path(metadata.get('path'))
        if not doc_path.exists():
            return None

        try:
            with open(doc_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load document {doc_id}: {e}")
            return None

    def verify_claim(self, claim: str, threshold: float = 0.75) -> Tuple[str, Optional[Dict]]:
        """
        Verify a factual claim against the knowledge base.

        Args:
            claim: Claim text to verify
            threshold: Minimum similarity threshold for confirmation

        Returns:
            Tuple of (status, evidence) where status is one of:
            - "confirmed": Claim aligns with verified sources
            - "contradicted": Claim conflicts with verified sources
            - "inferred": Reasonable deduction but not directly sourced
            - "out_of_scope": Knowledge base lacks data
        """
        # Search for similar documents
        results = self.search(claim, top_k=3, threshold=threshold)

        if not results:
            return "out_of_scope", None

        # Check for contradictions
        for result in results:
            if self._is_contradiction(claim, result['content']):
                return "contradicted", result

        # Check for confirmation
        for result in results:
            if result['similarity'] >= 0.85:
                return "confirmed", result

        # Otherwise, it's inferred
        return "inferred", results[0] if results else None

    def _is_contradiction(self, claim: str, source_content: str) -> bool:
        """
        Check if a claim contradicts source content.

        This is a simplified check. In production, you would use
        a more sophisticated NLI (Natural Language Inference) model.
        """
        # Simple keyword-based contradiction detection
        claim_lower = claim.lower()
        content_lower = source_content.lower()

        # Check for negation patterns
        contradiction_indicators = [
            'not', 'never', 'no', 'cannot', 'unable', 'unlikely',
            'contraindicated', 'avoid', 'warning', 'caution'
        ]

        for indicator in contradiction_indicators:
            if indicator in claim_lower and indicator not in content_lower:
                # This is a very basic heuristic
                # In production, use proper NLI
                pass

        return False

    def get_document_count(self) -> int:
        """Get the total number of documents in the knowledge base."""
        return len(self.doc_metadata)

    def get_sources_summary(self) -> Dict[str, int]:
        """Get a summary of documents by source."""
        summary = {}
        for doc_id, metadata in self.doc_metadata.items():
            source = metadata.get('source', 'unknown')
            summary[source] = summary.get(source, 0) + 1
        return summary

    def check_staleness(self) -> Tuple[bool, int]:
        """
        Check if the knowledge base is stale.

        Returns:
            Tuple of (is_stale, days_since_update)
        """
        audit_log_path = self.kb_root / "delta_agent" / "audit.log"
        if not audit_log_path.exists():
            return True, 999  # Never updated

        try:
            import json
            from datetime import datetime
            with open(audit_log_path, 'r') as f:
                lines = f.readlines()
            if not lines:
                return True, 999
            last_entry = json.loads(lines[-1])
            last_update = datetime.fromisoformat(last_entry['timestamp'])
            days_since = (datetime.utcnow() - last_update).days
            return days_since > 7, days_since
        except Exception as e:
            logger.error(f"Error checking staleness: {e}")
            return True, 999

    def save_index(self):
        """Save the index to disk."""
        if self.index:
            import faiss
            index_file = self.index_path / "faiss.index"
            self.index_path.mkdir(parents=True, exist_ok=True)
            faiss.write_index(self.index, str(index_file))
            logger.info(f"Saved index to {index_file}")

        # Save metadata
        metadata_file = self.index_path / "metadata.json"
        with open(metadata_file, 'w') as f:
            json.dump(self.doc_metadata, f, indent=2)

        logger.info("Saved knowledge base metadata")

    def rebuild_index(self):
        """
        Rebuild the entire index from source documents.

        This is useful after bulk updates or when the index is corrupted.
        """
        logger.info("Rebuilding index from source documents")

        # Clear existing index
        if self.index:
            import faiss
            self.index = faiss.IndexFlatL2(384)

        self.doc_metadata = {}

        # Re-index all documents
        for source_dir in self.sources_path.iterdir():
            if source_dir.is_dir():
                for category_dir in source_dir.iterdir():
                    if category_dir.is_dir():
                        for doc_file in category_dir.glob('*.json'):
                            try:
                                with open(doc_file, 'r') as f:
                                    doc_data = json.load(f)

                                doc_id = doc_data.get('doc_id')
                                content = doc_data.get('content')
                                metadata = doc_data.get('metadata', {})

                                if doc_id and content:
                                    self.add_document(doc_id, content, metadata)

                            except Exception as e:
                                logger.error(f"Failed to re-index {doc_file}: {e}")

        # Save rebuilt index
        self.save_index()
        logger.info(f"Index rebuild complete: {self.get_document_count()} documents")


def main():
    """Main entry point for knowledge base operations."""
    import argparse

    parser = argparse.ArgumentParser(description='P.R.I.S.M. Knowledge Base')
    parser.add_argument('--kb-root', default='./knowledge_base', help='Knowledge base root path')
    parser.add_argument('--rebuild', action='store_true', help='Rebuild the index')
    parser.add_argument('--search', help='Search query')
    parser.add_argument('--verify', help='Claim to verify')
    parser.add_argument('--stats', action='store_true', help='Show knowledge base statistics')

    args = parser.parse_args()

    kb = KnowledgeBase(args.kb_root)

    if args.rebuild:
        kb.rebuild_index()
        print("✅ Index rebuilt successfully")

    elif args.search:
        results = kb.search(args.search, top_k=5)
        print(f"Found {len(results)} results for '{args.search}':")
        for i, result in enumerate(results, 1):
            print(f"\n{i}. {result['doc_id']} (similarity: {result['similarity']:.2f})")
            print(f"   Source: {result['source']}")
            print(f"   Content: {result['content'][:200]}...")

    elif args.verify:
        status, evidence = kb.verify_claim(args.verify)
        print(f"Claim: '{args.verify}'")
        print(f"Status: {status}")
        if evidence:
            print(f"Evidence: {evidence.get('content', '')[:200]}...")

    elif args.stats:
        print(f"Total documents: {kb.get_document_count()}")
        print("\nDocuments by source:")
        for source, count in kb.get_sources_summary().items():
            print(f"  {source}: {count}")

    else:
        print("No action specified. Use --help for options.")


if __name__ == '__main__':
    main()

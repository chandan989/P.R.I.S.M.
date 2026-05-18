#!/usr/bin/env python3
"""
P.R.I.S.M. Knowledge Base Index Builder

Scans all source documents under knowledge_base/sources/ and builds a FAISS
index with MiniLM-L6-v2 embeddings. Can optionally pull additional abstracts
from PubMed E-utilities API.

Usage:
    python build_index.py                  # Index local sources
    python build_index.py --pull-pubmed    # Also pull fresh PubMed abstracts
    python build_index.py --stats          # Show index statistics
"""

import os
import sys
import json
import hashlib
import argparse
import logging
from pathlib import Path
from datetime import datetime

import numpy as np

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
logger = logging.getLogger(__name__)

KB_ROOT = Path(__file__).resolve().parent
SOURCES_DIR = KB_ROOT / "sources"
INDEX_DIR = KB_ROOT / "index"
EMBEDDING_DIM = 384  # MiniLM-L6-v2 output dimension


def load_embedding_model():
    """Load the CPU-optimized sentence-transformers model."""
    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2", device="cpu")
        logger.info("✅ Loaded MiniLM-L6-v2 embedding model (CPU)")
        return model
    except ImportError:
        logger.warning("⚠ sentence-transformers not installed — using random embeddings (demo only)")
        return None


def scan_source_documents() -> list:
    """Recursively find all .json source documents."""
    docs = []
    for json_file in SOURCES_DIR.rglob("*.json"):
        if json_file.name == "README.md":
            continue
        try:
            with open(json_file, "r") as f:
                data = json.load(f)
            if "doc_id" in data and "content" in data:
                data["_path"] = str(json_file)
                docs.append(data)
        except Exception as e:
            logger.warning(f"Skipping {json_file}: {e}")
    return docs


def build_index(docs: list, model):
    """Build FAISS index and metadata from documents."""
    try:
        import faiss
    except ImportError:
        logger.error("❌ faiss-cpu not installed. Run: pip install faiss-cpu")
        sys.exit(1)

    index = faiss.IndexFlatIP(EMBEDDING_DIM)  # Inner product (cosine after normalization)
    metadata = {}

    texts = [doc["content"] for doc in docs]

    if model:
        logger.info(f"Encoding {len(texts)} documents...")
        embeddings = model.encode(texts, show_progress_bar=True, normalize_embeddings=True)
    else:
        embeddings = np.random.randn(len(texts), EMBEDDING_DIM).astype(np.float32)
        # Normalize for cosine similarity
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        embeddings = embeddings / norms

    index.add(embeddings.astype(np.float32))

    for i, doc in enumerate(docs):
        doc_id = doc["doc_id"]
        meta = doc.get("metadata", {})
        metadata[doc_id] = {
            "source": meta.get("source", "unknown"),
            "category": meta.get("category", "unknown"),
            "path": doc["_path"],
            "added_at": doc.get("added_at", datetime.utcnow().isoformat()),
        }

    return index, metadata


def save_index(index, metadata):
    """Save FAISS index and metadata to disk."""
    import faiss

    INDEX_DIR.mkdir(parents=True, exist_ok=True)

    faiss.write_index(index, str(INDEX_DIR / "faiss.index"))
    with open(INDEX_DIR / "metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)

    logger.info(f"✅ Saved index ({index.ntotal} vectors) to {INDEX_DIR}")


def pull_pubmed(query: str = "polypharmacy drug interactions elderly", max_results: int = 5):
    """Pull abstracts from PubMed E-utilities API."""
    try:
        import urllib.request
        import xml.etree.ElementTree as ET

        logger.info(f"Searching PubMed for: '{query}'")

        # Step 1: Search
        search_url = (
            f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
            f"?db=pubmed&term={urllib.parse.quote(query)}&retmax={max_results}&sort=date&retmode=json"
        )
        with urllib.request.urlopen(search_url, timeout=10) as resp:
            search_data = json.loads(resp.read())

        id_list = search_data.get("esearchresult", {}).get("idlist", [])
        if not id_list:
            logger.warning("No PubMed results found")
            return []

        # Step 2: Fetch abstracts
        ids_str = ",".join(id_list)
        fetch_url = (
            f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
            f"?db=pubmed&id={ids_str}&rettype=abstract&retmode=xml"
        )
        with urllib.request.urlopen(fetch_url, timeout=15) as resp:
            xml_text = resp.read()

        root = ET.fromstring(xml_text)
        docs = []
        for article in root.findall(".//PubmedArticle"):
            pmid = article.findtext(".//PMID", "")
            title = article.findtext(".//ArticleTitle", "")
            abstract = article.findtext(".//AbstractText", "")
            journal = article.findtext(".//Journal/Title", "")
            year = article.findtext(".//PubDate/Year", "")

            if abstract:
                doc = {
                    "doc_id": f"pubmed_live_{pmid}",
                    "content": f"Title: {title}. Journal: {journal}. PMID: {pmid}. Year: {year}. Abstract: {abstract}",
                    "metadata": {
                        "source": "PubMed",
                        "category": "live_pull",
                        "pmid": pmid,
                        "journal": journal,
                        "year": int(year) if year else 0,
                        "last_updated": datetime.utcnow().strftime("%Y-%m-%d"),
                    },
                    "added_at": datetime.utcnow().isoformat(),
                    "content_hash": hashlib.sha256(abstract.encode()).hexdigest(),
                }
                # Save to disk
                out_dir = SOURCES_DIR / "pubmed" / "live"
                out_dir.mkdir(parents=True, exist_ok=True)
                with open(out_dir / f"{pmid}.json", "w") as f:
                    json.dump(doc, f, indent=2)

                docs.append(doc)
                logger.info(f"  Fetched PMID {pmid}: {title[:60]}...")

        return docs

    except Exception as e:
        logger.warning(f"PubMed pull failed (offline?): {e}")
        return []


def show_stats():
    """Show knowledge base statistics."""
    metadata_file = INDEX_DIR / "metadata.json"
    if not metadata_file.exists():
        print("No index found. Run build_index.py first.")
        return

    with open(metadata_file) as f:
        metadata = json.load(f)

    print(f"\n📊 Knowledge Base Statistics")
    print(f"   Total documents: {len(metadata)}")
    print(f"\n   Documents by source:")
    sources = {}
    for doc_id, meta in metadata.items():
        src = meta.get("source", "unknown")
        sources[src] = sources.get(src, 0) + 1
    for src, count in sorted(sources.items()):
        print(f"     {src}: {count}")
    print()


def main():
    parser = argparse.ArgumentParser(description="P.R.I.S.M. Knowledge Base Index Builder")
    parser.add_argument("--pull-pubmed", action="store_true", help="Pull fresh abstracts from PubMed")
    parser.add_argument("--stats", action="store_true", help="Show index statistics")
    args = parser.parse_args()

    if args.stats:
        show_stats()
        return

    # Load model
    model = load_embedding_model()

    # Scan local sources
    docs = scan_source_documents()
    logger.info(f"Found {len(docs)} local source documents")

    # Optionally pull from PubMed
    if args.pull_pubmed:
        import urllib.parse
        pubmed_docs = pull_pubmed("polypharmacy drug interactions CYP3A4 elderly", max_results=5)
        # Re-scan to include newly saved docs
        docs = scan_source_documents()
        logger.info(f"Total after PubMed pull: {len(docs)} documents")

    if not docs:
        logger.error("No source documents found!")
        return

    # Build and save index
    index, metadata = build_index(docs, model)
    save_index(index, metadata)

    # Show summary
    show_stats()


if __name__ == "__main__":
    main()

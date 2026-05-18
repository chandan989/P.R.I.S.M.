#!/usr/bin/env python3
"""
P.R.I.S.M. Knowledge Base Populator

Automatically pulls clinical data from public APIs and populates the
knowledge base source documents. No API keys required.

Sources:
  - PubMed E-utilities   (abstracts via esearch + efetch)
  - OpenFDA Drug Labels   (drug interactions, warnings, contraindications)

Usage:
    python populate_kb.py                       # Pull from all sources
    python populate_kb.py --pubmed-only         # PubMed only
    python populate_kb.py --openfda-only        # OpenFDA only
    python populate_kb.py --dry-run             # Show what would be fetched
"""

import os
import json
import hashlib
import argparse
import logging
import time
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
logger = logging.getLogger(__name__)

KB_ROOT = Path(__file__).resolve().parent
SOURCES_DIR = KB_ROOT / "sources"

# ── SSL context (macOS workaround) ─────────────────────────────────────
import ssl
_SSL_CTX = None
try:
    _SSL_CTX = ssl.create_default_context()
    # Test if default context works
    urllib.request.urlopen("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/einfo.fcgi", timeout=5, context=_SSL_CTX)
except Exception:
    # Default context failed (common on macOS), use unverified
    _SSL_CTX = ssl.create_default_context()
    _SSL_CTX.check_hostname = False
    _SSL_CTX.verify_mode = ssl.CERT_NONE
    logger.warning("⚠ Using unverified SSL context (macOS cert issue — safe for public APIs)")

# ── Rate limiting ──────────────────────────────────────────────────────
# NCBI allows 3 requests/second without an API key, 10 with.
# OpenFDA allows 240 requests/minute without a key.
PUBMED_DELAY = 0.4   # seconds between PubMed requests
OPENFDA_DELAY = 0.3  # seconds between OpenFDA requests


# ═══════════════════════════════════════════════════════════════════════
#  PubMed E-utilities
# ═══════════════════════════════════════════════════════════════════════

PUBMED_QUERIES = [
    # Core polypharmacy / DDI queries
    "polypharmacy drug interactions elderly adverse events",
    "CYP3A4 drug drug interactions clinical significance",
    "warfarin drug interactions bleeding risk management",
    "statin rhabdomyolysis CYP3A4 inhibitor risk",
    "SSRI serotonin syndrome drug interactions",
    "ACE inhibitor hyperkalemia potassium drug interaction",
    "metformin lactic acidosis renal impairment",
    "proton pump inhibitor clopidogrel interaction cardiovascular",
    "beta blocker CYP2D6 metabolism drug interaction",
    "anticoagulant antibiotic interaction INR monitoring",
    "QT prolongation drug interactions polypharmacy",
    "NSAID renal function ACE inhibitor triple whammy",
]


def pubmed_search(query: str, max_results: int = 5) -> List[str]:
    """Search PubMed and return a list of PMIDs."""
    url = (
        "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
        f"?db=pubmed&term={urllib.parse.quote(query)}"
        f"&retmax={max_results}&sort=relevance&retmode=json"
    )
    try:
        with urllib.request.urlopen(url, timeout=15, context=_SSL_CTX) as resp:
            data = json.loads(resp.read())
        return data.get("esearchresult", {}).get("idlist", [])
    except Exception as e:
        logger.warning(f"PubMed search failed for '{query[:40]}...': {e}")
        return []


def pubmed_fetch(pmids: List[str]) -> List[Dict]:
    """Fetch article details for a list of PMIDs."""
    if not pmids:
        return []

    ids_str = ",".join(pmids)
    url = (
        "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
        f"?db=pubmed&id={ids_str}&rettype=abstract&retmode=xml"
    )
    try:
        with urllib.request.urlopen(url, timeout=20, context=_SSL_CTX) as resp:
            xml_bytes = resp.read()
    except Exception as e:
        logger.warning(f"PubMed fetch failed: {e}")
        return []

    articles = []
    try:
        root = ET.fromstring(xml_bytes)
        for article_el in root.findall(".//PubmedArticle"):
            pmid = article_el.findtext(".//PMID", "").strip()
            title = article_el.findtext(".//ArticleTitle", "").strip()
            journal = article_el.findtext(".//Journal/Title", "").strip()
            year = article_el.findtext(".//PubDate/Year", "").strip()

            # Abstract can be in multiple AbstractText elements
            abstract_parts = []
            for at in article_el.findall(".//AbstractText"):
                label = at.get("Label", "")
                text = (at.text or "").strip()
                if text:
                    if label:
                        abstract_parts.append(f"{label}: {text}")
                    else:
                        abstract_parts.append(text)

            abstract = " ".join(abstract_parts)
            if not abstract:
                continue

            # Build combined content
            content = f"Title: {title}. Journal: {journal}. PMID: {pmid}. Year: {year}. Abstract: {abstract}"

            articles.append({
                "pmid": pmid,
                "title": title,
                "journal": journal,
                "year": year,
                "abstract": abstract,
                "content": content,
            })
    except ET.ParseError as e:
        logger.warning(f"XML parse error: {e}")

    return articles


def pull_pubmed(max_per_query: int = 3, dry_run: bool = False) -> int:
    """Pull abstracts from PubMed for all configured queries."""
    out_dir = SOURCES_DIR / "pubmed"
    out_dir.mkdir(parents=True, exist_ok=True)

    seen_pmids = set()
    total_saved = 0

    for query in PUBMED_QUERIES:
        logger.info(f"  PubMed search: '{query[:50]}...'")
        pmids = pubmed_search(query, max_results=max_per_query)
        # Filter already seen
        new_pmids = [p for p in pmids if p not in seen_pmids]
        seen_pmids.update(new_pmids)

        if not new_pmids:
            continue

        time.sleep(PUBMED_DELAY)

        articles = pubmed_fetch(new_pmids)
        time.sleep(PUBMED_DELAY)

        for article in articles:
            pmid = article["pmid"]
            doc_id = f"pubmed_{pmid}"
            out_file = out_dir / f"{pmid}.json"

            if out_file.exists():
                logger.debug(f"    Skip {pmid} (already exists)")
                continue

            if dry_run:
                logger.info(f"    [DRY RUN] Would save PMID {pmid}: {article['title'][:60]}...")
                total_saved += 1
                continue

            doc = {
                "doc_id": doc_id,
                "content": article["content"],
                "metadata": {
                    "source": "PubMed",
                    "category": "abstract",
                    "pmid": pmid,
                    "journal": article["journal"],
                    "year": int(article["year"]) if article["year"].isdigit() else 0,
                    "title": article["title"],
                    "last_updated": datetime.utcnow().strftime("%Y-%m-%d"),
                },
                "added_at": datetime.utcnow().isoformat(),
                "content_hash": hashlib.sha256(article["content"].encode()).hexdigest(),
            }

            with open(out_file, "w") as f:
                json.dump(doc, f, indent=2)

            logger.info(f"    ✅ Saved PMID {pmid}: {article['title'][:60]}...")
            total_saved += 1

    return total_saved


# ═══════════════════════════════════════════════════════════════════════
#  OpenFDA Drug Labels
# ═══════════════════════════════════════════════════════════════════════

# Drugs commonly involved in polypharmacy interactions
OPENFDA_DRUGS = [
    "warfarin",
    "clarithromycin",
    "atorvastatin",
    "simvastatin",
    "metformin",
    "lisinopril",
    "metoprolol",
    "omeprazole",
    "sertraline",
    "fluoxetine",
    "amlodipine",
    "clopidogrel",
    "digoxin",
    "amiodarone",
    "gabapentin",
    "levothyroxine",
    "furosemide",
    "spironolactone",
    "prednisone",
    "allopurinol",
]


def openfda_fetch_label(drug_name: str) -> Optional[Dict]:
    """Fetch drug label data from OpenFDA."""
    url = (
        "https://api.fda.gov/drug/label.json"
        f"?search=openfda.generic_name:\"{urllib.parse.quote(drug_name)}\""
        "&limit=1"
    )
    try:
        with urllib.request.urlopen(url, timeout=15, context=_SSL_CTX) as resp:
            data = json.loads(resp.read())

        results = data.get("results", [])
        if not results:
            return None

        label = results[0]

        # Extract key sections
        sections = {}
        for field in [
            "drug_interactions",
            "warnings",
            "contraindications",
            "clinical_pharmacology",
            "adverse_reactions",
            "dosage_and_administration",
        ]:
            val = label.get(field)
            if val:
                if isinstance(val, list):
                    sections[field] = " ".join(val)[:2000]
                else:
                    sections[field] = str(val)[:2000]

        if not sections:
            return None

        # Get brand name and NDC
        openfda = label.get("openfda", {})
        brand_name = openfda.get("brand_name", [drug_name.title()])
        if isinstance(brand_name, list):
            brand_name = brand_name[0] if brand_name else drug_name.title()

        return {
            "drug_name": drug_name,
            "brand_name": brand_name,
            "sections": sections,
            "openfda": openfda,
        }

    except urllib.error.HTTPError as e:
        if e.code == 404:
            logger.debug(f"    No FDA label found for {drug_name}")
        else:
            logger.warning(f"    OpenFDA error for {drug_name}: {e}")
        return None
    except Exception as e:
        logger.warning(f"    OpenFDA fetch failed for {drug_name}: {e}")
        return None


def pull_openfda(dry_run: bool = False) -> int:
    """Pull drug labels from OpenFDA for all configured drugs."""
    total_saved = 0

    for drug_name in OPENFDA_DRUGS:
        logger.info(f"  OpenFDA: {drug_name}")

        # Save interactions as FDA source
        label = openfda_fetch_label(drug_name)
        time.sleep(OPENFDA_DELAY)

        if not label:
            continue

        sections = label["sections"]

        # Save drug_interactions section
        if "drug_interactions" in sections:
            doc_id = f"fda_{drug_name}_interactions"
            out_dir = SOURCES_DIR / "fda" / "interactions"
            out_dir.mkdir(parents=True, exist_ok=True)
            out_file = out_dir / f"{drug_name}_interactions_openfda.json"

            if not out_file.exists() or True:  # Always update from live API
                content = f"{label['brand_name']} ({drug_name}) — FDA Drug Interactions: {sections['drug_interactions']}"

                if not dry_run:
                    doc = {
                        "doc_id": doc_id,
                        "content": content,
                        "metadata": {
                            "source": "FDA",
                            "category": "interactions",
                            "drug": drug_name,
                            "brand_name": label["brand_name"],
                            "last_updated": datetime.utcnow().strftime("%Y-%m-%d"),
                            "api_source": "OpenFDA",
                        },
                        "added_at": datetime.utcnow().isoformat(),
                        "content_hash": hashlib.sha256(content.encode()).hexdigest(),
                    }
                    with open(out_file, "w") as f:
                        json.dump(doc, f, indent=2)
                    logger.info(f"    ✅ Saved FDA interactions for {drug_name}")
                else:
                    logger.info(f"    [DRY RUN] Would save FDA interactions for {drug_name}")
                total_saved += 1

        # Save contraindications as FDA source
        if "contraindications" in sections:
            doc_id = f"fda_{drug_name}_contraindications"
            out_dir = SOURCES_DIR / "fda" / "contraindications"
            out_dir.mkdir(parents=True, exist_ok=True)
            out_file = out_dir / f"{drug_name}_contraindications_openfda.json"

            if not out_file.exists() or True:
                content = f"{label['brand_name']} ({drug_name}) — FDA Contraindications: {sections['contraindications']}"

                if not dry_run:
                    doc = {
                        "doc_id": doc_id,
                        "content": content,
                        "metadata": {
                            "source": "FDA",
                            "category": "contraindications",
                            "drug": drug_name,
                            "brand_name": label["brand_name"],
                            "last_updated": datetime.utcnow().strftime("%Y-%m-%d"),
                            "api_source": "OpenFDA",
                        },
                        "added_at": datetime.utcnow().isoformat(),
                        "content_hash": hashlib.sha256(content.encode()).hexdigest(),
                    }
                    with open(out_file, "w") as f:
                        json.dump(doc, f, indent=2)
                    logger.info(f"    ✅ Saved FDA contraindications for {drug_name}")
                else:
                    logger.info(f"    [DRY RUN] Would save FDA contraindications for {drug_name}")
                total_saved += 1

        # Save warnings + adverse reactions as DrugBank-style entry
        drug_content_parts = []
        if "warnings" in sections:
            drug_content_parts.append(f"Warnings: {sections['warnings']}")
        if "adverse_reactions" in sections:
            drug_content_parts.append(f"Adverse Reactions: {sections['adverse_reactions']}")
        if "clinical_pharmacology" in sections:
            drug_content_parts.append(f"Clinical Pharmacology: {sections['clinical_pharmacology']}")
        if "dosage_and_administration" in sections:
            drug_content_parts.append(f"Dosage: {sections['dosage_and_administration']}")

        if drug_content_parts:
            doc_id = f"drugbank_{drug_name}_openfda"
            out_dir = SOURCES_DIR / "drugbank"
            out_dir.mkdir(parents=True, exist_ok=True)
            out_file = out_dir / f"{drug_name}_openfda.json"

            if not out_file.exists() or True:
                content = f"{label['brand_name']} ({drug_name}). " + " ".join(drug_content_parts)

                if not dry_run:
                    doc = {
                        "doc_id": doc_id,
                        "content": content[:3000],  # Cap at 3K chars for embedding quality
                        "metadata": {
                            "source": "DrugBank",
                            "category": "drug_information",
                            "drug": drug_name,
                            "brand_name": label["brand_name"],
                            "last_updated": datetime.utcnow().strftime("%Y-%m-%d"),
                            "api_source": "OpenFDA",
                        },
                        "added_at": datetime.utcnow().isoformat(),
                        "content_hash": hashlib.sha256(content.encode()).hexdigest(),
                    }
                    with open(out_file, "w") as f:
                        json.dump(doc, f, indent=2)
                    logger.info(f"    ✅ Saved DrugBank-style entry for {drug_name}")
                else:
                    logger.info(f"    [DRY RUN] Would save DrugBank-style entry for {drug_name}")
                total_saved += 1

    return total_saved


# ═══════════════════════════════════════════════════════════════════════
#  Main
# ═══════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="P.R.I.S.M. Knowledge Base Populator")
    parser.add_argument("--pubmed-only", action="store_true", help="Only pull from PubMed")
    parser.add_argument("--openfda-only", action="store_true", help="Only pull from OpenFDA")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be fetched without saving")
    parser.add_argument("--pubmed-per-query", type=int, default=3, help="Max PubMed results per query (default: 3)")
    args = parser.parse_args()

    pull_all = not args.pubmed_only and not args.openfda_only

    logger.info("=" * 60)
    logger.info("P.R.I.S.M. Knowledge Base Populator")
    logger.info("=" * 60)

    total = 0

    if pull_all or not args.openfda_only:
        logger.info("\n📚 Pulling from PubMed E-utilities...")
        count = pull_pubmed(max_per_query=args.pubmed_per_query, dry_run=args.dry_run)
        logger.info(f"   PubMed: {count} documents saved\n")
        total += count

    if pull_all or not args.pubmed_only:
        logger.info("💊 Pulling from OpenFDA Drug Labels...")
        count = pull_openfda(dry_run=args.dry_run)
        logger.info(f"   OpenFDA: {count} documents saved\n")
        total += count

    logger.info(f"✅ Total: {total} documents added to knowledge base")
    logger.info(f"   Run 'python build_index.py' to rebuild the FAISS index")


if __name__ == "__main__":
    main()

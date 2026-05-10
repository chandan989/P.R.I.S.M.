# P.R.I.S.M. Knowledge Base

This directory contains the curated clinical knowledge base used for source grounding verification in P.R.I.S.M.

## Directory Structure

```
knowledge_base/
├── sources/              # Source documents
│   ├── fda/             # FDA Drug Labels, Safety Communications
│   ├── drugbank/        # DrugBank Interaction Profiles
│   ├── pubmed/          # PubMed Pharmacovigilance Abstracts
│   ├── mimic/           # MIMIC-IV Clinical Notes (de-identified)
│   └── formulary/       # Institutional Formulary Additions
├── index/               # Vector index (FAISS/ChromaDB)
│   ├── faiss.index     # FAISS vector index
│   └── metadata.json   # Index metadata
├── delta_agent/         # Nightly delta update agent
│   ├── pull_delta.py   # Encrypted delta bundle puller
│   ├── verify_manifest.py  # Ed25519 signature + hash chain verification
│   ├── apply_delta.py  # Atomic index update with rollback
│   └── config.yaml     # Update schedule, upstream URL, key paths
├── audit/               # Audit logs
│   └── updates.log     # Update audit trail
└── backups/             # Backup snapshots
```

## Quick Start

### Initial Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Initialize the knowledge base
python knowledge_base.py --rebuild
```

### Adding Documents

```python
from knowledge_base import KnowledgeBase

kb = KnowledgeBase()

kb.add_document(
    doc_id="fda-warfarin-label",
    content="Warfarin is contraindicated with clarithromycin due to increased bleeding risk...",
    metadata={
        "source": "fda",
        "category": "drug_labels",
        "drugs": ["warfarin", "clarithromycin"],
        "severity": "critical"
    }
)

kb.save_index()
```

### Searching and Verification

```python
# Search for similar documents
results = kb.search("warfarin drug interactions", top_k=5)

# Verify a claim
status, evidence = kb.verify_claim("Warfarin increases bleeding risk with clarithromycin")
# Returns: ("confirmed", evidence_dict) or ("contradicted", evidence_dict) or ("out_of_scope", None)
```

## Delta Update Protocol

The knowledge base is updated nightly via encrypted delta pulls:

```bash
# Check if knowledge base is stale
python delta_agent/pull_delta.py --check-staleness

# Force an update
python delta_agent/pull_delta.py --force
```

### Update Lifecycle

1. **Generate**: Upstream server diffs current canonical index
2. **Sign**: Ed25519 signature over manifest + payloads
3. **Encrypt**: AES-256-GCM with per-institution keys
4. **Pull**: Local agent initiates one-way TLS 1.3 pull
5. **Verify**: Signature verification → hash chain validation
6. **Apply**: Atomic delta application with rollback
7. **Re-embed**: New documents re-embedded via CPU MiniLM
8. **Audit**: Update receipt written to encrypted audit log

## Staleness Safeguard

If the local index hasn't been updated in >7 days, P.R.I.S.M. surfaces a warning:

```
⚠️ Knowledge base last updated 9 days ago. Drug interaction data may be stale.
   Contraindication results should be cross-referenced with current FDA resources.
```

## Source Categories

### FDA Drug Labels
- Structured XML drug labels
- Safety communications
- MedWatch alerts

### DrugBank
- Drug-drug interaction profiles
- Enzyme metabolism data
- Pharmacokinetic information

### PubMed
- Pharmacovigilance abstracts
- Clinical trial results
- Case reports

### MIMIC-IV
- De-identified clinical notes
- Medication administration records
- Lab results

### Institutional Formulary
- Hospital-specific drug lists
- Dosage guidelines
- Local contraindications

## Security

- **Zero-data-egress**: All processing is local
- **Encrypted updates**: AES-256-GCM encryption
- **Signed bundles**: Ed25519 signature verification
- **Audit trail**: Complete update history logged
- **Rollback support**: Automatic rollback on failure

## Performance

- **CPU-optimized embeddings**: ONNX MiniLM-L6 for fast inference
- **Vector search**: FAISS for efficient similarity search
- **Selective verification**: Only pharmacological claims are verified
- **Async pipeline**: Verification runs while user reviews deliberation

## Maintenance

```bash
# Rebuild index from source documents
python knowledge_base.py --rebuild

# Show statistics
python knowledge_base.py --stats

# Clean up old backups
python delta_agent/apply_delta.py --cleanup-backups
```

## Troubleshooting

### Index not found
```bash
python knowledge_base.py --rebuild
```

### Stale knowledge base warning
```bash
python delta_agent/pull_delta.py --force
```

### Signature verification failed
Check that the public key is correct and the bundle hasn't been tampered with.

### Decryption failed
Verify that the decryption key matches the one used by the upstream server.

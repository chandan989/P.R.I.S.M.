# Knowledge Base Agent Documentation

This agent provides a specialized interface for managing the P.R.I.S.M. knowledge base, which contains curated clinical documents used for source grounding verification.

## Key Responsibilities

1. **Document Management**: Handles adding, updating, and removing documents from the knowledge base
2. **Search Operations**: Provides vector search capabilities over clinical documents
3. **Claim Verification**: Verifies factual claims against verified sources
4. **Index Maintenance**: Manages the vector index and ensures it stays current
5. **Delta Updates**: Executes secure delta update protocol for keeping the knowledge base current

## Usage

### Command Line Interface

```bash
# Show statistics
python knowledge_base_agent.py --stats

# Search for documents
python knowledge_base_agent.py --search "warfarin interactions"

# Verify a claim
python knowledge_base_agent.py --verify "Warfarin increases bleeding risk with clarithromycin"

# Check staleness
python knowledge_base_agent.py --staleness

# Rebuild index
python knowledge_base_agent.py --rebuild

# Run delta update
python knowledge_base_agent.py --update
```

### Python API

```python
from knowledge_base_agent import KnowledgeBaseAgent

# Initialize agent
agent = KnowledgeBaseAgent()

# Search for documents
results = agent.search("drug interactions", top_k=5)

# Verify a claim
status, evidence = agent.verify_claim("Warfarin increases bleeding risk with clarithromycin")

# Check staleness
is_stale, days = agent.check_staleness()

# Run delta update
success = agent.run_delta_update()
```

## Key Components

### KnowledgeBaseAgent Class

The main agent class that provides all knowledge base functionality:

- `add_document()`: Add new documents to the knowledge base
- `search()`: Perform semantic search over documents
- `verify_claim()`: Verify factual claims against the knowledge base
- `run_delta_update()`: Execute the secure delta update protocol
- `rebuild_index()`: Rebuild the entire index from source documents
- `get_stats()`: Get knowledge base statistics

## Security Features

- Zero-data-egress architecture
- Encrypted delta updates
- Signed bundles verification
- Complete audit trail
- Automatic rollback on failure

## Performance

- CPU-optimized embeddings for fast inference
- Vector search for efficient similarity search
- Async pipeline for real-time verification

## Maintenance

The agent automatically checks for knowledge base staleness and can execute updates through the delta update protocol to ensure information is current.
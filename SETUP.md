# P.R.I.S.M. - Probabilistic Reasoning and Interpretability System for Models

The Glass Box Interpreter — see how Gemma 4 thinks, whether it's right, and how sure it is.

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- Ollama installed

### Installation

```bash
# Clone the repository
git clone https://github.com/chandan989/P.R.I.S.M..git
cd P.R.I.S.M.

# Run setup script
python setup.py --all
```

### Running P.R.I.S.M.

```bash
# 1. Start Ollama
ollama serve

# 2. Pull the model
ollama pull hf.co/chandan989/gemma-4-26B-A4B-it-MXFP4_MOE.gguf

# 3. Start the backend
cd backend
source venv/bin/activate  # On Windows: venv\Scripts\activate
python server.py

# 4. Start the frontend (in a new terminal)
cd prism-web
npm run dev
```

Open http://localhost:3000 to use P.R.I.S.M.

## Project Structure

```
P.R.I.S.M./
├── backend/              # FastAPI backend
│   ├── server.py        # Main API server
│   ├── client/          # Gemma 4 client
│   ├── parsers/         # Deliberation and claim parsers
│   ├── grounding/       # Source verification
│   └── calibration/     # Confidence calibration
├── knowledge_base/      # Clinical knowledge base
│   ├── sources/         # Source documents
│   ├── index/           # Vector index
│   └── delta_agent/     # Update agent
├── prism-web/          # Next.js frontend
├── training/           # Fine-tuning notebooks
└── setup.py            # Setup script
```

## Features

### Three Pillars

1. **Latent Deliberation Engine** - Shows how the AI reached its conclusion
2. **Source Grounding Visualizer** - Verifies claims against curated sources
3. **Certainty Indicators** - Shows how confident the AI actually is

### Use Case

**Polypharmacy Contraindication Auditing** - reviewing complex multi-drug regimens for fatal interactions with full reasoning transparency.

## Documentation

- [Backend Documentation](backend/README.md)
- [Knowledge Base Documentation](knowledge_base/README.md)
- [Training Documentation](training/FINETUNING_STRATEGY.md)

## License

MIT License - see [LICENSE](LICENSE) for details.

## Acknowledgments

- [Google DeepMind](https://deepmind.google/) — Gemma 4 model family
- [Unsloth](https://github.com/unslothai/unsloth) — Memory-efficient fine-tuning
- [Gemma 4 Good Hackathon](https://www.kaggle.com/competitions/gemma-4-good-hackathon)

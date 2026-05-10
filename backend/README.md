# P.R.I.S.M. Backend

FastAPI backend for the P.R.I.S.M. Glass Box interface.

Supports two backends:
- **Ollama**: For containerized model serving
- **llama.cpp**: For direct local inference with grammar enforcement

## Directory Structure

```
backend/
├── server.py              # FastAPI server
├── config.py              # Configuration management
├── requirements.txt       # Python dependencies
├── .env.example          # Environment variables template
├── client/
│   └── gemma_client.py   # Gemma 4 API client (streaming + logprobs)
├── parsers/
│   ├── deliberation.py   # Thought block parser
│   ├── claim_extractor.py  # Factual claim extraction
│   └── logprobs.py       # Logprobs → confidence scores
├── grounding/
│   ├── verifier.py       # Selective claim verification
│   └── knowledge_base.py # Vector search over curated sources
└── calibration/
    ├── conformal.py      # Conformal prediction + OOD detection
    ├── temperature.py    # Temperature scaling
    ├── brier.py          # Brier Score evaluation
    └── ece.py            # Expected Calibration Error evaluation
```

## Quick Start

### Installation

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
```

### Configuration

Edit `.env` to configure:

```bash
# Model Settings
MODEL_NAME=gemma-4-26B-A4B-it-MXFP4_MOE
MODEL_HOST=localhost
MODEL_PORT=11434
MODEL_BACKEND=ollama  # Options: ollama, llama_cpp
MODEL_PATH=  # Path to GGUF file (required for llama_cpp)

# llama.cpp Settings (only used if MODEL_BACKEND=llama_cpp)
N_CTX=4096
N_GPU_LAYERS=28
N_THREADS=4
VERBOSE=false
```

### Running the Server

```bash
python server.py
```

Or with uvicorn:

```bash
uvicorn server:app --host 0.0.0.0 --port 8000 --reload
```

### Standalone Inference

For direct local inference without the API server:

```bash
python prism_inference.py --model-path /path/to/model.gguf --query "Your query here"
```

Options:
- `--n-gpu-layers`: Number of GPU layers (default: 28)
- `--temperature`: Sampling temperature (default: 0.6)
- `--stream`: Enable streaming output
- `--no-grammar`: Disable grammar enforcement
- `--verbose`: Enable verbose logging

Example:
```bash
python prism_inference.py \
  --model-path ./models \
  --query "Patient is on warfarin and clarithromycin. Review for interactions." \
  --stream
```

## API Endpoints

### Health Check

```bash
GET /health
```

Returns server health status.

### Query

```bash
POST /query
Content-Type: application/json

{
  "query": "What are the drug interactions for warfarin?",
  "history": [],
  "temperature": 0.7,
  "max_tokens": 2048
}
```

Returns complete Glass Box response with:
- Answer text
- Deliberation trace
- Verified claims
- Confidence scores
- Source citations

### Streaming Query

```bash
POST /query/stream
Content-Type: application/json

{
  "query": "What are the drug interactions for warfarin?",
  "temperature": 0.7
}
```

Streams response chunks as Server-Sent Events.

### Verify Claims

```bash
POST /verify
Content-Type: application/json

["Warfarin increases bleeding risk", "Metformin is safe for renal patients"]
```

Returns verification results for each claim.

### Knowledge Base Status

```bash
GET /knowledge-base/status
```

Returns knowledge base statistics and staleness information.

### Model Info

```bash
GET /model/info
```

Returns information about the loaded model.

## Components

### Gemma Client

Handles communication with Gemma 4 via Ollama:

```python
from client.gemma_client import GemmaClient

async with GemmaClient() as client:
    async for chunk in client.generate("What is the capital of France?"):
        print(chunk.text, end="")
```

### Deliberation Parser

Extracts structured deliberation from thought blocks:

```python
from parsers.deliberation import DeliberationParser

parser = DeliberationParser()
trace = parser.parse(response_text)
```

### Claim Extractor

Extracts factual claims for verification:

```python
from parsers.claim_extractor import ClaimExtractor

extractor = ClaimExtractor()
claims = extractor.extract_claims(response_text)
```

### Claim Verifier

Verifies claims against knowledge base:

```python
from grounding.verifier import ClaimVerifier

verifier = ClaimVerifier()
result = verifier.verify_claim("Warfarin increases bleeding risk")
```

### Confidence Calibration

Applies conformal prediction and temperature scaling:

```python
from calibration.conformal import ConformalPredictor

predictor = ConformalPredictor(alpha=0.1)
predictor.fit(calibration_data)
interval = predictor.predict(confidence, semantic_distance=0.5)
```

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    FRONTEND (Next.js)                    │
└────────────────────┬────────────────────────────────────┘
                     │ API
                     ▼
┌─────────────────────────────────────────────────────────┐
│                  BACKEND (FastAPI)                       │
├─────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────────┐  │
│  │  API Server                                      │  │
│  │  ├── Gemma 4 API client (streaming)             │  │
│  │  ├── Thought block parser → deliberation        │  │
│  │  ├── Claim extractor → selective verification   │  │
│  │  ├── Logprobs extractor → confidence scores     │  │
│  │  └── Knowledge base (CPU dense embeddings)      │  │
│  └──────────────────────────────────────────────────┘  │
└────────────────────┬────────────────────────────────────┘
                     │ Local API call
                     ▼
┌─────────────────────────────────────────────────────────┐
│         LOCAL WORKSTATION HOST (Ollama / llama.cpp)      │
│  Gemma 4 A4B 26B MoE (Unsloth fine-tuned)               │
│  • MXFP4 Quantization + RotorQuant KV Compression        │
│  • ~4B active — MoE local workstation efficiency         │
└─────────────────────────────────────────────────────────┘
```

## Development

### Running Tests

```bash
pytest tests/
```

### Code Style

```bash
black backend/
isort backend/
flake8 backend/
```

## Troubleshooting

### Model not responding

Check that Ollama is running:

```bash
ollama list
ollama run gemma-4-26B-A4B-it-MXFP4_MOE
```

### Knowledge base not found

Ensure the knowledge base is initialized:

```bash
cd knowledge_base
python knowledge_base.py --rebuild
```

### CORS errors

Configure CORS origins in `.env`:

```bash
CORS_ORIGINS=http://localhost:3000,http://localhost:3001
```

## Performance

- **Streaming**: Response chunks streamed as generated
- **Async verification**: Claims verified while user reviews deliberation
- **CPU-optimized embeddings**: ONNX MiniLM-L6 for fast inference
- **Selective verification**: Only pharmacological claims verified

## Security

- **Zero-data-egress**: All processing is local
- **No PHI storage**: In-memory only processing
- **Encrypted audit logs**: TPM/HSM secured logging
- **CORS protection**: Configurable origin whitelist

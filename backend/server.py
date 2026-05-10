"""
P.R.I.S.M. Backend Server

FastAPI server for the Glass Box interface.

Handles:
- Gemma 4 API client (streaming via Ollama or llama.cpp)
- Thought block parsing
- Claim extraction and verification
- Logprobs extraction
- Knowledge base queries
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import logging
import json
import asyncio
from contextlib import asynccontextmanager

# Import P.R.I.S.M. components
from config import get_settings
from client.gemma_client import GemmaClient, BackendType
from parsers.deliberation import DeliberationParser
from parsers.claim_extractor import ClaimExtractor
from parsers.logprobs import LogprobsParser
from grounding.verifier import ClaimVerifier
from calibration.conformal import ConformalPredictor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global components
gemma_client: Optional[GemmaClient] = None
deliberation_parser: Optional[DeliberationParser] = None
claim_extractor: Optional[ClaimExtractor] = None
logprobs_parser: Optional[LogprobsParser] = None
claim_verifier: Optional[ClaimVerifier] = None
conformal_predictor: Optional[ConformalPredictor] = None

# System prompt for P.R.I.S.M.
PRISM_SYSTEM_PROMPT = """For every response:
1. Begin reasoning with <unused0> to expose your deliberation
2. Enumerate competing interpretations with probability estimates
3. Use tool calls to verify factual claims when confidence is low
4. Start your final clinical output exactly with a signal dot (🟢, 🟡, or 🔴).
5. Include a confidence assessment formatted exactly as 'Confidence: ✅ [LEVEL]'.
6. Conclude with a clear 'Recommendation:' block."""


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle."""
    global gemma_client, deliberation_parser, claim_extractor, logprobs_parser, claim_verifier, conformal_predictor

    settings = get_settings()

    # Initialize components on startup
    logger.info("Initializing P.R.I.S.M. components...")

    try:
        # Initialize Gemma client
        backend_type = BackendType(settings.model_backend)
        logger.info(f"Initializing Gemma client with backend: {backend_type.value}")

        gemma_client = GemmaClient(
            backend=backend_type,
            host=settings.model_host,
            port=settings.model_port,
            model=settings.model_name,
            model_path=settings.model_path,
            n_ctx=settings.n_ctx,
            n_gpu_layers=settings.n_gpu_layers,
            n_threads=settings.n_threads,
            verbose=settings.verbose
        )

        # Initialize parsers
        deliberation_parser = DeliberationParser()
        claim_extractor = ClaimExtractor()
        logprobs_parser = LogprobsParser(temperature=0.7)

        # Initialize claim verifier
        claim_verifier = ClaimVerifier(kb_root=settings.kb_root)

        # Initialize conformal predictor
        conformal_predictor = ConformalPredictor(alpha=settings.confidence_alpha)

        logger.info("✅ All components initialized successfully")

    except Exception as e:
        logger.error(f"❌ Failed to initialize components: {e}")
        raise

    yield

    # Cleanup on shutdown
    logger.info("Shutting down P.R.I.S.M. components...")
    if gemma_client:
        await gemma_client.close()
    logger.info("Shutdown complete")


# Initialize FastAPI app
app = FastAPI(
    title="P.R.I.S.M. API",
    description="Probabilistic Reasoning and Interpretability System for Models",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_origins_list,
    allow_credentials=get_settings().cors_allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response Models
class QueryRequest(BaseModel):
    """Request model for querying the model."""
    query: str
    history: Optional[List[Dict[str, str]]] = None
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 2048
    use_grammar: Optional[bool] = True


class DeliberationNode(BaseModel):
    """Model for a deliberation node."""
    interpretation: str
    probability: float
    supporting: List[str]
    weakening: List[str]


class DeliberationResponse(BaseModel):
    """Model for deliberation response."""
    selected_interpretation: str
    competing_hypotheses: List[DeliberationNode]
    discarded_paths: List[str]
    logical_chain: List[str]


class Claim(BaseModel):
    """Model for a factual claim."""
    text: str
    verification_status: str  # "confirmed", "contradicted", "inferred", "out_of_scope"
    source: Optional[str] = None
    confidence: Optional[float] = None


class VerificationResponse(BaseModel):
    """Model for claim verification response."""
    claims: List[Claim]
    overall_confidence: float


class ConfidenceScore(BaseModel):
    """Model for confidence score."""
    level: str  # "HIGH", "MODERATE", "LOW"
    score: float
    calibration: Optional[Dict[str, Any]] = None


class GlassBoxResponse(BaseModel):
    """Complete Glass Box response."""
    answer: str
    deliberation: Optional[DeliberationResponse] = None
    verified_claims: List[Claim]
    confidence: ConfidenceScore
    sources: List[Dict[str, Any]]


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "P.R.I.S.M. Backend",
        "version": "1.0.0",
        "model_loaded": gemma_client is not None
    }


# Query endpoint
@app.post("/query", response_model=GlassBoxResponse)
async def query(request: QueryRequest):
    """
    Process a query through the Glass Box pipeline.

    Returns:
        Complete Glass Box response with answer, deliberation,
        verified claims, and confidence scores.
    """
    if not gemma_client:
        raise HTTPException(status_code=503, detail="Model not initialized")

    try:
        # Build prompt with system prompt
        prompt = f"{PRISM_SYSTEM_PROMPT}\n<bos><start_of_turn>user\n{request.query}<end_of_turn>\n<start_of_turn>model\n<unused0>\n"

        # Get grammar if requested
        grammar = None
        if request.use_grammar and gemma_client.backend == BackendType.LLAMA_CPP:
            grammar = gemma_client.get_prism_grammar()

        # Generate response
        full_response = ""
        async for chunk in gemma_client.generate(
            prompt=prompt,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            stream=False,
            grammar=grammar,
            stop=["<eos>", "<end_of_turn>"]
        ):
            full_response += chunk.text

        # Parse deliberation
        deliberation_trace = deliberation_parser.parse(full_response)
        deliberation_response = None
        if deliberation_trace:
            deliberation_response = DeliberationResponse(
                selected_interpretation=deliberation_trace.selected_interpretation,
                competing_hypotheses=[
                    DeliberationNode(
                        interpretation=h.interpretation,
                        probability=h.probability,
                        supporting=h.supporting_evidence,
                        weakening=h.weakening_evidence
                    )
                    for h in deliberation_trace.competing_hypotheses
                ],
                discarded_paths=[d.hypothesis for d in deliberation_trace.discarded_paths],
                logical_chain=[s.description for s in deliberation_trace.logical_chain]
            )

        # Extract claims
        claims = claim_extractor.extract_claims(full_response)

        # Verify claims
        verified_claims = []
        for claim in claims:
            result = claim_verifier.verify_claim(claim.text)
            verified_claims.append(Claim(
                text=claim.text,
                verification_status=result.status.value,
                source=result.sources[0].get('source') if result.sources else None,
                confidence=result.confidence
            ))

        # Calculate confidence
        confidence_level = "MODERATE"
        confidence_score = 0.5

        # Check for confidence indicators in response
        if "Confidence: ✅ HIGH" in full_response:
            confidence_level = "HIGH"
            confidence_score = 0.8
        elif "Confidence: ✅ MODERATE" in full_response:
            confidence_level = "MODERATE"
            confidence_score = 0.5
        elif "Confidence: ✅ LOW" in full_response:
            confidence_level = "LOW"
            confidence_score = 0.2

        # Extract answer (remove thought blocks)
        answer = full_response
        if deliberation_trace and deliberation_trace.raw_thought_blocks:
            for thought_block in deliberation_trace.raw_thought_blocks:
                answer = answer.replace(thought_block, "")

        return GlassBoxResponse(
            answer=answer.strip(),
            deliberation=deliberation_response,
            verified_claims=verified_claims,
            confidence=ConfidenceScore(
                level=confidence_level,
                score=confidence_score
            ),
            sources=[result.sources[0] for result in [claim_verifier.verify_claim(c.text) for c in claims] if result.sources]
        )

    except Exception as e:
        logger.error(f"Error processing query: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# Streaming query endpoint
@app.post("/query/stream")
async def query_stream(request: QueryRequest):
    """
    Process a query with streaming response.

    Yields:
        Streaming response chunks as they become available.
    """
    if not gemma_client:
        raise HTTPException(status_code=503, detail="Model not initialized")

    try:
        # Build prompt with system prompt
        prompt = f"{PRISM_SYSTEM_PROMPT}\n<bos><start_of_turn>user\n{request.query}<end_of_turn>\n<start_of_turn>model\n<unused0>\n"

        # Get grammar if requested
        grammar = None
        if request.use_grammar and gemma_client.backend == BackendType.LLAMA_CPP:
            grammar = gemma_client.get_prism_grammar()

        async def generate():
            """Generate streaming response."""
            full_response = ""

            async for chunk in gemma_client.generate(
                prompt=prompt,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                stream=True,
                grammar=grammar,
                stop=["<eos>", "<end_of_turn>"]
            ):
                full_response += chunk.text

                # Send chunk
                yield "data: " + json.dumps({
                    "type": "chunk",
                    "content": chunk.text,
                    "is_complete": chunk.is_complete
                }) + "\n\n"

                # If complete, send final analysis
                if chunk.is_complete:
                    # Parse deliberation
                    deliberation_trace = deliberation_parser.parse(full_response)

                    # Extract claims
                    claims = claim_extractor.extract_claims(full_response)

                    # Send final metadata
                    yield "data: " + json.dumps({
                        "type": "complete",
                        "deliberation": deliberation_parser.to_dict(deliberation_trace) if deliberation_trace else None,
                        "claims_count": len(claims),
                        "is_complete": True
                    }) + "\n\n"

        return StreamingResponse(generate(), media_type="text/event-stream")

    except Exception as e:
        logger.error(f"Error in streaming query: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# Verification endpoint
@app.post("/verify", response_model=VerificationResponse)
async def verify_claims(claims: List[str]):
    """
    Verify a list of claims against the knowledge base.

    Args:
        claims: List of claim texts to verify

    Returns:
        Verification results for each claim
    """
    if not claim_verifier:
        raise HTTPException(status_code=503, detail="Claim verifier not initialized")

    try:
        verified = []

        for claim in claims:
            result = claim_verifier.verify_claim(claim)
            verified.append(Claim(
                text=claim,
                verification_status=result.status.value,
                source=result.sources[0].get('source') if result.sources else None,
                confidence=result.confidence
            ))

        # Calculate overall confidence
        overall_confidence = sum(c.confidence or 0 for c in verified) / len(verified) if verified else 0

        return VerificationResponse(
            claims=verified,
            overall_confidence=overall_confidence
        )

    except Exception as e:
        logger.error(f"Error verifying claims: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# Knowledge base status endpoint
@app.get("/knowledge-base/status")
async def knowledge_base_status():
    """
    Get the current status of the knowledge base.

    Returns:
        Knowledge base statistics and staleness information.
    """
    if not claim_verifier:
        raise HTTPException(status_code=503, detail="Claim verifier not initialized")

    try:
        is_stale, days_since = claim_verifier.check_staleness()
        summary = claim_verifier.get_sources_summary()

        return {
            "document_count": claim_verifier.kb.get_document_count(),
            "last_updated": None,  # Would need to track this
            "is_stale": is_stale,
            "days_since_update": days_since,
            "sources": summary
        }

    except Exception as e:
        logger.error(f"Error getting knowledge base status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# Model info endpoint
@app.get("/model/info")
async def model_info():
    """
    Get information about the currently loaded model.

    Returns:
        Model metadata and capabilities.
    """
    if not gemma_client:
        raise HTTPException(status_code=503, detail="Model not initialized")

    try:
        info = await gemma_client.get_model_info()

        # Add P.R.I.S.M. specific info
        info.update({
            "prism_version": "1.0.0",
            "capabilities": [
                "deliberation_traces",
                "source_grounding",
                "confidence_calibration",
                "tool_calls",
                "grammar_enforced_output"
            ],
            "backend": gemma_client.backend.value
        })

        return info

    except Exception as e:
        logger.error(f"Error getting model info: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()

    uvicorn.run(
        "server:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload
    )

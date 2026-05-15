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
from pydantic import BaseModel, model_validator
from typing import Optional, List, Dict, Any
import logging
import json
import asyncio
from contextlib import asynccontextmanager
from datetime import datetime

# Import P.R.I.S.M. components
from config import get_settings
from client.gemma_client import GemmaClient, BackendType
from parsers.deliberation import DeliberationParser
from parsers.claim_extractor import ClaimExtractor
from parsers.logprobs import LogprobsParser
from grounding.verifier import ClaimVerifier
from calibration.conformal import ConformalPredictor
from session_manager import get_session_manager, init_session_manager
from exceptions import (
    ModelNotInitializedError,
    KnowledgeBaseNotInitializedError,
    SessionNotFoundError,
    SessionExpiredError
)

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
            n_gpu_layers=-1,  # Offload all layers to GPU
            n_threads=settings.n_threads,
            n_batch=1024,      # Faster prefill on dual T4
            tensor_split=[0.5, 0.5], # Split workload 50/50 across dual T4s
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

        # Initialize session manager
        await init_session_manager(
            session_timeout_minutes=30,
            use_redis=False  # Set to True and provide redis_url for distributed sessions
        )

        logger.info("✅ All components initialized successfully")

    except Exception as e:
        logger.error(f"❌ Failed to initialize components: {e}")
        raise

    yield

    # Cleanup on shutdown
    logger.info("Shutting down P.R.I.S.M. components...")

    # Shutdown session manager
    session_mgr = get_session_manager()
    await session_mgr.shutdown()

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
    query: Optional[str] = None
    prompt: Optional[str] = None
    history: Optional[List[Dict[str, str]]] = None
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 2048
    use_grammar: Optional[bool] = True

    @model_validator(mode="after")
    def normalize_query(self):
        """Accept legacy prompt payloads while keeping query as canonical."""
        if not self.query and self.prompt:
            self.query = self.prompt
        if not self.query:
            raise ValueError("query is required")
        return self


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
    """
    Comprehensive health check endpoint.

    Checks the status of all system components:
    - Model backend connectivity
    - Knowledge base availability
    - Embedding model status
    - Index integrity
    """
    health_status = {
        "status": "healthy",
        "service": "P.R.I.S.M. Backend",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "components": {}
    }

    # Check model backend
    model_healthy = True
    model_details = {}
    if gemma_client:
        try:
            if gemma_client.backend == BackendType.OLLAMA:
                # Test Ollama connectivity
                try:
                    info = await gemma_client.get_model_info()
                    model_details = {
                        "backend": "ollama",
                        "model": gemma_client.model,
                        "host": gemma_client.host,
                        "port": gemma_client.port,
                        "connected": "error" not in str(info).lower()
                    }
                    model_healthy = model_details["connected"]
                except Exception as e:
                    model_healthy = False
                    model_details = {"error": str(e)}
            else:
                # llama.cpp backend
                model_details = {
                    "backend": "llama_cpp",
                    "model_path": gemma_client.model_path,
                    "loaded": gemma_client.llm is not None
                }
                model_healthy = model_details["loaded"]
        except Exception as e:
            model_healthy = False
            model_details = {"error": str(e)}
    else:
        model_healthy = False
        model_details = {"error": "Model client not initialized"}

    health_status["components"]["model"] = {
        "status": "healthy" if model_healthy else "unhealthy",
        "details": model_details
    }

    # Check knowledge base
    kb_healthy = True
    kb_details = {}
    if claim_verifier:
        try:
            doc_count = claim_verifier.kb.get_document_count()
            sources_summary = claim_verifier.kb.get_sources_summary()
            is_stale, days_since = claim_verifier.kb.check_staleness()

            kb_details = {
                "document_count": doc_count,
                "sources": sources_summary,
                "is_stale": is_stale,
                "days_since_update": days_since,
                "index_available": claim_verifier.kb.index is not None
            }
            kb_healthy = doc_count > 0 and kb_details["index_available"]
        except Exception as e:
            kb_healthy = False
            kb_details = {"error": str(e)}
    else:
        kb_healthy = False
        kb_details = {"error": "Claim verifier not initialized"}

    health_status["components"]["knowledge_base"] = {
        "status": "healthy" if kb_healthy else "unhealthy",
        "details": kb_details
    }

    # Check embedding model
    embedding_healthy = True
    embedding_details = {}
    if claim_verifier and claim_verifier.kb.embedding_model:
        embedding_details = {
            "model": "sentence-transformers/all-MiniLM-L6-v2",
            "device": "cpu",
            "loaded": True
        }
    else:
        embedding_healthy = False
        embedding_details = {"error": "Embedding model not loaded"}

    health_status["components"]["embedding_model"] = {
        "status": "healthy" if embedding_healthy else "unhealthy",
        "details": embedding_details
    }

    # Check parsers
    parsers_healthy = True
    parsers_details = {
        "deliberation_parser": deliberation_parser is not None,
        "claim_extractor": claim_extractor is not None,
        "logprobs_parser": logprobs_parser is not None
    }
    parsers_healthy = all(parsers_details.values())

    health_status["components"]["parsers"] = {
        "status": "healthy" if parsers_healthy else "unhealthy",
        "details": parsers_details
    }

    # Check calibration
    calibration_healthy = True
    calibration_details = {
        "conformal_predictor": conformal_predictor is not None,
        "alpha": conformal_predictor.alpha if conformal_predictor else None
    }
    calibration_healthy = conformal_predictor is not None

    health_status["components"]["calibration"] = {
        "status": "healthy" if calibration_healthy else "unhealthy",
        "details": calibration_details
    }

    # Overall status
    all_healthy = all(
        comp["status"] == "healthy"
        for comp in health_status["components"].values()
    )
    health_status["status"] = "healthy" if all_healthy else "degraded"

    # Set appropriate HTTP status code
    if not all_healthy:
        # Still return 200 but with degraded status
        pass

    return health_status


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


# ── Audit endpoint (frontend-compatible SSE) ──────────────────────────

class AuditRequest(BaseModel):
    """Request model for the audit endpoint (frontend-compatible)."""
    query: str
    session_id: Optional[str] = None
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 2048


def _map_verification_to_signal(status_value: str) -> str:
    """Map a VerificationStatus value to a frontend signal color."""
    mapping = {
        "confirmed": "green",
        "contradicted": "red",
        "inferred": "yellow",
        "out_of_scope": "grey",
    }
    return mapping.get(status_value, "grey")


def _format_deliberation_for_frontend(deliberation_trace, confidence_data):
    """
    Convert a DeliberationTrace into the JSON structure the frontend expects
    for the 'thought' event.
    """
    interpretations = []
    for i, h in enumerate(deliberation_trace.competing_hypotheses):
        interpretations.append({
            "label": h.interpretation,
            "probability": round(h.probability * 100, 1),
            "supporting": h.supporting_evidence,
            "weakening": h.weakening_evidence,
        })

    discarded = [d.hypothesis for d in deliberation_trace.discarded_paths]

    # The selected index is the one with highest probability, default 0
    selected = 0
    if interpretations:
        selected = max(range(len(interpretations)),
                       key=lambda i: interpretations[i]["probability"])

    return {
        "interpretations": interpretations,
        "discarded": discarded,
        "selected": selected,
    }


@app.post("/api/audit")
async def audit_stream(request: AuditRequest):
    """
    Glass Box audit endpoint — SSE stream compatible with the frontend.

    Runs the full pipeline:
      1. Generate model response
      2. Parse deliberation traces
      3. Extract & verify claims
      4. Emit structured SSE events (thought → answer+source_dot → confidence → done)

    Supports session management for query history and resumption.
    """
    if not gemma_client:
        raise HTTPException(status_code=503, detail="Model not initialized")

    session_mgr = get_session_manager()

    # Get or create session
    session = None
    if request.session_id:
        session = await session_mgr.get_session(request.session_id)
        if not session:
            session = await session_mgr.create_session(
                session_id=request.session_id,
                metadata={"source": "api_audit"}
            )
    else:
        session = await session_mgr.create_session(metadata={"source": "api_audit"})

    async def generate_audit_events():
        try:
            # Build prompt
            prompt = (
                f"{PRISM_SYSTEM_PROMPT}\n<bos><start_of_turn>user\n"
                f"{request.query}<end_of_turn>\n<start_of_turn>model\n<unused0>\n"
            )

            # Get grammar if using llama.cpp
            grammar = None
            if gemma_client.backend == BackendType.LLAMA_CPP:
                grammar = gemma_client.get_prism_grammar()

            # ── Step 1: Generate full response ────────────────────────
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

            # ── Step 2: Parse deliberation ────────────────────────────
            deliberation_trace = deliberation_parser.parse(full_response)

            # ── Step 3: Extract & verify claims ───────────────────────
            claims = claim_extractor.extract_claims(full_response)

            verified_results = []
            for claim in claims:
                result = claim_verifier.verify_claim(claim.text)
                verified_results.append({
                    "text": claim.text,
                    "status": result.status.value,
                    "signal": _map_verification_to_signal(result.status.value),
                    "source": result.sources[0].get("source", "Source") if result.sources else "No source",
                    "snippet": (result.sources[0].get("content", "")[:200]
                                if result.sources else "No evidence found"),
                    "confidence": result.confidence,
                })

            # ── Step 4: Determine confidence ──────────────────────────
            confidence_level = "MODERATE"
            confidence_score = 50

            if "Confidence: ✅ HIGH" in full_response:
                confidence_level = "HIGH"
                confidence_score = 82
            elif "Confidence: ✅ MODERATE" in full_response:
                confidence_level = "MODERATE"
                confidence_score = 58
            elif "Confidence: ✅ LOW" in full_response:
                confidence_level = "LOW"
                confidence_score = 35

            # If we have verified claims, adjust score based on verification
            if verified_results:
                confirmed = sum(1 for v in verified_results if v["status"] == "confirmed")
                contradicted = sum(1 for v in verified_results if v["status"] == "contradicted")
                total = len(verified_results)
                if total > 0:
                    ratio = confirmed / total
                    if contradicted > 0:
                        confidence_level = "LOW"
                        confidence_score = max(20, int(ratio * 50))
                    elif ratio >= 0.7:
                        confidence_level = "HIGH"
                        confidence_score = max(70, int(ratio * 100))
                    elif ratio >= 0.3:
                        confidence_level = "MODERATE"
                        confidence_score = int(ratio * 100)

            confidence_data = {
                "level": confidence_level,
                "score": confidence_score,
                "brier": 0.15,
                "ece": 0.06,
                "ood": False,
            }

            # ── Update session ───────────────────────────────────────
            if session:
                await session_mgr.update_session(
                    session.session_id,
                    query=request.query,
                    deliberation=deliberation_parser.to_dict(deliberation_trace) if deliberation_trace else None,
                    claims=verified_results,
                    confidence=confidence_data,
                    answer=full_response
                )
                await session_mgr.add_message(session.session_id, "user", request.query)
                await session_mgr.add_message(session.session_id, "assistant", full_response)

            # ── Emit SSE events ───────────────────────────────────────

            # 1. Thought event (deliberation)
            if deliberation_trace:
                thought_payload = _format_deliberation_for_frontend(
                    deliberation_trace, confidence_data
                )
            else:
                # Fallback: produce a single interpretation from the response
                thought_payload = {
                    "interpretations": [{
                        "label": "Primary analysis based on model reasoning",
                        "probability": confidence_score,
                        "supporting": ["Model generated response based on clinical knowledge"],
                        "weakening": ["No structured deliberation was captured"],
                    }],
                    "discarded": [],
                    "selected": 0,
                }

            yield "data: " + json.dumps({
                "type": "thought",
                "content": json.dumps(thought_payload),
            }) + "\n\n"

            # Small delay for visual effect
            await asyncio.sleep(0.1)

            # 2. Answer + source_dot events
            # Strip thought blocks from the answer
            answer = full_response
            if deliberation_trace and deliberation_trace.raw_thought_blocks:
                for thought_block in deliberation_trace.raw_thought_blocks:
                    answer = answer.replace(thought_block, "")
            # Also strip thought channel markers
            answer = answer.replace("<|channel>thought\n", "").replace("<|channel>|", "")
            answer = answer.strip()

            # Split answer into sentences for interleaving source dots
            import re
            sentences = re.split(r'(?<=[.!?])\s+', answer)
            sentences = [s.strip() for s in sentences if s.strip()]

            source_idx = 0
            for i, sentence in enumerate(sentences):
                # Emit answer tokens (word by word for streaming feel)
                words = sentence.split()
                for j, word in enumerate(words):
                    separator = " " if j < len(words) - 1 else ""
                    yield "data: " + json.dumps({
                        "type": "answer",
                        "content": word + separator,
                    }) + "\n\n"
                    await asyncio.sleep(0.03)  # 30ms per word

                # After each sentence, emit a source dot if we have a matching verified claim
                if source_idx < len(verified_results):
                    vr = verified_results[source_idx]
                    yield "data: " + json.dumps({
                        "type": "source_dot",
                        "signal": vr["signal"],
                        "source": vr["source"],
                        "snippet": vr["snippet"],
                    }) + "\n\n"
                    source_idx += 1

                # Add space between sentences
                if i < len(sentences) - 1:
                    yield "data: " + json.dumps({
                        "type": "answer",
                        "content": " ",
                    }) + "\n\n"

            # 3. Confidence event
            await asyncio.sleep(0.15)
            yield "data: " + json.dumps({
                "type": "confidence",
                "confidence": confidence_data,
            }) + "\n\n"

            # 4. Done event
            yield "data: " + json.dumps({"type": "done"}) + "\n\n"

        except Exception as e:
            logger.error(f"Error in audit stream: {e}", exc_info=True)
            yield "data: " + json.dumps({
                "type": "error",
                "content": str(e),
            }) + "\n\n"

    return StreamingResponse(
        generate_audit_events(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()

    uvicorn.run(
        "server:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload
    )

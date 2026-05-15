"""
P.R.I.S.M. Gemma 4 Client

Handles communication with the Gemma 4 model via Ollama or llama.cpp.

Features:
- Streaming response generation
- Logprobs extraction
- Thought block capture
- Context management
- Grammar-based structured output
"""

import httpx
import json
import logging
import os
from typing import AsyncGenerator, Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum
import asyncio

logger = logging.getLogger(__name__)


class BackendType(Enum):
    """Supported backend types."""
    OLLAMA = "ollama"
    LLAMA_CPP = "llama_cpp"


@dataclass
class TokenLogprob:
    """Log probability information for a token."""
    token: str
    logprob: float
    token_id: int


@dataclass
class ThoughtBlock:
    """A thought block from the model's deliberation."""
    content: str
    tokens: List[TokenLogprob]
    start_position: int
    end_position: int


@dataclass
class GenerationChunk:
    """A chunk of generated text."""
    text: str
    thought_blocks: List[ThoughtBlock]
    logprobs: List[TokenLogprob]
    is_complete: bool


class GemmaClient:
    """
    Client for interacting with Gemma 4 via Ollama or llama.cpp.

    Handles streaming generation, logprobs extraction, and
    thought block parsing.
    """

    def __init__(
        self,
        backend: Union[str, BackendType] = BackendType.OLLAMA,
        host: str = "localhost",
        port: int = 11434,
        model: str = "gemma-4-26B-A4B-it-MXFP4_MOE",
        model_path: Optional[str] = None,
        timeout: int = 300,
        n_ctx: int = 4096,
        n_gpu_layers: int = 100,  # Force all layers to GPU
        n_threads: int = 1,      # Minimal CPU overhead
        n_batch: int = 512,       # More stable batch size for T4 bandwidth
        tensor_split: Optional[List[float]] = [0.5, 0.5], # Dual T4 split
        verbose: bool = False,
        model_name: Optional[str] = None,
        backend_type: Optional[Union[str, BackendType]] = None
    ):
        """
        Initialize the Gemma client.

        Args:
            backend: Backend type ('ollama' or 'llama_cpp')
            host: Ollama host (for Ollama backend)
            port: Ollama port (for Ollama backend)
            model: Model name (for Ollama backend)
            model_path: Path to GGUF model file (for llama.cpp backend)
            timeout: Request timeout in seconds
            n_ctx: Context window size (for llama.cpp backend)
            n_gpu_layers: Number of layers to offload to GPU (for llama.cpp backend)
            n_threads: Number of CPU threads (for llama.cpp backend)
            n_batch: Batch size for prompt processing
            tensor_split: Split ratio for multi-GPU setups
            verbose: Enable verbose logging (for llama.cpp backend)
        """
        if backend_type is not None:
            backend = backend_type
        if model_name is not None:
            model = model_name

        self.backend = BackendType(backend) if isinstance(backend, str) else backend
        self.host = host
        self.port = port
        self.model = model
        self.model_name = model
        self.backend_type = self.backend
        self.model_path = model_path
        self.timeout = timeout
        self.n_ctx = n_ctx
        self.n_gpu_layers = n_gpu_layers
        self.n_threads = n_threads
        self.n_batch = n_batch
        self.tensor_split = tensor_split
        self.verbose = verbose
        self.base_url = f"http://{host}:{port}"

        # Initialize backend
        self.llm = None
        self.client = None

        if self.backend == BackendType.OLLAMA:
            # HTTP client for Ollama
            self.client = httpx.AsyncClient(timeout=timeout)
        elif self.backend == BackendType.LLAMA_CPP:
            # Initialize llama.cpp model
            self._init_llama_cpp()
        else:
            raise ValueError(f"Unsupported backend: {backend}")

    def _generate_prompt(self, prompt: str) -> str:
        """Wrap a raw prompt in the simple user/assistant format used by tests."""
        return self._messages_to_prompt([{"role": "user", "content": prompt}])

    def _init_llama_cpp(self):
        """Initialize llama.cpp model."""
        try:
            import llama_cpp
            import glob

            # Find GGUF file if model_path is a directory
            if self.model_path and os.path.isdir(self.model_path):
                gguf_files = glob.glob(f"{self.model_path}/*.gguf")
                gguf_files.sort()
                self.model_path = gguf_files[0] if gguf_files else None

            if not self.model_path or not os.path.exists(self.model_path):
                raise FileNotFoundError(f"Model file not found: {self.model_path}")

            logger.info(f"Loading llama.cpp model from: {self.model_path}")

            self.llm = llama_cpp.Llama(
                model_path=self.model_path,
                n_ctx=self.n_ctx,
                n_gpu_layers=self.n_gpu_layers,
                n_threads=self.n_threads,
                n_batch=self.n_batch,
                tensor_split=self.tensor_split,
                offload_kqv=True,
                # RotorQuant KV Cache Compression (sparse 3D Clifford rotors)
                type_k=llama_cpp.GGML_TYPE_Q4_0,
                type_v=llama_cpp.GGML_TYPE_Q4_0,
                flash_attn=True,
                verbose=self.verbose
            )

            logger.info("llama.cpp model loaded successfully")

        except ImportError:
            raise ImportError("llama-cpp-python not installed. Install with: pip install llama-cpp-python")
        except Exception as e:
            logger.error(f"Failed to initialize llama.cpp: {e}")
            raise

    async def generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        stream: bool = True,
        include_logprobs: bool = True,
        grammar: Optional[Any] = None,
        stop: Optional[List[str]] = None
    ) -> AsyncGenerator[GenerationChunk, None]:
        """
        Generate text from the model.

        Args:
            prompt: Input prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            stream: Whether to stream the response
            include_logprobs: Whether to include logprobs
            grammar: Optional grammar for structured output (llama.cpp only)
            stop: Optional stop tokens

        Yields:
            Generation chunks as they're generated
        """
        if self.backend == BackendType.OLLAMA:
            async for chunk in self._generate_ollama(
                prompt, temperature, max_tokens, stream, include_logprobs, stop
            ):
                yield chunk
        elif self.backend == BackendType.LLAMA_CPP:
            async for chunk in self._generate_llama_cpp(
                prompt, temperature, max_tokens, stream, include_logprobs, grammar, stop
            ):
                yield chunk

    async def _generate_ollama(
        self,
        prompt: str,
        temperature: float,
        max_tokens: int,
        stream: bool,
        include_logprobs: bool,
        stop: Optional[List[str]]
    ) -> AsyncGenerator[GenerationChunk, None]:
        """Generate using Ollama backend."""
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": stream,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens
            }
        }

        if include_logprobs:
            payload["options"]["num_ctx"] = 16384

        if stop:
            payload["options"]["stop"] = stop

        try:
            if stream:
                async with self.client.stream(
                    "POST",
                    f"{self.base_url}/api/generate",
                    json=payload
                ) as response:
                    response.raise_for_status()

                    async for line in response.aiter_lines():
                        if line.strip():
                            try:
                                chunk_data = json.loads(line)
                                yield self._parse_chunk(chunk_data)
                            except json.JSONDecodeError:
                                continue
            else:
                response = await self.client.post(
                    f"{self.base_url}/api/generate",
                    json=payload
                )
                response.raise_for_status()
                data = response.json()
                yield self._parse_chunk(data)

        except httpx.HTTPError as e:
            logger.error(f"HTTP error during generation: {e}")
            raise
        except Exception as e:
            logger.error(f"Error during generation: {e}")
            raise

    async def _generate_llama_cpp(
        self,
        prompt: str,
        temperature: float,
        max_tokens: int,
        stream: bool,
        include_logprobs: bool,
        grammar: Optional[Any],
        stop: Optional[List[str]]
    ) -> AsyncGenerator[GenerationChunk, None]:
        """Generate using llama.cpp backend."""
        try:
            import llama_cpp

            # Prepare generation parameters
            gen_params = {
                "prompt": prompt,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "top_p": 0.85,
                "echo": False
            }

            if grammar:
                gen_params["grammar"] = grammar

            if stop:
                gen_params["stop"] = stop

            if stream:
                # Stream generation
                for chunk in self.llm.create_completion(**gen_params, stream=True):
                    text = chunk["choices"][0]["text"]
                    if text:
                        yield GenerationChunk(
                            text=text,
                            thought_blocks=self._extract_thought_blocks(text),
                            logprobs=[],
                            is_complete=chunk.get("finish_reason") is not None
                        )
            else:
                # Non-streaming generation
                output = self.llm.create_completion(**gen_params)
                text = output["choices"][0]["text"]

                yield GenerationChunk(
                    text=text,
                    thought_blocks=self._extract_thought_blocks(text),
                    logprobs=[],
                    is_complete=True
                )

        except ImportError:
            raise ImportError("llama-cpp-python not installed")
        except Exception as e:
            logger.error(f"Error during llama.cpp generation: {e}")
            raise

    def _parse_chunk(self, chunk_data: Dict[str, Any]) -> GenerationChunk:
        """
        Parse a chunk from the Ollama response.

        Args:
            chunk_data: Raw chunk data from Ollama

        Returns:
            Parsed generation chunk
        """
        text = chunk_data.get("response", "")
        done = chunk_data.get("done", False)

        # Parse thought blocks if present
        thought_blocks = self._extract_thought_blocks(text)

        # Parse logprobs if present
        logprobs = self._extract_logprobs(chunk_data)

        return GenerationChunk(
            text=text,
            thought_blocks=thought_blocks,
            logprobs=logprobs,
            is_complete=done
        )

    def _extract_thought_blocks(self, text: str) -> List[ThoughtBlock]:
        """
        Extract thought blocks from generated text.

        Args:
            text: Generated text

        Returns:
            List of thought blocks
        """
        thought_blocks = []

        # Look for thought markers
        # Gemma 4 uses <unused0> for deliberation start and <unused1> for end
        thought_start = "<unused0>"
        thought_end = "<unused1>"

        start_pos = 0
        while True:
            start_idx = text.find(thought_start, start_pos)
            if start_idx == -1:
                # Try legacy markers as fallback
                thought_start_legacy = "<|channel>thought\n"
                thought_end_legacy = "<|channel>|"
                start_idx = text.find(thought_start_legacy, start_pos)
                if start_idx == -1:
                    break
                thought_start = thought_start_legacy
                thought_end = thought_end_legacy

            end_idx = text.find(thought_end, start_idx)
            if end_idx == -1:
                break

            # Extract thought content
            content = text[start_idx + len(thought_start):end_idx]

            thought_blocks.append(ThoughtBlock(
                content=content,
                tokens=[],  # Would need token-level info
                start_position=start_idx,
                end_position=end_idx + len(thought_end)
            ))

            start_pos = end_idx + len(thought_end)

        return thought_blocks

    def _extract_logprobs(self, chunk_data: Dict[str, Any]) -> List[TokenLogprob]:
        """
        Extract logprobs from chunk data.

        Args:
            chunk_data: Raw chunk data

        Returns:
            List of token logprobs
        """
        logprobs = []

        # Ollama provides logprobs in the "logprobs" field
        # Format: {"logprobs": {"tokens": [...], "values": [...]}}
        if "logprobs" in chunk_data:
            logprobs_data = chunk_data["logprobs"]

            # Handle different Ollama logprobs formats
            if isinstance(logprobs_data, dict):
                tokens = logprobs_data.get("tokens", [])
                values = logprobs_data.get("values", [])

                # Create TokenLogprob objects
                for i, (token, logprob) in enumerate(zip(tokens, values)):
                    logprobs.append(TokenLogprob(
                        token=token,
                        logprob=float(logprob),
                        token_id=i  # Ollama doesn't provide token IDs
                    ))

            elif isinstance(logprobs_data, list):
                # Alternative format: list of logprob objects
                for i, lp in enumerate(logprobs_data):
                    if isinstance(lp, dict):
                        logprobs.append(TokenLogprob(
                            token=lp.get("token", ""),
                            logprob=float(lp.get("logprob", 0.0)),
                            token_id=lp.get("token_id", i)
                        ))

        # Check for top_k logprobs (alternative format)
        if "top_logprobs" in chunk_data:
            top_logprobs = chunk_data["top_logprobs"]
            if isinstance(top_logprobs, list) and len(top_logprobs) > 0:
                # Use the first (selected) token's logprob
                first_token = top_logprobs[0]
                if isinstance(first_token, dict):
                    logprobs.append(TokenLogprob(
                        token=first_token.get("token", ""),
                        logprob=float(first_token.get("logprob", 0.0)),
                        token_id=first_token.get("token_id", 0)
                    ))

        return logprobs

    async def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2048,
        stream: bool = True
    ) -> AsyncGenerator[GenerationChunk, None]:
        """
        Chat with the model using message format.

        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            stream: Whether to stream the response

        Yields:
            Generation chunks as they're generated
        """
        # Convert messages to prompt format
        prompt = self._messages_to_prompt(messages)

        async for chunk in self.generate(
            prompt=prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=stream
        ):
            yield chunk

    def _messages_to_prompt(self, messages: List[Dict[str, str]]) -> str:
        """
        Convert message format to prompt format.

        Args:
            messages: List of message dicts

        Returns:
            Formatted prompt string
        """
        prompt_parts = []

        for message in messages:
            role = message.get("role", "user")
            content = message.get("content", "")

            if role == "system":
                prompt_parts.append(f"<system>{content}</system>")
            elif role == "user":
                prompt_parts.append(f"<user>{content}</user>")
            elif role == "assistant":
                prompt_parts.append(f"<assistant>{content}</assistant>")
            elif role == "tool":
                prompt_parts.append(f"<tool>{content}</tool>")

        # Add assistant start
        prompt_parts.append("<assistant>")

        return "\n".join(prompt_parts)

    async def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the loaded model.

        Returns:
            Model information dictionary
        """
        try:
            response = await self.client.get(f"{self.base_url}/api/tags")
            response.raise_for_status()
            data = response.json()

            # Find our model
            models = data.get("models", [])
            for model in models:
                if model.get("name") == self.model:
                    return model

            return {"error": "Model not found"}

        except httpx.HTTPError as e:
            logger.error(f"HTTP error getting model info: {e}")
            raise

    async def close(self):
        """Close resources."""
        if self.client:
            await self.client.aclose()
        # llama.cpp model doesn't need explicit closing

    async def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the loaded model.

        Returns:
            Model information dictionary
        """
        if self.backend == BackendType.OLLAMA:
            try:
                response = await self.client.get(f"{self.base_url}/api/tags")
                response.raise_for_status()
                data = response.json()

                # Find our model
                models = data.get("models", [])
                for model in models:
                    if model.get("name") == self.model:
                        return model

                return {"error": "Model not found"}

            except httpx.HTTPError as e:
                logger.error(f"HTTP error getting model info: {e}")
                raise

        elif self.backend == BackendType.LLAMA_CPP:
            if self.llm:
                return {
                    "backend": "llama_cpp",
                    "model_path": self.model_path,
                    "n_ctx": self.n_ctx,
                    "n_gpu_layers": self.n_gpu_layers,
                    "n_threads": self.n_threads,
                    "type_k": "Q8_0",
                    "type_v": "Q8_0",
                    "flash_attn": True
                }
            return {"error": "Model not loaded"}

        return {"error": "Unknown backend"}

    def create_grammar(self, grammar_text: str) -> Optional[Any]:
        """
        Create a grammar object for structured output.

        Args:
            grammar_text: Grammar string in GBNF format

        Returns:
            Grammar object (llama.cpp only)
        """
        if self.backend == BackendType.LLAMA_CPP:
            try:
                import llama_cpp
                return llama_cpp.LlamaGrammar.from_string(grammar_text)
            except ImportError:
                logger.error("llama-cpp-python not installed")
                return None
        else:
            logger.warning("Grammar only supported with llama.cpp backend")
            return None

    def get_prism_grammar(self) -> Optional[Any]:
        """
        Get the P.R.I.S.M. grammar for structured output.

        Returns:
            Grammar object for P.R.I.S.M. structured output
        """
        grammar_text = r'''
root ::= thought-process channel-output
thought-process ::= "<unused1>" [^\x00]* "<unused2>"
channel-output ::= [^\x00]* "Confidence: " [0-9.]+ "%" [^\x00]* ("🟢" | "🟡" | "🔴") [^\x00]*
'''
        return self.create_grammar(grammar_text)

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()


async def main():
    """Test the Gemma client."""
    import asyncio

    async with GemmaClient() as client:
        # Get model info
        info = await client.get_model_info()
        print("Model info:", json.dumps(info, indent=2))

        # Generate text
        print("\nGenerating text...")
        async for chunk in client.generate(
            prompt="What is the capital of France?",
            stream=True
        ):
            print(chunk.text, end="", flush=True)
            if chunk.is_complete:
                print("\n\nGeneration complete!")


if __name__ == "__main__":
    asyncio.run(main())

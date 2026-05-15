"""
P.R.I.S.M. Client Tests

Tests for the Gemma client module.
"""

import pytest
import sys
import types
from client.gemma_client import GemmaClient, BackendType

class TestGemmaClient:
    """Tests for GemmaClient."""

    @pytest.fixture
    def client(self):
        """Create a test client."""
        return GemmaClient(
            model_name="test-model",
            backend_type=BackendType.OLLAMA,
            host="localhost",
            port=11434
        )

    def test_client_initialization(self):
        """Test client initialization."""
        client = GemmaClient(
            model_name="test-model",
            backend_type=BackendType.OLLAMA,
            host="localhost",
            port=11434
        )
        assert client is not None
        assert client.model_name == "test-model"
        assert client.backend_type == BackendType.OLLAMA

    def test_backend_type_enum(self):
        """Test BackendType enum values."""
        assert BackendType.OLLAMA.value == "ollama"
        assert BackendType.LLAMA_CPP.value == "llama_cpp"

    def test_generate_prompt(self, client):
        """Test prompt generation."""
        prompt = "Test prompt"
        full_prompt = client._generate_prompt(prompt)
        assert prompt in full_prompt

    def test_llama_cpp_non_stream_uses_create_completion_prompt(self, event_loop, monkeypatch):
        """llama.cpp generation should use the current create_completion(prompt=...) API."""
        monkeypatch.setitem(sys.modules, "llama_cpp", types.SimpleNamespace())
        llama = _FakeCurrentLlamaCpp(
            [{"choices": [{"text": "Final answer"}], "finish_reason": "stop"}]
        )
        client = _llama_cpp_client_with(llama)
        grammar = object()

        chunks = event_loop.run_until_complete(_collect_chunks(
            client._generate_llama_cpp(
                prompt="Clinical prompt",
                temperature=0.2,
                max_tokens=32,
                stream=False,
                include_logprobs=True,
                grammar=grammar,
                stop=["</s>"],
            )
        ))

        assert [chunk.text for chunk in chunks] == ["Final answer"]
        assert chunks[0].is_complete is True
        assert llama.create_completion_calls == [{
            "prompt": "Clinical prompt",
            "max_tokens": 32,
            "temperature": 0.2,
            "top_p": 0.85,
            "echo": False,
            "grammar": grammar,
            "stop": ["</s>"],
        }]

    def test_llama_cpp_stream_uses_create_completion_prompt(self, event_loop, monkeypatch):
        """Streaming llama.cpp generation should not pass tokens= to Llama.__call__."""
        monkeypatch.setitem(sys.modules, "llama_cpp", types.SimpleNamespace())
        llama = _FakeCurrentLlamaCpp([
            {"choices": [{"text": "Part "}], "finish_reason": None},
            {"choices": [{"text": "done"}], "finish_reason": "stop"},
        ])
        client = _llama_cpp_client_with(llama)

        chunks = event_loop.run_until_complete(_collect_chunks(
            client._generate_llama_cpp(
                prompt="Streaming prompt",
                temperature=0.4,
                max_tokens=64,
                stream=True,
                include_logprobs=False,
                grammar=None,
                stop=None,
            )
        ))

        assert [chunk.text for chunk in chunks] == ["Part ", "done"]
        assert [chunk.is_complete for chunk in chunks] == [False, True]
        assert llama.create_completion_calls == [{
            "prompt": "Streaming prompt",
            "max_tokens": 64,
            "temperature": 0.4,
            "top_p": 0.85,
            "echo": False,
            "stream": True,
        }]


class _FakeCurrentLlamaCpp:
    """Fake llama-cpp-python 0.3.x surface: create_completion accepts prompt."""

    def __init__(self, responses):
        self.responses = responses
        self.create_completion_calls = []

    def tokenize(self, *_args, **_kwargs):
        return [1, 2, 3]

    def __call__(self, *_args, **kwargs):
        if "tokens" in kwargs:
            raise TypeError("Llama.__call__() got an unexpected keyword argument 'tokens'")
        raise AssertionError("Expected create_completion to be used")

    def create_completion(self, **kwargs):
        self.create_completion_calls.append(kwargs)
        if kwargs.get("stream"):
            return iter(self.responses)
        return self.responses[0]


def _llama_cpp_client_with(llama):
    client = GemmaClient.__new__(GemmaClient)
    client.backend = BackendType.LLAMA_CPP
    client.backend_type = BackendType.LLAMA_CPP
    client.llm = llama
    return client


async def _collect_chunks(generator):
    return [chunk async for chunk in generator]

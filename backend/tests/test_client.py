"""
P.R.I.S.M. Client Tests

Tests for the Gemma client module.
"""

import pytest
from unittest.mock import Mock, patch
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
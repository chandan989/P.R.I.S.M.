"""
P.R.I.S.M. Test Configuration

Pytest fixtures and test configuration.
"""

import pytest
import asyncio
from typing import AsyncGenerator
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def sample_deliberation_text():
    """Sample text with deliberation blocks for testing."""
    return """
Based on the patient's medication regimen, I need to analyze potential drug-drug interactions.

<|channel>thought
[Competing Hypotheses]
Interpretation A: Clarithromycin significantly increases warfarin levels [85%]
Supporting: CYP3A4 inhibition, documented interaction
Weakening: Patient has stable INR

Interpretation B: The interaction is minimal [15%]
Supporting: Patient on warfarin for long time
Weakening: Strong CYP3A4 inhibitor

[Discarded Paths]
✗ Discarded: No interaction - contradicts known pharmacology

[Logical Chain]
1. Clarithromycin is a potent CYP3A4 inhibitor
2. Warfarin is metabolized by CYP3A4
3. Therefore, clarithromycin will increase warfarin levels
4. This increases bleeding risk

▶ Selected: Interpretation A
<|channel>|

The patient is at high risk of bleeding due to the warfarin-clarithromycin interaction.
"""


@pytest.fixture
def sample_claims_text():
    """Sample text with pharmacological claims for testing."""
    return """
The patient is taking warfarin and clarithromycin together.
Clarithromycin significantly increases warfarin levels through CYP3A4 inhibition.
This interaction is contraindicated and may cause severe bleeding.
The recommended warfarin dose is 5mg daily.
Common side effects of warfarin include bleeding and bruising.
"""


@pytest.fixture
def sample_logprobs_data():
    """Sample logprobs data for testing."""
    return [
        {"token": "The", "token_id": 123, "logprob": -0.1},
        {"token": "patient", "token_id": 456, "logprob": -0.2},
        {"token": "is", "token_id": 789, "logprob": -0.15},
        {"token": "at", "token_id": 101, "logprob": -0.3},
        {"token": "risk", "token_id": 234, "logprob": -0.25},
    ]


@pytest.fixture
def event_loop():
    """Create an event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

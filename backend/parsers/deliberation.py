"""
P.R.I.S.M. Deliberation Parser

Parses thought blocks from Gemma 4 responses to extract
deliberation traces, competing hypotheses, and logical chains.
"""

import re
import json
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class Hypothesis:
    """A competing hypothesis with probability estimate."""
    interpretation: str
    probability: float
    supporting_evidence: List[str]
    weakening_evidence: List[str]


@dataclass
class DiscardedPath:
    """A reasoning path that was rejected."""
    hypothesis: str
    reason: str


@dataclass
class LogicalStep:
    """A step in the logical reasoning chain."""
    step_number: int
    description: str
    premises: List[str]
    conclusion: str


@dataclass
class DeliberationTrace:
    """Complete deliberation trace from thought blocks."""
    competing_hypotheses: List[Hypothesis]
    discarded_paths: List[DiscardedPath]
    logical_chain: List[LogicalStep]
    selected_interpretation: str
    raw_thought_blocks: List[str]


class DeliberationParser:
    """
    Parser for Gemma 4 thought blocks.

    Extracts structured deliberation information from
    the model's internal reasoning traces.
    """

    # Gemma 4 thought channel markers
    THOUGHT_START = "<|channel>thought\n"
    THOUGHT_END = "<|channel>|"

    # Structured headers (using reserved tokens from README)
    HEADERS = {
        "logical_chain": "<unused5>",
        "competing_hypotheses": "<unused6>",
        "discarded_paths": "<unused7>",
        "selected": "<unused8>",
        "discarded": "<unused9>"
    }
    
    # Legacy headers for backward compatibility
    LEGACY_HEADERS = {
        "logical_chain": "[Logical Chain]",
        "competing_hypotheses": "[Competing Hypotheses]",
        "discarded_paths": "[Discarded Paths]",
        "selected": "▶ Selected:",
        "discarded": "✗ Discarded:"
    }

    def __init__(self):
        """Initialize the deliberation parser."""
        # Compile regex patterns for efficiency
        self.hypothesis_pattern = re.compile(
            r"Interpretation\s+[A-Z]?:?\s*(.+?)\s*\[?(\d+(?:\.\d+)?)%?\]?"
        )
        self.evidence_pattern = re.compile(
            r"(Supporting|Weakening):\s*(.+?)(?=(?:Supporting|Weakening)|$)",
            re.IGNORECASE
        )
        self.step_pattern = re.compile(
            r"(\d+)\.\s*(.+?)(?=\d+\.|$)"
        )

    def parse(self, response_text: str) -> Optional[DeliberationTrace]:
        """
        Parse deliberation from response text.

        Args:
            response_text: Full response text from the model

        Returns:
            Deliberation trace if found, None otherwise
        """
        # Extract thought blocks
        thought_blocks = self._extract_thought_blocks(response_text)

        if not thought_blocks:
            logger.debug("No thought blocks found in response")
            return None

        # Parse each thought block
        all_hypotheses = []
        all_discarded = []
        all_steps = []
        selected = None

        for block in thought_blocks:
            # Parse competing hypotheses
            hypotheses = self._parse_hypotheses(block)
            all_hypotheses.extend(hypotheses)

            # Parse discarded paths
            discarded = self._parse_discarded_paths(block)
            all_discarded.extend(discarded)

            # Parse logical chain
            steps = self._parse_logical_chain(block)
            all_steps.extend(steps)

            # Parse selected interpretation
            if not selected:
                selected = self._parse_selected(block)

        # If no structured parsing succeeded, try fallback
        if not all_hypotheses and not all_steps:
            logger.debug("No structured deliberation found, using fallback")
            return self._fallback_parse(thought_blocks)

        return DeliberationTrace(
            competing_hypotheses=all_hypotheses,
            discarded_paths=all_discarded,
            logical_chain=all_steps,
            selected_interpretation=selected or "",
            raw_thought_blocks=thought_blocks
        )

    def _extract_thought_blocks(self, text: str) -> List[str]:
        """
        Extract all thought blocks from text.

        Args:
            text: Response text

        Returns:
            List of thought block contents
        """
        blocks = []

        # Standard extraction with markers
        start_pos = 0
        while True:
            start_idx = text.find(self.THOUGHT_START, start_pos)
            if start_idx == -1:
                start_idx = text.find("<unused0>", start_pos)
            
            if start_idx == -1:
                break

            end_idx = text.find(self.THOUGHT_END, start_idx)
            if end_idx == -1:
                end_idx = text.find("<unused1>", start_idx)
                
            if end_idx == -1:
                end_idx = text.find("Clinical Output:", start_idx)
                
            if end_idx == -1:
                break

            # Extract content between markers
            # If using <unused0>, start_idx + len
            if text[start_idx:start_idx+9] == "<unused0>":
                start_offset = 9
            else:
                start_offset = len(self.THOUGHT_START)
                
            content = text[start_idx + start_offset:end_idx]
            blocks.append(content.strip())

            start_pos = end_idx + (9 if text[end_idx:end_idx+9] == "<unused1>" else 0)

        # Fallback: if the prompt injected <unused0>, the generated text might just start with the thought block
        # and end with <unused1> or 'Clinical Output:'
        if not blocks:
            end_idx = text.find("<unused1>")
            if end_idx == -1:
                end_idx = text.find("Clinical Output:")
            
            if end_idx != -1 and end_idx > 0:
                blocks.append(text[:end_idx].strip())

        return blocks

    def _parse_hypotheses(self, text: str) -> List[Hypothesis]:
        """
        Parse competing hypotheses from text.

        Args:
            text: Thought block text

        Returns:
            List of hypotheses
        """
        hypotheses = []

        # Look for hypothesis section
        hypothesis_section = self._extract_section(
            text,
            self.HEADERS["competing_hypotheses"],
            self.LEGACY_HEADERS["competing_hypotheses"],
            [self.HEADERS["discarded_paths"], self.LEGACY_HEADERS["discarded_paths"], self.HEADERS["selected"], self.LEGACY_HEADERS["selected"]]
        )

        # Fallback for "Competing Interpretations:" format
        if not hypothesis_section:
            hypothesis_section = self._extract_section(
                text,
                "Competing Interpretations:",
                "Competing Interpretations:",
                ["Clinical Output:", "Logical Chain", "<unused"]
            )
            # If it's just the entire text before clinical output
            if not hypothesis_section and "Competing Interpretations:" in text:
                parts = text.split("Competing Interpretations:")
                if len(parts) > 1:
                    hypothesis_section = parts[1].split("Clinical Output:")[0].strip()

        if not hypothesis_section:
            return hypotheses

        current = None
        
        # Try finding numbered list formats like "1. **Major Interaction...** ... (Probability: 98%)"
        numbered_pattern = re.compile(r"(\d+)\.\s*(?:\*\*)?(.+?)(?:\*\*|:)?\s*(.*?)\s*\(\s*Probability:\s*(\d+(?:\.\d+)?)%\s*\)", re.IGNORECASE)
        for match in numbered_pattern.finditer(hypothesis_section):
            try:
                probability = float(match.group(4)) / 100.0
            except ValueError:
                probability = 0.0
                
            # Combine the label and description
            label = match.group(2).strip()
            desc = match.group(3).strip()
            if desc and not label.endswith(desc):
                 label = f"{label} {desc}"
                 
            hypotheses.append(Hypothesis(
                interpretation=label,
                probability=probability,
                supporting_evidence=[],
                weakening_evidence=[]
            ))
            
        # Try the original simpler numbered format "1. High risk... (85%)" if the above didn't match
        if not hypotheses:
            numbered_pattern_alt = re.compile(r"(\d+)\.\s*(.+?)\s*\((\d+(?:\.\d+)?)%\)")
            for match in numbered_pattern_alt.finditer(hypothesis_section):
                try:
                    probability = float(match.group(3)) / 100.0
                except ValueError:
                    probability = 0.0
                    
                hypotheses.append(Hypothesis(
                    interpretation=match.group(2).strip(),
                    probability=probability,
                    supporting_evidence=[],
                    weakening_evidence=[]
                ))
            
        if hypotheses:
            return hypotheses

        for line in hypothesis_section.splitlines():
            stripped = line.strip()
            if not stripped:
                continue

            match = self.hypothesis_pattern.match(stripped)
            if match:
                if current:
                    hypotheses.append(current)

                try:
                    probability = float(match.group(2)) / 100.0
                except ValueError:
                    probability = 0.0

                current = Hypothesis(
                    interpretation=match.group(1).strip(),
                    probability=probability,
                    supporting_evidence=[],
                    weakening_evidence=[]
                )
                continue

            if current and stripped.lower().startswith("supporting:"):
                current.supporting_evidence.append(stripped.split(":", 1)[1].strip())
            elif current and stripped.lower().startswith("weakening:"):
                current.weakening_evidence.append(stripped.split(":", 1)[1].strip())

        if current:
            hypotheses.append(current)

        return hypotheses

    def _parse_discarded_paths(self, text: str) -> List[DiscardedPath]:
        """
        Parse discarded reasoning paths from text.

        Args:
            text: Thought block text

        Returns:
            List of discarded paths
        """
        discarded = []

        # Look for discarded section
        discarded_section = self._extract_section(
            text,
            self.HEADERS["discarded_paths"],
            self.LEGACY_HEADERS["discarded_paths"],
            [self.HEADERS["selected"], self.LEGACY_HEADERS["selected"]]
        )

        if not discarded_section:
            return discarded

        # Parse each discarded path
        # Format: "✗ Discarded: [hypothesis] - [reason]" or "<unused9> [hypothesis] - [reason]"
        pattern = re.compile(r"(?:✗\s*Discarded:|<unused9>)\s*(.+?)\s*-\s*(.+)")
        for match in pattern.finditer(discarded_section):
            hypothesis = match.group(1).strip()
            reason = match.group(2).strip()

            discarded.append(DiscardedPath(
                hypothesis=hypothesis,
                reason=reason
            ))

        return discarded

    def _parse_logical_chain(self, text: str) -> List[LogicalStep]:
        """
        Parse logical reasoning chain from text.

        Args:
            text: Thought block text

        Returns:
            List of logical steps
        """
        steps = []

        # Look for logical chain section
        chain_section = self._extract_section(
            text,
            self.HEADERS["logical_chain"],
            self.LEGACY_HEADERS["logical_chain"],
            [self.HEADERS["competing_hypotheses"], self.LEGACY_HEADERS["competing_hypotheses"]]
        )

        if not chain_section:
            return steps

        # Parse each step line by line so single-line numbered steps do not
        # consume the remainder of the section.
        for line in chain_section.splitlines():
            match = re.match(r"^\s*(\d+)\.\s*(.+?)\s*$", line)
            if not match:
                continue

            step_num = int(match.group(1))
            description = match.group(2).strip()

            # Try to extract premises and conclusion
            premises = []
            conclusion = description

            # Look for "therefore" or "thus" indicators
            conclusion_pattern = re.compile(
                r"(.+?)(?:therefore|thus|so|consequently)\s*(.+)",
                re.IGNORECASE
            )
            conclusion_match = conclusion_pattern.search(description)

            if conclusion_match:
                premises_text = conclusion_match.group(1).strip()
                conclusion = conclusion_match.group(2).strip()

                # Split premises by commas or "and"
                premises = [
                    p.strip()
                    for p in re.split(r",\s*|\s+and\s+", premises_text)
                    if p.strip()
                ]

            steps.append(LogicalStep(
                step_number=step_num,
                description=description,
                premises=premises,
                conclusion=conclusion
            ))

        return steps

    def _parse_selected(self, text: str) -> Optional[str]:
        """
        Parse the selected interpretation from text.

        Args:
            text: Thought block text

        Returns:
            Selected interpretation if found
        """
        # Look for selected marker
        selected_pattern = re.compile(
            r"(?:▶\s*Selected:|<unused8>)\s*(.+?)(?:$|\n)"
        )
        match = selected_pattern.search(text)

        if match:
            return match.group(1).strip()

        return None

    def _extract_section(
        self,
        text: str,
        header: str,
        legacy_header: str,
        stop_at: Optional[List[str]] = None
    ) -> Optional[str]:
        """
        Extract a section from text between header and stop markers.

        Args:
            text: Full text
            header: Section header to find
            legacy_header: Fallback legacy header
            stop_at: List of headers that end this section

        Returns:
            Section text if found, None otherwise
        """
        # Find header
        header_idx = text.find(header)
        active_header = header
        if header_idx == -1:
            header_idx = text.find(legacy_header)
            active_header = legacy_header
            
        if header_idx == -1:
            return None

        # Find end of section
        start_pos = header_idx + len(active_header)
        end_pos = len(text)

        if stop_at:
            for stop_header in stop_at:
                stop_idx = text.find(stop_header, start_pos)
                if stop_idx != -1 and stop_idx < end_pos:
                    end_pos = stop_idx

        return text[start_pos:end_pos].strip()

    def _fallback_parse(self, thought_blocks: List[str]) -> Optional[DeliberationTrace]:
        """
        Fallback parsing when structured format is not found.

        Args:
            thought_blocks: List of thought block contents

        Returns:
            Basic deliberation trace
        """
        if not thought_blocks:
            return None

        # Combine all thought blocks
        combined = "\n".join(thought_blocks)

        # Try to extract any numbered steps
        steps = []
        for match in self.step_pattern.finditer(combined):
            step_num = int(match.group(1))
            description = match.group(2).strip()

            steps.append(LogicalStep(
                step_number=step_num,
                description=description,
                premises=[],
                conclusion=description
            ))

        return DeliberationTrace(
            competing_hypotheses=[],
            discarded_paths=[],
            logical_chain=steps,
            selected_interpretation="",
            raw_thought_blocks=thought_blocks
        )

    def to_dict(self, trace: DeliberationTrace) -> Dict[str, Any]:
        """
        Convert deliberation trace to dictionary.

        Args:
            trace: Deliberation trace

        Returns:
            Dictionary representation
        """
        return {
            "competing_hypotheses": [
                {
                    "interpretation": h.interpretation,
                    "probability": h.probability,
                    "supporting_evidence": h.supporting_evidence,
                    "weakening_evidence": h.weakening_evidence
                }
                for h in trace.competing_hypotheses
            ],
            "discarded_paths": [
                {
                    "hypothesis": d.hypothesis,
                    "reason": d.reason
                }
                for d in trace.discarded_paths
            ],
            "logical_chain": [
                {
                    "step_number": s.step_number,
                    "description": s.description,
                    "premises": s.premises,
                    "conclusion": s.conclusion
                }
                for s in trace.logical_chain
            ],
            "selected_interpretation": trace.selected_interpretation,
            "raw_thought_blocks": trace.raw_thought_blocks
        }


def main():
    """Test the deliberation parser."""
    # Example response with thought blocks
    example_response = """
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

    parser = DeliberationParser()
    trace = parser.parse(example_response)

    if trace:
        print("Deliberation Trace:")
        print(json.dumps(parser.to_dict(trace), indent=2))
    else:
        print("No deliberation found")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
P.R.I.S.M. Standalone Inference Script

Run P.R.I.S.M. with llama.cpp directly for local inference.
This script provides a complete pipeline similar to the user's code.
"""

import glob
import os
import time
import argparse
import json
from typing import Optional, List

try:
    import llama_cpp
except ImportError:
    print("Error: llama-cpp-python not installed.")
    print("Install with: pip install llama-cpp-python")
    exit(1)


# P.R.I.S.M. System Prompt
PRISM_SYSTEM_PROMPT = """For every response:
1. Begin reasoning with <unused0> to expose your deliberation
2. Enumerate competing interpretations with probability estimates
3. Use tool calls to verify factual claims when confidence is low
4. Start your final clinical output exactly with a signal dot (🟢, 🟡, or 🔴).
5. Include a confidence assessment formatted exactly as 'Confidence: ✅ [LEVEL]'.
6. Conclude with a clear 'Recommendation:' block."""


# P.R.I.S.M. Grammar for structured output
PRISM_GRAMMAR = r'''
root ::= thought-process channel-output
thought-process ::= "<unused1>" [^\x00]* "<unused2>"
channel-output ::= [^\x00]* "Confidence: " [0-9.]+ "%" [^\x00]* ("🟢" | "🟡" | "🔴") [^\x00]*
'''


class PrismInference:
    """P.R.I.S.M. inference engine using llama.cpp."""

    def __init__(
        self,
        model_path: str,
        n_ctx: int = 4096,
        n_gpu_layers: int = 28,
        n_threads: int = 4,
        verbose: bool = False
    ):
        """
        Initialize the P.R.I.S.M. inference engine.

        Args:
            model_path: Path to GGUF model file or directory
            n_ctx: Context window size
            n_gpu_layers: Number of layers to offload to GPU
            n_threads: Number of CPU threads
            verbose: Enable verbose logging
        """
        self.model_path = self._find_model_file(model_path)
        self.n_ctx = n_ctx
        self.n_gpu_layers = n_gpu_layers
        self.n_threads = n_threads
        self.verbose = verbose

        self.llm = None
        self.grammar = None

    def _find_model_file(self, path: str) -> str:
        """Find the GGUF file to load."""
        if os.path.isfile(path):
            return path

        if os.path.isdir(path):
            gguf_files = glob.glob(f"{path}/*.gguf")
            gguf_files.sort()
            if gguf_files:
                return gguf_files[0]

        raise FileNotFoundError(f"No GGUF file found at: {path}")

    def load_model(self):
        """Load the model into memory."""
        print(f"Loading GGUF file: {self.model_path}")
        print("Loading model into memory with partial offloading and KV compression...")

        start = time.time()

        self.llm = llama_cpp.Llama(
            model_path=self.model_path,
            n_ctx=self.n_ctx,
            n_gpu_layers=self.n_gpu_layers,
            type_k=llama_cpp.GGML_TYPE_Q8_0,
            type_v=llama_cpp.GGML_TYPE_Q8_0,
            flash_attn=True,
            n_threads=self.n_threads,
            verbose=self.verbose,
        )

        elapsed = time.time() - start
        print(f"✅ Model loaded in {elapsed:.1f}s")

        # Create grammar
        self.grammar = llama_cpp.LlamaGrammar.from_string(PRISM_GRAMMAR)

    def generate(
        self,
        query: str,
        temperature: float = 0.6,
        max_tokens: int = 3072,
        use_grammar: bool = True,
        stream: bool = False
    ) -> str:
        """
        Generate a response for the given query.

        Args:
            query: User query
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            use_grammar: Whether to use grammar for structured output
            stream: Whether to stream the response

        Returns:
            Generated response
        """
        if not self.llm:
            raise RuntimeError("Model not loaded. Call load_model() first.")

        # Build prompt
        prompt = f"{PRISM_SYSTEM_PROMPT}\n<bos><start_of_turn>user\n{query}<end_of_turn>\n<start_of_turn>model\n<unused0>\n"

        # Tokenize
        prompt_tokens = self.llm.tokenize(prompt.encode("utf-8"), add_bos=False, special=True)

        # Prepare generation parameters
        gen_params = {
            "tokens": prompt_tokens,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "top_p": 0.85,
            "echo": False,
            "stop": ["<eos>", "<end_of_turn>"]
        }

        if use_grammar and self.grammar:
            gen_params["grammar"] = self.grammar

        # Generate
        if stream:
            print("========== STREAMING RESPONSE ==========")
            for chunk in self.llm(**gen_params, stream=True):
                text = chunk["choices"][0]["text"]
                print(text, end="", flush=True)
            print("\n=========================================")
            return ""
        else:
            print("Running evaluation prompt...")
            output = self.llm(**gen_params)
            response = output['choices'][0]['text']

            print("========== LLAMA.CPP MODEL RESPONSE ==========")
            print(response)
            print("=========================================")

            return response

    def evaluate_structure(self, response: str) -> dict:
        """
        Evaluate the structure of the response.

        Args:
            response: Generated response

        Returns:
            Dictionary with evaluation metrics
        """
        print("========== STRUCTURE EVALUATION ==========")

        metrics = {
            "Has Logical Chain": "<unused5>" in response,
            "Has Competing Hypotheses": "<unused6>" in response,
            "Has Discarded Paths": "<unused7>" in response,
            "Has Final Output Signal": "🟢" in response or "🟡" in response or "🔴" in response,
            "Has Confidence Badge": "Confidence:" in response
        }

        # Tool calls are circumstantial
        used_tool = "<unused3>" in response
        print(f"Tool Call Triggered: {'Yes' if used_tool else 'No (Model deemed it unnecessary)'}")

        print("\n--- Structured Output Evaluation ---")
        score = sum(1 for passed in metrics.values() if passed)
        for key, passed in metrics.items():
            print(f"{key}: {'✅ Pass' if passed else '❌ Fail'}")

        print(f"\nOverall Structure Score: {score}/{len(metrics)}")

        return {
            "metrics": metrics,
            "score": score,
            "total": len(metrics),
            "used_tool": used_tool
        }


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="P.R.I.S.M. Standalone Inference",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with default settings
  python prism_inference.py --model-path ./models

  # Run with custom settings
  python prism_inference.py --model-path ./models --n-gpu-layers 30 --temperature 0.5

  # Run with streaming output
  python prism_inference.py --model-path ./models --stream

  # Run with a specific query
  python prism_inference.py --model-path ./models --query "What are the side effects of warfarin?"
        """
    )

    parser.add_argument(
        "--model-path",
        type=str,
        required=True,
        help="Path to GGUF model file or directory"
    )

    parser.add_argument(
        "--n-ctx",
        type=int,
        default=4096,
        help="Context window size (default: 4096)"
    )

    parser.add_argument(
        "--n-gpu-layers",
        type=int,
        default=28,
        help="Number of layers to offload to GPU (default: 28)"
    )

    parser.add_argument(
        "--n-threads",
        type=int,
        default=4,
        help="Number of CPU threads (default: 4)"
    )

    parser.add_argument(
        "--temperature",
        type=float,
        default=0.6,
        help="Sampling temperature (default: 0.6)"
    )

    parser.add_argument(
        "--max-tokens",
        type=int,
        default=3072,
        help="Maximum tokens to generate (default: 3072)"
    )

    parser.add_argument(
        "--no-grammar",
        action="store_true",
        help="Disable grammar enforcement"
    )

    parser.add_argument(
        "--stream",
        action="store_true",
        help="Stream the response"
    )

    parser.add_argument(
        "--query",
        type=str,
        help="Query to process (default: polypharmacy example)"
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )

    args = parser.parse_args()

    # Default query
    if not args.query:
        args.query = "Patient is a 68yo male on Warfarin 5mg daily, Fluconazole 200mg for 14 days, and Aspirin 81mg. Review for interactions."

    # Initialize inference engine
    prism = PrismInference(
        model_path=args.model_path,
        n_ctx=args.n_ctx,
        n_gpu_layers=args.n_gpu_layers,
        n_threads=args.n_threads,
        verbose=args.verbose
    )

    # Load model
    prism.load_model()

    # Generate response
    response = prism.generate(
        query=args.query,
        temperature=args.temperature,
        max_tokens=args.max_tokens,
        use_grammar=not args.no_grammar,
        stream=args.stream
    )

    # Evaluate structure (if not streaming)
    if not args.stream and response:
        prism.evaluate_structure(response)


if __name__ == "__main__":
    main()

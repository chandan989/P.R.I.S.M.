# P.R.I.S.M. Agents

Based on the project architecture and descriptions in the `README.md`, P.R.I.S.M. consists of several specialized agents or sub-systems that work together to provide a transparent, reliable clinical decision support tool for polypharmacy auditing.

## 1. Latent Deliberation Engine
**Role:** The reasoning core.
**Responsibilities:**
- Intercepts and captures Gemma 4's native `<|channel>thought\n` blocks.
- Exposes the internal reasoning process to the user.
- Enumerates competing hypotheses with probability estimates.
- Details discarded reasoning paths and step-by-step logical chains.
- Operates primarily through the fine-tuned Deliberation Format Adapter.

## 2. Source Grounding Visualizer / Verification Agent
**Role:** The factual checker.
**Responsibilities:**
- Extracts factual claims (specifically pharmacological assertions) from the AI's final output.
- Verifies extracted claims against a curated clinical knowledge base (FDA Drug Labels, DrugBank, PubMed/MIMIC).
- Operates offline using a highly quantized, ultra-lightweight dense embedding model (e.g., ONNX-optimized MiniLM-L6) running on the CPU.
- Generates verification signals (🟢 Confirmed, 🟡 Inferred, ⚪ Out of Scope, 🔴 Contradicted) inline with the response.

## 3. Certainty Indicator System
**Role:** The confidence calibrator.
**Responsibilities:**
- Translates model certainty into explicit, accessible signals (badges, progress bars, color codes).
- Employs Dynamic Conformal Prediction paired with an out-of-distribution (OOD) detector to establish confidence boundaries.
- Uses Speculative Decoding (Draft & Verify) where a small model drafts the reasoning and the 26B model verifies it, speeding up inference and maintaining quality.

## 4. Delta Update Agent
**Role:** The knowledge base synchronizer.
**Responsibilities:**
- Ensures the local, air-gapped clinical knowledge base stays current with the latest medical data.
- Runs nightly at 02:00 local time.
- Pulls encrypted delta bundles (TLS 1.3, one-way pull).
- Verifies Ed25519 signatures and decrypts AES-256-GCM payloads.
- Applies deltas to the local FAISS/ChromaDB index and re-embeds new/modified documents.
- Writes update receipts to an encrypted local audit log (TPM/HSM).

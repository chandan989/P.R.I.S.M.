#!/usr/bin/env python3
"""
P.R.I.S.M. Setup Script

Initializes the P.R.I.S.M. knowledge base and backend.
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path


def run_command(cmd, cwd=None):
    """Run a command and return success status."""
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True, cwd=cwd)
    return result.returncode == 0


def setup_backend():
    """Setup the backend."""
    print("\n=== Setting up Backend ===")

    backend_dir = Path("backend")

    # Create virtual environment
    if not (backend_dir / "venv").exists():
        print("Creating virtual environment...")
        if not run_command(f"python3 -m venv {backend_dir / 'venv'}"):
            print("Failed to create virtual environment")
            return False

    # Install dependencies
    print("Installing backend dependencies...")
    pip_path = backend_dir / "venv" / "bin" / "pip"
    if not run_command(f"{pip_path} install -r {backend_dir / 'requirements.txt'}"):
        print("Failed to install dependencies")
        return False

    # Create .env file
    env_file = backend_dir / ".env"
    if not env_file.exists():
        print("Creating .env file...")
        import shutil
        shutil.copy(backend_dir / ".env.example", env_file)

    print("Backend setup complete!")
    return True


def setup_knowledge_base():
    """Setup the knowledge base."""
    print("\n=== Setting up Knowledge Base ===")

    kb_dir = Path("knowledge_base")

    # Create directory structure
    print("Creating directory structure...")
    directories = [
        kb_dir / "sources" / "fda" / "drug_labels",
        kb_dir / "sources" / "fda" / "safety_communications",
        kb_dir / "sources" / "fda" / "medwatch",
        kb_dir / "sources" / "drugbank" / "interaction_profiles",
        kb_dir / "sources" / "drugbank" / "enzyme_data",
        kb_dir / "sources" / "drugbank" / "pharmacokinetics",
        kb_dir / "sources" / "pubmed" / "pharmacovigilance",
        kb_dir / "sources" / "pubmed" / "clinical_trials",
        kb_dir / "sources" / "pubmed" / "case_reports",
        kb_dir / "sources" / "mimic" / "clinical_notes",
        kb_dir / "sources" / "mimic" / "medication_records",
        kb_dir / "sources" / "mimic" / "lab_results",
        kb_dir / "sources" / "formulary" / "institutional_drugs",
        kb_dir / "sources" / "formulary" / "dosage_guidelines",
        kb_dir / "sources" / "formulary" / "contraindications",
        kb_dir / "index",
        kb_dir / "audit",
        kb_dir / "backups",
        kb_dir / "delta_agent" / "keys",
    ]

    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)

    # Install knowledge base dependencies
    print("Installing knowledge base dependencies...")
    if not run_command("pip install -r knowledge_base/requirements.txt"):
        print("Failed to install knowledge base dependencies")
        return False

    # Create sample documents
    print("Creating sample documents...")
    create_sample_documents(kb_dir)

    # Build initial index
    print("Building initial index...")
    if not run_command("python knowledge_base/knowledge_base.py --rebuild"):
        print("Failed to build index")
        return False

    print("Knowledge base setup complete!")
    return True


def create_sample_documents(kb_dir: Path):
    """Create sample documents for testing."""
    import json

    # Sample FDA document
    fda_doc = {
        "doc_id": "fda-warfarin-label-sample",
        "content": "Warfarin sodium tablets are indicated for the prophylaxis and/or treatment of venous thrombosis. CONTRAINDICATIONS: Warfarin is contraindicated in any condition where the hazard of hemorrhage might be greater than the potential clinical benefits. DRUG INTERACTIONS: CYP3A4 inhibitors like clarithromycin can significantly increase warfarin levels and bleeding risk.",
        "metadata": {
            "source": "fda",
            "category": "drug_labels",
            "drugs": ["warfarin", "clarithromycin"],
            "severity": "critical",
            "date": "2024-01-15"
        }
    }

    fda_path = kb_dir / "sources" / "fda" / "drug_labels" / "fda-warfarin-label-sample.json"
    with open(fda_path, 'w') as f:
        json.dump(fda_doc, f, indent=2)

    # Sample DrugBank document
    drugbank_doc = {
        "doc_id": "drugbank-warfarin-interaction-sample",
        "content": "Warfarin and clarithromycin interaction: Clarithromycin is a potent inhibitor of CYP3A4, the primary enzyme responsible for warfarin metabolism. This interaction leads to increased warfarin plasma concentrations and enhanced anticoagulant effect, significantly increasing the risk of bleeding.",
        "metadata": {
            "source": "drugbank",
            "category": "interaction_profiles",
            "drugs": ["warfarin", "clarithromycin"],
            "severity": "critical",
            "date": "2024-02-01",
            "enzymes": ["CYP3A4"]
        }
    }

    drugbank_path = kb_dir / "sources" / "drugbank" / "interaction_profiles" / "drugbank-warfarin-interaction-sample.json"
    with open(drugbank_path, 'w') as f:
        json.dump(drugbank_doc, f, indent=2)

    print(f"Created {len(list(kb_dir.rglob('*.json')))} sample documents")


def setup_frontend():
    """Setup the frontend."""
    print("\n=== Setting up Frontend ===")

    frontend_dir = Path("prism-web")

    if not frontend_dir.exists():
        print("Frontend directory not found. Skipping frontend setup.")
        return True

    # Install dependencies
    print("Installing frontend dependencies...")
    if not run_command("npm install", cwd=frontend_dir):
        print("Failed to install frontend dependencies")
        return False

    print("Frontend setup complete!")
    return True


def generate_keys():
    """Generate cryptographic keys for delta updates."""
    print("\n=== Generating Cryptographic Keys ===")

    from cryptography.hazmat.primitives.asymmetric import ed25519
    from cryptography.hazmat.primitives import serialization
    import secrets

    keys_dir = Path("knowledge_base/delta_agent/keys")
    keys_dir.mkdir(parents=True, exist_ok=True)

    # Generate Ed25519 key pair
    private_key = ed25519.Ed25519PrivateKey.generate()
    public_key = private_key.public_key()

    # Save private key
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )

    with open(keys_dir / "private_key.pem", 'wb') as f:
        f.write(private_pem)

    # Save public key
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )

    with open(keys_dir / "public_key.pem", 'wb') as f:
        f.write(public_pem)

    # Generate AES-256-GCM key
    decryption_key = secrets.token_bytes(32)

    with open(keys_dir / "decryption_key.bin", 'wb') as f:
        f.write(decryption_key)

    print("Keys generated successfully!")
    print(f"  Private key: {keys_dir / 'private_key.pem'}")
    print(f"  Public key: {keys_dir / 'public_key.pem'}")
    print(f"  Decryption key: {keys_dir / 'decryption_key.bin'}")

    return True


def main():
    """Main setup function."""
    parser = argparse.ArgumentParser(description="P.R.I.S.M. Setup")
    parser.add_argument("--backend", action="store_true", help="Setup backend only")
    parser.add_argument("--knowledge-base", action="store_true", help="Setup knowledge base only")
    parser.add_argument("--frontend", action="store_true", help="Setup frontend only")
    parser.add_argument("--keys", action="store_true", help="Generate keys only")
    parser.add_argument("--all", action="store_true", help="Setup everything (default)")

    args = parser.parse_args()

    # Default to all if no specific option selected
    if not any([args.backend, args.knowledge_base, args.frontend, args.keys]):
        args.all = True

    success = True

    if args.all or args.backend:
        if not setup_backend():
            success = False

    if args.all or args.knowledge_base:
        if not setup_knowledge_base():
            success = False

    if args.all or args.frontend:
        if not setup_frontend():
            success = False

    if args.all or args.keys:
        if not generate_keys():
            success = False

    if success:
        print("\n✅ Setup complete!")
        print("\nNext steps:")
        print("1. Start Ollama: ollama serve")
        print("2. Pull the model: ollama pull hf.co/chandan989/gemma-4-26B-A4B-it-MXFP4_MOE.gguf")
        print("3. Start the backend: cd backend && source venv/bin/activate && python server.py")
        print("4. Start the frontend: cd prism-web && npm run dev")
    else:
        print("\n❌ Setup encountered errors. Please check the output above.")
        sys.exit(1)


if __name__ == "__main__":
    main()

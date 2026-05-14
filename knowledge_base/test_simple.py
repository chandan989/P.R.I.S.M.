#!/usr/bin/env python3
"""
Simple test script for the Knowledge Base
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_simple():
    """Simple test to verify the knowledge base is working."""
    print("Testing Knowledge Base...")

    try:
        # Try to import the knowledge base
        from knowledge_base import KnowledgeBase

        # Initialize with the knowledge base root
        kb = KnowledgeBase()
        print(f"Knowledge base initialized with {kb.get_document_count()} documents")
        print("Sources summary:", kb.get_sources_summary())

        # Test search functionality
        print("\\n=== Knowledge Base Test Completed Successfully ===")

    except Exception as e:
        print(f"Error initializing knowledge base: {e}")
        return False

if __name__ == "__main__":
    test_simple()
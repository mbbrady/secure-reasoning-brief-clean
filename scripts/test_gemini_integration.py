#!/usr/bin/env python3
"""
Test script for Gemini integration in RKL Secure Reasoning Brief.

This script validates the Gemini + Ollama hybrid model approach for the
Kaggle AI Agents Capstone submission.

Usage:
    python scripts/test_gemini_integration.py
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'scripts'))

from gemini_client import GeminiClient, HybridModelClient, test_gemini_connection
from fetch_and_summarize import OllamaClient  # Import existing Ollama client


def test_gemini_only():
    """Test Gemini client directly"""
    print("\n" + "="*60)
    print("TEST 1: Gemini Client Only")
    print("="*60)

    try:
        client = GeminiClient(model_name="gemini-2.0-flash")
        print("✅ Gemini client initialized")

        # Test simple generation
        response = client.generate(
            prompt="What is Type III secure reasoning? Answer in one sentence.",
            temperature=0.3
        )
        print(f"\n✅ Gemini response:")
        print(f"   {response}")

        return True
    except Exception as e:
        print(f"❌ Gemini test failed: {e}")
        return False


def test_hybrid_client():
    """Test hybrid Gemini + Ollama client"""
    print("\n" + "="*60)
    print("TEST 2: Hybrid Client (Gemini + Ollama Fallback)")
    print("="*60)

    try:
        # Initialize Ollama client (fallback)
        ollama_endpoint = os.getenv('OLLAMA_ENDPOINT', 'http://192.168.1.11:11434/api/generate')
        ollama = OllamaClient(endpoint=ollama_endpoint, model="llama3.2:8b")
        print("✅ Ollama client initialized")

        # Initialize hybrid client
        hybrid = HybridModelClient(
            ollama_client=ollama,
            gemini_model="gemini-2.0-flash",
            use_gemini_for=['qa_review', 'fact_check', 'governance']
        )
        print("✅ Hybrid client initialized")

        # Get status
        status = hybrid.get_status()
        print(f"\n📊 Hybrid Client Status:")
        print(f"   Gemini available: {status['gemini_available']}")
        print(f"   Gemini model: {status['gemini_model']}")
        print(f"   Ollama available: {status['ollama_available']}")
        print(f"   Ollama model: {status['ollama_model']}")
        print(f"   Gemini preferred for: {status['preferred_for_critical']}")

        # Test critical task (should use Gemini)
        print("\n🔍 Testing critical QA task (should use Gemini)...")
        qa_result = hybrid.generate(
            prompt="Rate this text for quality (0-10): 'The agent processes data locally.'",
            task_type="qa_review",
            temperature=0.1
        )
        print(f"✅ QA Task Result:")
        print(f"   Model used: {qa_result['model_used']}")
        print(f"   Response: {qa_result['response'][:100]}...")

        # Test bulk task (should use Ollama)
        print("\n📝 Testing bulk task (should use Ollama)...")
        bulk_result = hybrid.generate(
            prompt="Count words in: 'Hello world'",
            task_type="word_count",
            temperature=0.0
        )
        print(f"✅ Bulk Task Result:")
        print(f"   Model used: {bulk_result['model_used']}")
        print(f"   Response: {bulk_result['response'][:100]}...")

        return True
    except Exception as e:
        print(f"❌ Hybrid client test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_qa_review_simulation():
    """Simulate a QA review task"""
    print("\n" + "="*60)
    print("TEST 3: QA Review Simulation")
    print("="*60)

    try:
        # Setup hybrid client
        ollama_endpoint = os.getenv('OLLAMA_ENDPOINT', 'http://192.168.1.11:11434/api/generate')
        ollama = OllamaClient(endpoint=ollama_endpoint, model="llama3.2:8b")
        hybrid = HybridModelClient(ollama_client=ollama)

        # Simulate QA review
        test_brief = """
        # Weekly AI Governance Brief

        ## Article 1: New Research on AI Alignment
        Technical Summary: Researchers propose novel approach to AI alignment
        using constrained optimization...

        Implications: Organizations should consider alignment frameworks...
        """

        print("📋 Simulating QA review of sample brief...")
        qa_prompt = f"""Review this brief for quality. Score 0-10 and provide feedback.

Brief:
{test_brief}

Provide:
1. Overall score (0-10)
2. Key issues found
3. Decision: PASS/REVISE/FAIL
"""

        result = hybrid.generate(
            prompt=qa_prompt,
            system_prompt="You are a QA reviewer for AI governance briefs.",
            task_type="qa_review",
            temperature=0.1
        )

        print(f"\n✅ QA Review Complete:")
        print(f"   Model used: {result['model_used']}")
        print(f"   Review:\n{result['response']}")

        return True
    except Exception as e:
        print(f"❌ QA review simulation failed: {e}")
        return False


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("RKL Secure Reasoning Brief - Gemini Integration Tests")
    print("Kaggle 5-Day AI Agents Intensive - Capstone Project")
    print("="*60)

    # Check API key
    api_key = os.getenv('GOOGLE_API_KEY')
    if not api_key:
        print("\n❌ ERROR: GOOGLE_API_KEY not found in environment")
        print("   Set it in .env file or environment variables")
        print("   Get key from: https://aistudio.google.com/app/apikey")
        return False

    print(f"\n✅ API key found: {api_key[:15]}...")

    # Run tests
    tests = [
        ("Gemini Only", test_gemini_only),
        ("Hybrid Client", test_hybrid_client),
        ("QA Review Simulation", test_qa_review_simulation)
    ]

    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except KeyboardInterrupt:
            print("\n\n⚠️  Tests interrupted by user")
            break
        except Exception as e:
            print(f"\n❌ Unexpected error in {test_name}: {e}")
            results.append((test_name, False))

    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")

    all_passed = all(r for _, r in results)
    if all_passed:
        print("\n🎉 All tests passed! Gemini integration working correctly.")
        print("\n✅ Ready for Kaggle Capstone submission!")
    else:
        print("\n⚠️  Some tests failed. Check errors above.")

    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

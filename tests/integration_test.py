#!/usr/bin/env python3
"""
Integration test: Verify AI modules work when imported by GUI.
Uses the live tailoring path (tailor.py) that the GUI actually calls.
Note: hits the live Gemini API; requires GEMINI_API_KEY in .env.
"""

import sys
from pathlib import Path

# Point to project root (parent of tests/)
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from AI.match_analyzer import analyze_match
from tailor import process_and_tailor_from_gui

def test_ai_integration():
    """Test AI modules can be imported and called from GUI context"""
    print("=== Integration Test (live API, GUI code path) ===")

    # Test data
    resume = """Senior Software Engineer with 5 years experience.
    Skills: Python, JavaScript, React, Node.js, AWS.
    Experience: Led team of 5 engineers, delivered 3 production systems.
    Education: BS Computer Science, MIT."""

    job = """Full Stack Developer role requiring:
    - Python expertise for backend development
    - React and modern JavaScript frameworks
    - Cloud experience (AWS preferred)
    - Leadership capabilities
    - 3+ years professional experience"""

    # Test match analysis
    print("\n1. Testing match analysis...")
    match = analyze_match(resume, job)
    score = match['overall_score']
    assert score >= 0, f"Invalid score: {score}"
    print(f"   Match score: {score}%")

    # Test tailoring through the same function the GUI calls
    print("\n2. Testing resume tailoring...")
    result = process_and_tailor_from_gui(
        resume, job, PROJECT_ROOT / "output", "Standard", None,
        job_title="Full Stack Developer", company_name="Test Corp",
    )
    assert result and result.get("resume_text"), "Empty tailoring result"
    assert len(result["resume_text"]) > 100, "Tailored resume too short"
    print(f"   Tailored resume length: {len(result['resume_text'])} chars")
    print(f"   Cover letter length: {len(result['cover_letter'])} chars")

    print("\n=== ALL TESTS PASSED ===")
    return True

if __name__ == "__main__":
    try:
        test_ai_integration()
        sys.exit(0)
    except Exception as e:
        print("\n=== TEST FAILED ===")
        print(f"Error: {e}")
        sys.exit(1)

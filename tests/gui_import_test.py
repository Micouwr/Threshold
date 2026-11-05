#!/usr/bin/env python3
"""
GUI Import Test
Verify AI modules can be imported in GUI context.
"""

import sys
from pathlib import Path

# Point to project root (parent directory)
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def test_ai_modules_import():
    from AI.match_analyzer import analyze_match
    from tailor import process_and_tailor_from_gui
    from config.settings import MIN_MATCH_THRESHOLD

    assert callable(analyze_match)
    assert callable(process_and_tailor_from_gui)
    assert MIN_MATCH_THRESHOLD == 80

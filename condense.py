"""AI-assisted resume condensing.

When a tailored resume runs over 2 pages, the AI analyzes it and proposes
specific, selectable options: roles or bullets that could be removed or
condensed, and bullets that could use tighter wording. The user picks which
options to apply; nothing is cut silently.
"""

import os
import json
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).parent / ".env")

try:
    from config.settings import GEMINI_MODEL
except ImportError:
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")


def _get_model():
    import google.generativeai as genai
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key == "your_api_key_here":
        raise Exception("GEMINI_API_KEY not configured")
    genai.configure(api_key=api_key)
    return genai.GenerativeModel(GEMINI_MODEL)


def _parse_json_response(response_text):
    text = response_text.strip()
    if text.startswith("```json"):
        text = text[7:]
    if text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return json.loads(text.strip())


def suggest_condense_options(resume_text):
    """Ask the AI for condense options. Returns a list of option dicts.

    Each option: {id, type, section, description, original, suggested,
                  lines_saved_estimate}
    Types: "remove" (drop a bullet/role), "condense" (merge/shorten a section),
           "tighten" (rewrite a bullet more concisely).
    """
    model = _get_model()
    prompt = f"""
    This resume runs over 2 pages and needs condensing. Analyze it and propose
    specific options for reducing length. Return ONLY a valid JSON object with
    an "options" array. Each option must have these exact keys:
    id (integer), type ("remove", "condense", or "tighten"), section (string),
    description (string, plain-language explanation of what would change and why),
    original (string, the exact current text, or "" if not applicable),
    suggested (string, the replacement text, or "" for removals),
    lines_saved_estimate (integer).

    Rules:
    - Base everything SOLELY on the resume text. Do not invent content.
    - Prefer condensing older or less relevant roles first.
    - For "tighten" options, keep every fact; only make the wording more concise.
    - For "remove" options, only suggest removing content that adds the least value
      for a hiring manager (oldest roles, redundant bullets).
    - Provide 3-6 options, ordered by most lines saved first.
    - Keep descriptions short and plain, no buzzwords.

    Example:
    {{
        "options": [
            {{
                "id": 1,
                "type": "condense",
                "section": "Professional Experience",
                "description": "Reduce the 1996-2005 Technical Consultant role from 4 bullets to 2, keeping the most relevant points",
                "original": "- Provided IT support...\\n- Handled PC setup...",
                "suggested": "- Provided IT support and consulting for 50+ SMB clients, including PC setup and infrastructure support",
                "lines_saved_estimate": 3
            }},
            {{
                "id": 2,
                "type": "tighten",
                "section": "Professional Experience",
                "description": "Tighten a wordy bullet without losing any facts",
                "original": "Was responsible for the creation and delivery of a structured training program...",
                "suggested": "Created and delivered MillBox 101, a structured dealer training program...",
                "lines_saved_estimate": 1
            }}
        ]
    }}

    RESUME:
    {resume_text}
    """
    response = model.generate_content(prompt)
    result = _parse_json_response(response.text)
    return result.get("options", [])


def apply_condense_options(resume_text, selected_options):
    """Apply the user's selected condense options. Returns the revised resume
    text in the same structured format (name/tagline/## sections/etc.)."""
    model = _get_model()
    options_json = json.dumps(selected_options, indent=2)
    prompt = f"""
    Apply ONLY the following condense options to the resume below. Return the
    FULL revised resume, keeping the exact structured format (ALL CAPS name line,
    tagline, contact line, ## section headers, ### Role | Company, *location | dates*,
    - bullets, **bold** labels). Do not change anything except what the selected
    options describe. Do not add new information. Keep every fact.

    SELECTED OPTIONS:
    {options_json}

    RESUME:
    {resume_text}

    Return ONLY the revised resume text, no explanations.
    """
    response = model.generate_content(prompt)
    return response.text.strip()

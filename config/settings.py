# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")

# AI Model Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")

# Workflow Configuration - User sets based on risk tolerance
def _validated_threshold():
    """Read the match threshold from .env. Bad input falls back to 80."""
    try:
        value = int(os.getenv("MIN_MATCH_THRESHOLD", "80"))
    except (TypeError, ValueError):
        return 80
    return max(50, min(95, value))

MIN_MATCH_THRESHOLD = _validated_threshold()  # Default 80%

# Paths
DB_PATH = Path("database/applications.db")
OUTPUT_PATH = Path("output")

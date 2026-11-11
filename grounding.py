# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""Light grounding check for Threshold.

Keeps free text tailoring. Extracts structured facts from the source
resume only, then compares the tailored output against those facts
with code, no AI call.

A flag is a warning, not a block and not a pass. The user decides.
See docs in the spec file for the full design and the known gaps.
"""

import re

NUMBER_WORDS = {
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "eleven": 11,
    "twelve": 12,
    "thirteen": 13,
    "fourteen": 14,
    "fifteen": 15,
    "sixteen": 16,
    "seventeen": 17,
    "eighteen": 18,
    "nineteen": 19,
    "twenty": 20,
}

# Synonym list. Decided 2026-11-11: starts empty.
# Add only from real false positives, one at a time, each with a test.
SYNONYMS = {}

_YEAR_RE = re.compile(r"\b(?:19|20)\d{2}\b")
_RANGE_RE = re.compile(
    r"\b((?:19|20)\d{2})\s*(?:to|-|-)\s*((?:19|20)\d{2}|Present|present)\b"
)
_NUMBER_RE = re.compile(r"\b\d+(?:,\d{3})*(?:\.\d+)?\b")
_PHONE_RE = re.compile(r"\(?\d{3}\)?[-. ]\d{3}[-. ]\d{4}")


def _norm(text):
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def _norm_number(value):
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return value


def _numbers_from_text(text):
    found = set()
    for match in _NUMBER_RE.finditer(text):
        raw = match.group(0).replace(",", "")
        try:
            value = float(raw)
        except ValueError:
            continue
        # Skip four digit years here, dates are checked separately.
        if 1900 <= value <= 2099 and "." not in raw and len(raw) == 4:
            continue
        found.add(_norm_number(value))
    for word, value in NUMBER_WORDS.items():
        if re.search(r"\b" + word + r"\b", text, re.IGNORECASE):
            found.add(value)
    return found


def _years_from_text(text):
    years = set()
    for match in _YEAR_RE.finditer(text):
        years.add(int(match.group(0)))
    return years


def _ranges_from_text(text):
    ranges = []
    durations = set()
    for match in _RANGE_RE.finditer(text):
        try:
            start = int(match.group(1))
        except ValueError:
            continue
        end_raw = match.group(2)
        if end_raw.lower() == "present":
            continue
        try:
            end = int(end_raw)
        except ValueError:
            continue
        if end > start:
            ranges.append([start, end])
            durations.add(end - start)
    return ranges, durations


def _employers_from_text(text):
    employers = []
    seen = set()
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        candidate = None
        # Job header form: ### Role | Company
        if stripped.startswith("### "):
            body = stripped[4:].strip()
            if "|" in body:
                candidate = body.rsplit("|", 1)[-1].strip()
        elif "|" in stripped:
            # Plain text job header: Role | Company
            parts = [p.strip() for p in stripped.split("|")]
            if len(parts) >= 2:
                last = parts[-1]
                # Only take it when the line also looks like a job line,
                # not a contact line with pipes.
                if "@" not in last and not _PHONE_RE.search(last):
                    candidate = last
        elif " at " in stripped:
            after = stripped.split(" at ", 1)[-1].strip()
            after = re.split(r"[,(\n]", after)[0].strip()
            if after:
                candidate = after
        if candidate:
            candidate = candidate.strip("* ").strip()
            candidate = re.sub(r"\s+", " ", candidate)
            if len(candidate) < 2:
                continue
            if candidate.lower() in ("present", "unknown"):
                continue
            key = candidate.lower()
            if key not in seen:
                seen.add(key)
                employers.append(candidate)
    return employers


def _skills_from_text(text):
    lines = text.splitlines()
    in_skills = False
    collected = []
    for line in lines:
        stripped = line.strip()
        lowered = _norm(stripped)
        if lowered in ("skills", "technical skills", "core skills", "key skills"):
            in_skills = True
            continue
        # Inline form: Skills: Python, JavaScript, ...
        low = stripped.lower()
        if low.startswith("skills:") or low.startswith("technical skills:"):
            in_skills = True
            after = stripped.split(":", 1)[-1].strip()
            if after:
                collected.append(after)
            continue
        if stripped.startswith("## "):
            if in_skills:
                break
            continue
        if in_skills:
            if not stripped:
                continue
            # Stop at a new section header in plain text.
            if lowered in ("experience", "professional experience", "education", "certifications"):
                break
            if low.startswith("experience:") or low.startswith("professional experience:") or low.startswith("education:") or low.startswith("certifications:"):
                break
            collected.append(stripped)
    if not collected:
        return []
    skills = []
    seen = set()
    joined = " ".join(collected)
    # Split on commas, semicolons, bullets, and newlines.
    for part in re.split(r"[,;•\n]+", joined):
        token = part.strip().strip("* ").strip()
        token = re.sub(r"\s+", " ", token)
        if not token or len(token) > 60:
            continue
        key = token.lower()
        if key not in seen:
            seen.add(key)
            skills.append(token)
    return skills


def extract_source_facts(resume_text):
    """Extract checkable facts from the source resume text.

    Returns a dict with employers, dates, date_ranges, durations,
    numbers, and skills. All extraction is deterministic, no AI call.
    """
    if not resume_text:
        return {
            "employers": [],
            "dates": [],
            "date_ranges": [],
            "durations": [],
            "numbers": [],
            "skills": [],
        }
    years = _years_from_text(resume_text)
    ranges, durations = _ranges_from_text(resume_text)
    # Expand ranges into years, so a year inside a range is allowed.
    for start, end in ranges:
        for year in range(start, end + 1):
            years.add(year)
    numbers = _numbers_from_text(resume_text)
    # Durations are allowed numbers too, for example 7 from 2018 to 2025.
    numbers = set(numbers) | set(durations)
    return {
        "employers": _employers_from_text(resume_text),
        "dates": sorted(years),
        "date_ranges": ranges,
        "durations": sorted(durations),
        "numbers": sorted(numbers, key=lambda v: (isinstance(v, float), v)),
        "skills": _skills_from_text(resume_text),
    }


def _header_lines(text):
    """Return the set of line indexes for the first three non-empty lines."""
    indexes = set()
    count = 0
    for idx, line in enumerate(text.splitlines()):
        if line.strip():
            indexes.add(idx)
            count += 1
            if count >= 3:
                break
    return indexes


def _body_lines(text):
    """Lines to check, skipping the name, tagline, and contact header."""
    header = _header_lines(text)
    out = []
    for idx, line in enumerate(text.splitlines()):
        if idx in header:
            continue
        if "@" in line and _PHONE_RE.search(line):
            continue
        if line.strip().lower().startswith("contact"):
            continue
        out.append((idx, line))
    return out


def _flag(kind, value, where, line, source_note):
    return {
        "kind": kind,
        "value": str(value),
        "where": where,
        "line": line.strip()[:120],
        "source_note": source_note,
    }


def check_grounding(source_facts, tailored_resume_text, cover_letter_text=None,
                    target_company=None, target_job_title=None):
    """Compare tailored output against source facts.

    Returns {"flags": [...], "clean": bool}. Empty tailored output
    returns clean False with an error key, not a pass.
    """
    if not tailored_resume_text or not tailored_resume_text.strip():
        return {"flags": [], "clean": False, "error": "empty tailored output"}
    flags = []
    seen_flags = set()

    def add_flag(kind, value, where, line, source_note):
        key = (kind, str(value).lower(), where)
        if key in seen_flags:
            return
        seen_flags.add(key)
        flags.append(_flag(kind, value, where, line, source_note))

    source_years = set(source_facts.get("dates", []))
    source_numbers = set(source_facts.get("numbers", []))
    source_durations = set(source_facts.get("durations", []))
    allowed_numbers = source_numbers | source_durations
    source_employers = source_facts.get("employers", [])
    source_employers_norm = {_norm(e): e for e in source_employers}
    source_skills = source_facts.get("skills", [])
    source_skills_norm = {_norm(s): s for s in source_skills}

    allowed_employers = set()
    if target_company:
        allowed_employers.add(_norm(target_company))

    texts = [("resume", tailored_resume_text)]
    if cover_letter_text:
        texts.append(("cover_letter", cover_letter_text))

    for where, text in texts:
        # Employers: job headers in the form ### Role | Company.
        for _, line in _body_lines(text):
            stripped = line.strip()
            candidate = None
            if stripped.startswith("### "):
                body = stripped[4:].strip()
                if "|" in body:
                    candidate = body.rsplit("|", 1)[-1].strip()
            if candidate:
                norm = _norm(candidate)
                if norm in allowed_employers:
                    continue
                if source_employers and norm not in source_employers_norm:
                    note = "source employers: " + ", ".join(source_employers)
                    add_flag("employer", candidate, where, line, note)
            # Dates and numbers, line by line, skipping headers.
            # Years first, so a year is not also counted as a number.
            for year_match in _YEAR_RE.finditer(line):
                year = int(year_match.group(0))
                if source_years and year not in source_years:
                    note = "source years: " + ", ".join(str(y) for y in sorted(source_years))
                    add_flag("date", year, where, line, note)
            if _PHONE_RE.search(line) or "@" in line:
                continue
            for number in _numbers_from_text(line):
                # Years were already checked above.
                if isinstance(number, int) and 1900 <= number <= 2099:
                    continue
                if number not in allowed_numbers:
                    note = "source numbers: " + ", ".join(str(n) for n in sorted(allowed_numbers, key=lambda v: (isinstance(v, float), v)))
                    add_flag("number", number, where, line, note)

    # Skills: only the Skills section of the tailored resume, v1.
    # Checking every word in every bullet would flag too much.
    if source_skills:
        tailored_skills = _skills_from_text(tailored_resume_text)
        for skill in tailored_skills:
            norm = _norm(skill)
            # Allow a trailing generic word when the base skill matches.
            base = norm.split(" ")[0] if norm else norm
            if norm in source_skills_norm or base in source_skills_norm:
                continue
            if norm in SYNONYMS:
                continue
            note = "source skills: " + ", ".join(source_skills)
            # Find the line for context, fall back to the skill itself.
            add_flag("skill", skill, "resume", skill, note)

    return {"flags": flags, "clean": len(flags) == 0}

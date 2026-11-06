# Match Analysis Evaluation Results

**Date:** 2026-11-05
**Model:** gemini-3.8-flash (temperature 0.1)
**Function under test:** `analyze_match` in `AI/match_analyzer.py`
**Cases:** 1 (first eval; single sample, not a benchmark)

## Why this model

The model pin is gemini-3.8-flash, the current generally-available flash
model on the free tier, set centrally in `config/settings.py` as
`GEMINI_MODEL`. The prompt template, verdict definitions, evidence rules,
and grounding instruction are the repo's own, unchanged.

## How the test was run

The Gemini free-tier API was down with 503 errors from 2026-11-04 until the
evening of 2026-11-05. A scheduled watch confirmed it responding again on
2026-11-05, and this eval ran immediately after recovery.

The API key is vault-backed and cannot be placed in an environment variable,
so `analyze_match` could not be imported and called directly in this run.
Instead the test sent the function's exact prompt, word for word, through
the vault-backed helper with the same model and the same resume summary and
job description below. The response parsing is the same as the function's:
strip markdown fences, then `json.loads`. The only untested part of the
function is its own import and key-loading path, which is unchanged code
that previously ran locally.

## What was tested

Resume summary (condensed from the master resume):

> WILLIAM RYAN MICOU, Technical Operations Leader, 20+ years. Built
> Document360 knowledge base cutting dealer questions from 100 to 65/day.
> Created MillBox 101 training cutting ramp-up from 1 month to 2 weeks.
> Certifications: ISO/IEC 42001 AI Management Systems Fundamentals, AWS
> Cloud Practitioner, CompTIA A+.

Sample job description:

> Senior Manager, Technical Operations (remote). 10+ years leading support
> operations. Own knowledge management strategy. Documentation platforms
> (Document360/Confluence) preferred. AI governance familiarity a plus.

## Summary

| Metric | Result |
|---|---|
| Cases evaluated | 1 of 1 |
| Valid JSON returned | yes |
| overall_score | 95 |
| verdict | STRONG |
| Evidence items | 3 |
| Gaps reported | 0 |
| Threshold gate (default 80) | PASS (95 >= 80) |

## Returned result (verbatim)

```json
{
    "overall_score": 95,
    "verdict": "STRONG",
    "evidence": [
        "Resume cites 20+ years as a Technical Operations Leader; job description requires 10+ years leading support operations.",
        "Resume states candidate built a Document360 knowledge base reducing dealer questions from 100 to 65/day; job description requires owning knowledge management strategy and lists Document360 as a preferred platform.",
        "Resume includes ISO/IEC 42001 AI Management Systems Fundamentals certification; job description states AI governance familiarity is a plus."
    ],
    "gaps": []
}
```

## Findings

**The JSON contract held.** The response parsed as JSON on the first try
with all four required keys: `overall_score` (integer, 0-100), `verdict`
(one of STRONG/MODERATE/WEAK), `evidence` (list), `gaps` (list). No
markdown fences to strip in this run.

**The verdict is defensible.** A 95/STRONG verdict on this pairing is a fair
read: the resume exceeds the 10+ years requirement, the Document360 work is
a direct hit on the knowledge management ask, and the ISO/IEC 42001
certification matches the AI governance plus. Nothing in the verdict depends
on a fact the resume does not state.

**Grounding held.** Each evidence item cites a specific fact from the resume
summary and the specific job requirement it matches, exactly as the prompt
requires. No invented qualifications appeared: no Confluence experience was
claimed (the posting lists it only as preferred), no degree was claimed, and
no management headcount was invented. The empty gaps list is correct for
this sample: every stated requirement is covered by a stated fact.

**The threshold gate passed.** CareerForge's default match threshold is 80
(configurable 50 to 95). A score of 95 clears it, so this pairing would
proceed to tailoring.

## Limitations

- One sample only. This proves the function works end to end on a strong
  match; it says nothing about scoring calibration on borderline or weak
  matches, where the verdict boundary matters most.
- The resume input was a condensed summary, not the full two-page resume.
  A full-resume run may surface more evidence and more gaps.
- The test ran through the vault-backed helper with the function's exact
  prompt, not by importing `analyze_match` directly, because the raw API
  key cannot be placed in an environment variable. The function's own
  import and key-loading path was not exercised in this run.
- Ground-truth judgment (that STRONG is the right verdict) is the author's
  read of the same facts, not an independent labeler's.
- Results reflect gemini-3.8-flash, not the retired gemini-2.5-flash.
- A single strong-match case cannot test the WEAK path or the
  below-threshold refusal. The next eval should use a borderline posting
  and a clear mismatch to check both.

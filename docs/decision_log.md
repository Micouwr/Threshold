# Decision Log (spec)

Status: spec only, not built. Roadmap item 10. Build after the Gemini API is back, the integration test passes, and roadmap items 1 and 2 are done. Needs live API testing.

## Why

Threshold can refuse to tailor, but a refusal leaves no trace. Nothing records gate decisions today, so the tool cannot honestly claim decision logging, traceability, or auditability. This log is what makes those words true.

## What it records

One record per gate decision, including refusals:

- Timestamp
- Job title and company
- Resume used (file path, not contents)
- Match score and verdict (STRONG, MODERATE, or WEAK)
- Threshold in force at the time
- Decision: tailoring allowed or refused
- For allowed runs, the output file paths

## What it does not record

No resume text. No job description text. No match summary text. Scores, verdicts, and paths only. A log that leaks personal data would repeat the mistake Vigil's error log had.

## Format

JSONL, one record per line, append-only. Same shape as Vigil's fallback log: human-readable, easy to inspect, easy to count.

## Where it hooks in

- When a match analysis completes: record the score, verdict, threshold, and decision.
- When tailoring starts: record the output paths against the same decision.

## What already exists

The applications table already stores each tailored application with its job, resume path, and match score. The log complements it: it covers refusals, which the table never sees, and it records the verdict and the threshold in force, which the table does not store.

## What it enables

- Traceability: every tailored output links back to the decision that produced it.
- Auditability: a complete record of gate decisions, including refusals.
- The README may claim decision logging, traceability, and auditability only after this ships.

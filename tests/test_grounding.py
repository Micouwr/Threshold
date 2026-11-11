#!/usr/bin/env python3
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""Grounding check tests. Offline, no live API calls, fixed strings only."""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from grounding import extract_source_facts, check_grounding


def _kinds(result):
    return sorted(f["kind"] for f in result["flags"])


def test_clean_pass_reworded():
    source = """Senior Software Engineer with 5 years experience.
Skills: Python, JavaScript, React, Node.js, AWS.
Experience: Led team of 5 engineers, delivered 3 production systems.
Education: BS Computer Science, MIT."""
    facts = extract_source_facts(source)
    tailored = """JOHN DOE
SENIOR SOFTWARE ENGINEER
Louisville, KY | 555-0100 | john@example.com
## PROFESSIONAL SUMMARY
Managed five engineers and delivered 3 production systems.
## SKILLS
Python, JavaScript, React, Node.js, AWS"""
    result = check_grounding(facts, tailored, target_company="Test Corp")
    assert result["clean"], result["flags"]
    assert result["flags"] == []


def test_invented_employer():
    source = """WILLIAM RYAN MICOU
TECHNICAL OPERATIONS LEADER
## EXPERIENCE
### Technical Operations Leader | CIMSystem
*Louisville, KY | 2018 to 2025*
- Built a Document360 knowledge base.
### Enterprise Support Analyst | CompuCom
*Louisville, KY | 2013 to 2017*
- Supported enterprise clients."""
    facts = extract_source_facts(source)
    assert "CIMSystem" in facts["employers"]
    assert "CompuCom" in facts["employers"]
    tailored = """WILLIAM RYAN MICOU
TECHNICAL OPERATIONS LEADER
Louisville, KY | 555-0100 | ryan@example.com
## EXPERIENCE
### Engineer | TechCorp Inc.
*Louisville, KY | 2018 to 2025*
- Built a knowledge base."""
    result = check_grounding(facts, tailored, target_company="Test Corp")
    assert not result["clean"]
    assert "employer" in _kinds(result)
    assert any(f["value"] == "TechCorp Inc." for f in result["flags"])


def test_invented_year():
    source = """WILLIAM RYAN MICOU
TECHNICAL OPERATIONS LEADER
## EXPERIENCE
### Technical Operations Leader | CIMSystem
*Louisville, KY | 2018 to 2025*
- Built a Document360 knowledge base."""
    facts = extract_source_facts(source)
    tailored = """WILLIAM RYAN MICOU
TECHNICAL OPERATIONS LEADER
Louisville, KY | 555-0100 | ryan@example.com
## EXPERIENCE
### Technical Operations Leader | CIMSystem
*Louisville, KY | 2015 to 2017*
- Built a Document360 knowledge base."""
    result = check_grounding(facts, tailored, target_company="Test Corp")
    assert not result["clean"]
    assert "date" in _kinds(result)


def test_invented_number():
    source = "Senior Software Engineer with 5 years experience. Led team of 5 engineers, delivered 3 production systems."
    facts = extract_source_facts(source)
    tailored = """JOHN DOE
SENIOR SOFTWARE ENGINEER
Louisville, KY | 555-0100 | john@example.com
## PROFESSIONAL SUMMARY
Led team of 12 engineers and delivered 3 production systems."""
    result = check_grounding(facts, tailored, target_company="Test Corp")
    assert not result["clean"]
    assert "number" in _kinds(result)
    assert any(f["value"] == "12" for f in result["flags"])


def test_invented_skill():
    source = """Senior Software Engineer with 5 years experience.
Skills: Python, JavaScript, React, Node.js, AWS.
Experience: Led team of 5 engineers, delivered 3 production systems."""
    facts = extract_source_facts(source)
    tailored = """JOHN DOE
SENIOR SOFTWARE ENGINEER
Louisville, KY | 555-0100 | john@example.com
## SKILLS
Python, JavaScript, React, Node.js, AWS, Go"""
    result = check_grounding(facts, tailored, target_company="Test Corp")
    assert not result["clean"]
    assert "skill" in _kinds(result)
    assert any(f["value"] == "Go" for f in result["flags"])


def test_target_role_not_flagged():
    source = """Senior Software Engineer with 5 years experience.
Skills: Python, JavaScript, React, Node.js, AWS.
Experience: Led team of 5 engineers, delivered 3 production systems."""
    facts = extract_source_facts(source)
    tailored = """JOHN DOE
FULL STACK DEVELOPER
Louisville, KY | 555-0100 | john@example.com
## PROFESSIONAL SUMMARY
Led team of 5 engineers and delivered 3 production systems.
## SKILLS
Python, JavaScript, React, Node.js, AWS"""
    cover = "I am applying for the Full Stack Developer role at Test Corp."
    result = check_grounding(
        facts, tailored, cover,
        target_company="Test Corp", target_job_title="Full Stack Developer",
    )
    assert result["clean"], result["flags"]


def test_contact_info_not_flagged():
    source = "Senior Software Engineer with 5 years experience. Skills: Python, JavaScript."
    facts = extract_source_facts(source)
    tailored = """JOHN DOE
SENIOR SOFTWARE ENGINEER
Louisville, KY | (502) 555-0100 | john@example.com | linkedin.com/in/johndoe
## PROFESSIONAL SUMMARY
Led team of 5 engineers."""
    result = check_grounding(facts, tailored, target_company="Test Corp")
    assert result["clean"], result["flags"]


def test_derived_duration_allowed():
    source = """WILLIAM RYAN MICOU
TECHNICAL OPERATIONS LEADER
## EXPERIENCE
### Technical Operations Leader | CIMSystem
*Louisville, KY | 2018 to 2025*
- Built a Document360 knowledge base."""
    facts = extract_source_facts(source)
    assert 7 in facts["durations"]
    tailored = """WILLIAM RYAN MICOU
TECHNICAL OPERATIONS LEADER
Louisville, KY | 555-0100 | ryan@example.com
## PROFESSIONAL SUMMARY
7 years leading technical operations."""
    result = check_grounding(facts, tailored, target_company="Test Corp")
    assert result["clean"], result["flags"]


def test_derived_duration_not_allowed():
    source = """WILLIAM RYAN MICOU
TECHNICAL OPERATIONS LEADER
## EXPERIENCE
### Technical Operations Leader | CIMSystem
*Louisville, KY | 2018 to 2025*
- Built a Document360 knowledge base."""
    facts = extract_source_facts(source)
    tailored = """WILLIAM RYAN MICOU
TECHNICAL OPERATIONS LEADER
Louisville, KY | 555-0100 | ryan@example.com
## PROFESSIONAL SUMMARY
10 years leading technical operations."""
    result = check_grounding(facts, tailored, target_company="Test Corp")
    assert not result["clean"]
    assert "number" in _kinds(result)


def test_empty_output():
    source = "Senior Software Engineer with 5 years experience."
    facts = extract_source_facts(source)
    result = check_grounding(facts, "")
    assert result["clean"] is False
    assert result["flags"] == []
    assert "error" in result

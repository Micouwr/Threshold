import os
import google.generativeai as genai
import json
from pathlib import Path
from dotenv import load_dotenv

# Load environment from project root
load_dotenv(dotenv_path=Path(__file__).parent.parent / '.env')

# Central model pin; falls back to env/default when run standalone
try:
    from config.settings import GEMINI_MODEL
except ImportError:
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")

DIAGNOSTIC_MODE = False

def analyze_match(resume_text: str, job_description: str) -> dict:
    """Core AI function: Compare resume to job description and return match analysis."""
    # Diagnostic mode disabled for production
    
    # Verify API key
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key == "your_api_key_here":
        raise Exception("GEMINI_API_KEY not configured")
    
    # Configure Gemini
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(GEMINI_MODEL)
    except Exception:
        raise
    
    # Build analysis prompt
    prompt = f"""
    Analyze this resume against the job description and provide a match analysis.
    Return ONLY a valid JSON object with these exact keys: overall_score, verdict, evidence, gaps.

    - overall_score: integer 0-100, your assessment of how well the resume matches the job.
    - verdict: one of "STRONG", "MODERATE", "WEAK".
      STRONG = the resume clearly covers the core requirements.
      MODERATE = plausible fit but with notable gaps.
      WEAK = significant gaps against core requirements.
    - evidence: array of 3-4 strings. Each must cite a SPECIFIC fact from the resume
      AND the SPECIFIC job requirement it matches. Base everything SOLELY on what the
      resume states. Do not infer, assume, or invent qualifications not present in the resume.
      If the resume does not state something, treat it as absent.
    - gaps: array of strings. Each names a job requirement the resume does not clearly
      cover, stated plainly. If there are no meaningful gaps, return an empty array.

    Example format:
    {{
        "overall_score": 85,
        "verdict": "STRONG",
        "evidence": [
            "Resume shows 20+ years in technical operations leadership; posting requires 10+ years leading support operations",
            "Resume lists Document360 knowledge base build cutting dealer questions from 100 to 65/day; posting asks for experience improving support processes with measurable results",
            "Resume includes ISO/IEC 42001 AI governance fundamentals certification; posting prefers AI governance knowledge"
        ],
        "gaps": [
            "Posting requires AWS Solutions Architect certification; resume lists AWS Cloud Practitioner Essentials only"
        ]
    }}

    RESUME:
    {resume_text}

    JOB DESCRIPTION:
    {job_description}
    """
    
    # Call Gemini API
    try:
        response = model.generate_content(prompt)
        
        # Parse JSON response (strip markdown if present)
        try:
            response_text = response.text.strip()
            
            # Remove markdown code block markers
            if response_text.startswith("```json"):
                response_text = response_text[7:]  # Remove ```json
            if response_text.startswith("```"):
                response_text = response_text[3:]  # Remove ```
            if response_text.endswith("```"):
                response_text = response_text[:-3]  # Remove ```
            
            response_text = response_text.strip()
            
            result = json.loads(response_text)
            return result
        except json.JSONDecodeError as e:
            raise Exception(f"Failed to parse AI response as JSON: {e}")
    
    except Exception:
        raise

def extract_job_details(job_description: str) -> dict:
    """Extract job title and company name from job description using AI."""
    # Verify API key
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key == "your_api_key_here":
        raise Exception("GEMINI_API_KEY not configured")
    
    # Configure Gemini
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(GEMINI_MODEL)
    except Exception:
        raise
    
    # Build extraction prompt
    prompt = f"""
    Extract the job title and company name from this job description.
    Return ONLY a valid JSON object with these exact keys: job_title, company_name
    
    If you cannot determine either value, use "Unknown" as the value.
    
    Example format:
    {{
        "job_title": "Software Engineer",
        "company_name": "Tech Corp"
    }}
    
    JOB DESCRIPTION:
    {job_description}
    """
    
    # Call Gemini API
    try:
        response = model.generate_content(prompt)
        
        # Parse JSON response (strip markdown if present)
        try:
            response_text = response.text.strip()
            
            # Remove markdown code block markers
            if response_text.startswith("```json"):
                response_text = response_text[7:]  # Remove ```json
            if response_text.startswith("```"):
                response_text = response_text[3:]  # Remove ```
            if response_text.endswith("```"):
                response_text = response_text[:-3]  # Remove ```
            
            response_text = response_text.strip()
            
            result = json.loads(response_text)
            return result
        except json.JSONDecodeError:
            # If JSON parsing fails, return defaults
            return {
                "job_title": "Unknown",
                "company_name": "Unknown"
            }
    
    except Exception:
        # If API call fails, return defaults
        return {
            "job_title": "Unknown",
            "company_name": "Unknown"
        }

# Self-test when module is run directly
if __name__ == "__main__":
    if DIAGNOSTIC_MODE:
        print("[DIAGNOSTIC] Running self-test...")
    
    # Built-in test data (no separate files)
    test_resume = """
    John Doe
    AI Developer & Automation Specialist
    Louisville, KY
    
    Professional Summary:
    5 years experience building AI-powered applications using Python, GPT APIs, and PyInstaller.
    
    Technical Skills:
    Python, JavaScript, SQL, Google Generative AI, PyInstaller, SQLite, REST APIs
    
    Experience:
    Senior AI Developer at Tech Innovations Inc. (2022-Present)
    - Developed AI-powered resume tailoring system using GPT-4 API
    - Implemented cross-platform desktop applications for 500+ users
    - Built automated job application bot using Gemini API
    
    Certifications:
    - Two AI certifications (Google, AWS)
    """
    
    test_job = """
    AI Learning Design Lead
    Healthcare Company
    
    Responsibilities:
    Design, develop, and deliver strategic learning experiences supporting AI initiatives.
    Analyze content, write storyboards, partner with subject matter experts.
    
    Requirements:
    - 5+ years experience in AI/ML development
    - Python, JavaScript, SQL proficiency
    - Experience with GPT APIs and PyInstaller
    - Strong consultative and project management skills
    """
    
    try:
        if DIAGNOSTIC_MODE:
            print("[DIAGNOSTIC] Testing AI match analysis...")
        result = analyze_match(test_resume, test_job)

        if DIAGNOSTIC_MODE:
            print("\n[DIAGNOSTIC] Test completed successfully!")
            print(f"Overall Match Score: {result.get('overall_score', 'N/A')}%")
            print(f"Verdict: {result.get('verdict', 'N/A')}")
            print(f"\nEvidence: {result.get('evidence', [])}")
            print(f"Gaps: {result.get('gaps', [])}")
        
    except Exception as e:
        if DIAGNOSTIC_MODE:
            print(f"\n[DIAGNOSTIC] Test FAILED: {e}")
        raise

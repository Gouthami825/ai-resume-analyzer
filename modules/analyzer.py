"""
Compare resume text to a job description using local keyword / fuzzy matching.

No external AI APIs — suitable for learning and offline use.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from rapidfuzz import fuzz

from modules.skills_data import canonical_display, find_canonical_skills_in_text


@dataclass
class AnalysisResult:
    """Structured output for the Streamlit UI."""

    match_score: float
    score_explanation: str
    matching_skills: list[str] = field(default_factory=list)
    missing_skills: list[str] = field(default_factory=list)
    resume_only_skills: list[str] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)
    job_skills_found: list[str] = field(default_factory=list)
    resume_word_count: int = 0


def normalize_text(text: str) -> str:
    """Lowercase and collapse whitespace for matching."""
    text = text.lower()
    text = re.sub(r"[\u2018\u2019]", "'", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def find_skills_in_text(text: str) -> set[str]:
    """Find canonical technical skill ids in text (curated dictionary only)."""
    return find_canonical_skills_in_text(text)


def _display_names(canonical_ids: set[str]) -> list[str]:
    """Convert canonical ids to sorted display names."""
    return sorted({canonical_display(cid) for cid in canonical_ids}, key=str.lower)


def compute_match_score(
    job_skills: set[str],
    resume_skills: set[str],
    job_text: str,
    resume_text: str,
) -> tuple[float, str]:
    """
    Score from 0–100 based on unique technical skill coverage and light text similarity.

    Primary weight: fraction of job skills found in resume (canonical ids, no duplicates).
    Secondary: partial fuzzy overlap of normalized texts (capped contribution).
    """
    if not job_text.strip():
        return 0.0, "Add a job description to calculate a match score."

    if not resume_text.strip():
        return 0.0, "Upload a resume with extractable text to calculate a match score."

    if not job_skills:
        similarity = fuzz.token_set_ratio(
            normalize_text(resume_text), normalize_text(job_text)
        )
        explanation = (
            "No technical skills from our curated dictionary were found in the job description. "
            f"Overall text similarity is {similarity:.0f}% (wording overlap only). "
            "Paste requirements that mention tools, languages, or frameworks for a skill-based score."
        )
        return float(similarity), explanation

    matched = job_skills & resume_skills
    coverage = len(matched) / len(job_skills)
    skill_component = coverage * 85.0

    similarity = fuzz.token_set_ratio(
        normalize_text(resume_text), normalize_text(job_text)
    )
    text_component = min(similarity * 0.15, 15.0)

    score = round(min(skill_component + text_component, 100.0), 1)

    pct_skills = coverage * 100
    explanation = (
        f"Your resume matches {len(matched)} of {len(job_skills)} unique technical skills "
        f"detected in the job description ({pct_skills:.0f}% skill coverage). "
        f"A small bonus (up to 15 points) reflects general wording overlap "
        f"({similarity:.0f}% text similarity). "
    )
    if score >= 75:
        explanation += "Strong alignment — polish bullets with metrics and role-specific keywords."
    elif score >= 50:
        explanation += "Moderate alignment — add missing skills where you have real experience."
    else:
        explanation += "Low alignment — tailor the resume to this role or verify it's the right fit."

    return score, explanation


def build_suggestions(
    missing: set[str],
    resume_text: str,
    job_text: str,
    score: float,
) -> list[str]:
    """Rule-based improvement tips (beginner-friendly, no LLM)."""
    tips: list[str] = []
    resume_norm = normalize_text(resume_text)

    if missing:
        top_missing = _display_names(missing)[:8]
        tips.append(
            "Technical skills in the job description not clearly found on your resume: "
            + ", ".join(top_missing)
            + ". If you have experience with any of these, add them to a Skills section "
            "and mention them in relevant project or work bullets."
        )

    if "experience" not in resume_norm and "work" not in resume_norm:
        tips.append(
            "Consider a clear Work Experience or Projects section with company names, "
            "dates, and bullet points starting with action verbs."
        )

    if resume_norm.count("•") + resume_norm.count("- ") < 3:
        tips.append(
            "Use more bullet points with measurable outcomes (e.g., 'Reduced load time by 30%')."
        )

    if len(resume_text.split()) < 200:
        tips.append(
            "Your extracted resume text is quite short. Ensure the file is not a scanned "
            "image PDF, and include enough detail for recruiters to assess fit."
        )

    if score < 60 and job_text:
        tips.append(
            "Mirror important phrases from the job description naturally in your summary "
            "and experience sections — avoid keyword stuffing."
        )

    if not tips:
        tips.append(
            "Good skill overlap! Proofread for typos, keep formatting ATS-friendly, "
            "and tailor your summary to this role."
        )

    return tips


def analyze_resume_vs_job(resume_text: str, job_description: str) -> AnalysisResult:
    """
    Compare resume to job description and return match details.

    Raises:
        ValueError: If inputs are invalid (handled at app layer).
    """
    resume_text = (resume_text or "").strip()
    job_description = (job_description or "").strip()

    if not resume_text:
        raise ValueError("Resume text is empty. Upload a valid PDF or DOCX file.")
    if not job_description:
        raise ValueError("Job description is empty. Paste the full job posting text.")
    if len(job_description) < 30:
        raise ValueError(
            "Job description looks too short. Paste the full requirements section."
        )

    resume_skills = find_skills_in_text(resume_text)
    job_skills = find_skills_in_text(job_description)

    matched = job_skills & resume_skills
    missing = job_skills - resume_skills
    resume_only = resume_skills - job_skills

    score, explanation = compute_match_score(
        job_skills, resume_skills, job_description, resume_text
    )
    suggestions = build_suggestions(missing, resume_text, job_description, score)

    return AnalysisResult(
        match_score=score,
        score_explanation=explanation,
        matching_skills=_display_names(matched),
        missing_skills=_display_names(missing),
        resume_only_skills=_display_names(resume_only),
        suggestions=suggestions,
        job_skills_found=_display_names(job_skills),
        resume_word_count=len(resume_text.split()),
    )

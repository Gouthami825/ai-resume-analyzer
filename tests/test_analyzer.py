"""Unit tests for skill extraction, aliases, and match scoring."""

from __future__ import annotations

import pytest

from modules.analyzer import analyze_resume_vs_job, compute_match_score, find_skills_in_text
from modules.skills_data import canonical_display, find_canonical_skills_in_text


class TestAliases:
    def test_git_and_github_same_canonical(self) -> None:
        assert find_canonical_skills_in_text("Experienced with Git version control") == {"git"}
        assert find_canonical_skills_in_text("Active on GitHub for open source") == {"git"}

    def test_rest_rest_api_api_apis_merge(self) -> None:
        jd = "Build REST APIs and RESTful services"
        skills = find_canonical_skills_in_text(jd)
        assert skills == {"rest_api"}

    def test_llm_variants(self) -> None:
        assert find_canonical_skills_in_text("Fine-tune LLMs for production") == {"llm"}
        assert find_canonical_skills_in_text("Work with LLM pipelines") == {"llm"}

    def test_ml_ai_slash_alias(self) -> None:
        skills = find_canonical_skills_in_text("AI/ML engineer with machine learning background")
        assert skills == {"machine_learning"}

    def test_named_library_aliases(self) -> None:
        text = (
            "Python, FastAPI, Streamlit, Pandas, NumPy, PyTorch, TensorFlow, "
            "Scikit-learn, NLP, SQL"
        )
        found = find_canonical_skills_in_text(text)
        expected = {
            "python",
            "fastapi",
            "streamlit",
            "pandas",
            "numpy",
            "pytorch",
            "tensorflow",
            "scikit_learn",
            "nlp",
            "sql",
        }
        assert found == expected

    def test_display_labels(self) -> None:
        assert canonical_display("git") == "Git/GitHub"
        assert canonical_display("rest_api") == "REST API"
        assert canonical_display("llm") == "LLMs"
        assert canonical_display("scikit_learn") == "Scikit-learn"


class TestFalsePositives:
    def test_generic_job_buzzwords_not_skills(self) -> None:
        jd = """
        Build scalable products. Developer role in Hyderabad.
        Education: Bachelor's. Experience required. Responsibilities include
        teamwork. Computer science background. Learning mindset. Work with stakeholders.
        """
        assert find_canonical_skills_in_text(jd) == set()

    def test_learning_alone_not_deep_learning(self) -> None:
        assert "deep_learning" not in find_canonical_skills_in_text(
            "Continuous learning culture"
        )

    def test_java_in_javascript_not_double_java_only(self) -> None:
        skills = find_canonical_skills_in_text("Proficient in JavaScript")
        assert "java" not in skills
        assert skills == {"javascript"}


class TestScoreCalculation:
    def test_coverage_uses_unique_canonical_skills(self) -> None:
        job = {"python", "docker", "rest_api"}
        resume = {"python", "rest_api"}
        score, explanation = compute_match_score(
            job,
            resume,
            "Python REST APIs and Docker",
            "Python developer, REST API design",
        )
        assert score == pytest.approx(67.2, abs=0.2)
        assert "2 of 3 unique technical skills" in explanation

    def test_redundant_synonyms_do_not_inflate_denominator(self) -> None:
        job_text = "Python, REST API, APIs, REST, LLM, LLMs, Git, GitHub"
        resume_text = "Python, REST APIs, LLMs, GitHub"
        result = analyze_resume_vs_job(resume_text, job_text)
        assert set(result.matching_skills) == {
            "Python",
            "REST API",
            "LLMs",
            "Git/GitHub",
        }
        assert result.missing_skills == []
        assert len(result.job_skills_found) == 4
        assert result.match_score >= 85

    def test_no_dictionary_skills_falls_back_to_similarity_message(self) -> None:
        job_skills: set[str] = set()
        resume_skills = {"python"}
        _, explanation = compute_match_score(
            job_skills,
            resume_skills,
            "Generic company overview only",
            "Python",
        )
        assert "curated dictionary" in explanation

"""
AI Resume Analyzer — Streamlit entry point.

Run locally: streamlit run app.py
"""

from __future__ import annotations

import streamlit as st

from modules.analyzer import analyze_resume_vs_job
from modules.resume_parser import ResumeParseError, extract_text_from_upload

st.set_page_config(
    page_title="AI Resume Analyzer",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("📄 AI Resume Analyzer")
st.caption(
    "Upload your resume, paste a job description, and get instant skill matching — "
    "100% local, no API keys required."
)


def init_session_state() -> None:
    defaults = {
        "resume_text": "",
        "analysis_done": False,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def render_score_gauge(score: float) -> None:
    if score >= 75:
        st.success(f"**Match score: {score}%** — Strong match")
    elif score >= 50:
        st.warning(f"**Match score: {score}%** — Moderate match")
    else:
        st.error(f"**Match score: {score}%** — Needs improvement")


def main() -> None:
    init_session_state()

    with st.sidebar:
        st.header("How it works")
        st.markdown(
            """
            1. Upload a **PDF** or **DOCX** resume.
            2. Paste the **job description**.
            3. Click **Analyze match**.
            4. Review skills, gaps, and suggestions.
            """
        )
        st.divider()
        st.markdown(
            "**Note:** Skill detection uses a built-in keyword list plus text similarity. "
            "It does not replace human review or professional career advice."
        )

    col_upload, col_job = st.columns(2)

    with col_upload:
        st.subheader("1. Upload resume")
        uploaded = st.file_uploader(
            "PDF or DOCX (max 10 MB)",
            type=["pdf", "docx"],
            help="Password-protected PDFs are not supported.",
        )

        if uploaded is not None:
            try:
                file_bytes = uploaded.getvalue()
                text = extract_text_from_upload(uploaded.name, file_bytes)
                st.session_state["resume_text"] = text
                st.success(f"Extracted **{len(text.split())}** words from `{uploaded.name}`.")
                with st.expander("Preview extracted text"):
                    st.text_area(
                        "Resume text",
                        value=text[:8000],
                        height=200,
                        disabled=True,
                        label_visibility="collapsed",
                    )
            except ResumeParseError as exc:
                st.session_state["resume_text"] = ""
                st.error(str(exc))
            except Exception as exc:
                st.session_state["resume_text"] = ""
                st.error(f"Unexpected error while reading the file: {exc}")

    with col_job:
        st.subheader("2. Job description")
        job_description = st.text_area(
            "Paste the full job posting",
            height=280,
            placeholder="Paste responsibilities, requirements, and preferred qualifications here…",
        )

    analyze_clicked = st.button("🔍 Analyze match", type="primary", use_container_width=False)

    if analyze_clicked:
        st.session_state["analysis_done"] = False
        try:
            result = analyze_resume_vs_job(
                st.session_state.get("resume_text", ""),
                job_description or "",
            )
            st.session_state["last_result"] = result
            st.session_state["analysis_done"] = True
        except ValueError as exc:
            st.warning(str(exc))
        except Exception as exc:
            st.error(f"Analysis failed: {exc}")

    if st.session_state.get("analysis_done") and st.session_state.get("last_result"):
        result = st.session_state["last_result"]

        st.divider()
        st.subheader("3. Results")

        render_score_gauge(result.match_score)
        st.info(result.score_explanation)

        m1, m2, m3 = st.columns(3)
        m1.metric("Words in resume", result.resume_word_count)
        m2.metric("Skills in job description", len(result.job_skills_found))
        m3.metric("Matching skills", len(result.matching_skills))

        c1, c2 = st.columns(2)
        with c1:
            st.markdown("#### ✅ Matching skills")
            if result.matching_skills:
                for skill in result.matching_skills:
                    st.markdown(f"- {skill}")
            else:
                st.write("No overlapping skills from our keyword list yet.")

        with c2:
            st.markdown("#### ⚠️ Missing skills (in job, not in resume)")
            if result.missing_skills:
                for skill in result.missing_skills:
                    st.markdown(f"- {skill}")
            else:
                st.write("No missing catalog skills — nice work!")

        if result.resume_only_skills:
            with st.expander("Extra skills on your resume (not listed in job description)"):
                st.write(", ".join(result.resume_only_skills))

        st.markdown("#### 💡 Improvement suggestions")
        for i, tip in enumerate(result.suggestions, start=1):
            st.markdown(f"{i}. {tip}")


if __name__ == "__main__":
    main()

# AI Resume Analyzer

A **beginner-friendly** web app that compares your resume to a job description and shows:

- **Match score** (0–100) with a plain-English explanation
- **Matching skills** and **missing skills**
- **Improvement suggestions** (rule-based, no paid AI APIs)

Built with **Python** and **Streamlit**. All parsing and analysis run **locally** on your machine.

---

## Features

| Feature | Description |
|--------|-------------|
| Resume upload | PDF or DOCX (up to 10 MB) |
| Text extraction | `pypdf` for PDF, `python-docx` for Word |
| Job description | Paste any job posting text |
| Skill matching | Built-in keyword list + fuzzy text similarity (`rapidfuzz`) |
| Results | Match score, skill lists, actionable tips |

**What this app is not:** It does not call OpenAI, Claude, or other cloud LLMs. It uses keyword and similarity heuristics, which are fast and free but less nuanced than a human reviewer or a large language model.

---

## Project structure

```
03_AI_Resume_Analyzer/
├── app.py                 # Streamlit UI (start here)
├── requirements.txt       # Python dependencies
├── README.md
├── .gitignore
└── modules/
    ├── __init__.py
    ├── resume_parser.py   # PDF/DOCX → plain text
    ├── skills_data.py     # Skill keyword list & display names
    └── analyzer.py        # Compare resume vs job description
```

### Module overview

- **`resume_parser.py`** — Validates file type/size, extracts text, raises `ResumeParseError` with clear messages.
- **`skills_data.py`** — Curated skills (languages, frameworks, cloud, soft skills). Easy to extend.
- **`analyzer.py`** — Finds skills in text, computes score, builds suggestions. Returns `AnalysisResult`.
- **`app.py`** — Wires upload + text area to the modules and displays results.

---

## Prerequisites

- **Python 3.10+** (3.11 or 3.12 recommended)
- Windows, macOS, or Linux
- Internet only needed to **install** packages (running the app works offline after install)

---

## Installation

### 1. Open a terminal in this folder

```powershell
cd "c:\Users\gouth\Downloads\AI_Freelancing_Portfolio\03_AI_Resume_Analyzer"
```

### 2. Create a virtual environment (recommended)

**Windows (PowerShell):**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**macOS / Linux:**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```powershell
pip install -r requirements.txt
```

---

## Run the app

```powershell
streamlit run app.py
```

Your browser should open to `http://localhost:8501`. If it does not, copy that URL from the terminal.

### Usage steps

1. **Upload** a `.pdf` or `.docx` resume.
2. **Paste** the full job description (requirements section helps most).
3. Click **Analyze match**.
4. Read the score, skill lists, and suggestions.

---

## How the match score works

The score is designed to be easy to understand:

1. **Skill coverage (up to ~85 points)** — Among skills detected in the job description, what fraction also appear in the resume?
2. **Text similarity (up to 15 points)** — `rapidfuzz` token similarity between resume and job text (small bonus).

If no skills are detected in the job description, the app falls back to **overall text similarity** and explains that in the UI.

---

## Error handling

| Situation | What you see |
|-----------|----------------|
| Wrong file type | Message asking for PDF or DOCX |
| File too large | Over 10 MB limit |
| Encrypted PDF | Ask for an unprotected export |
| Image-only / scanned PDF | Often no extractable text; OCR is not included |
| Empty job description | Validation warning |
| Resume not uploaded | Validation warning |

---

## Customization (for learners)

### Add more skills

Edit `modules/skills_data.py` and add strings to `SKILL_KEYWORDS` (lowercase). Add aliases in `SKILL_ALIASES` if you want prettier labels.

### Tune the score

Open `modules/analyzer.py` and adjust weights in `compute_match_score()` (e.g. change `85.0` / `15.0` split).

### Change UI

Edit `app.py` — Streamlit widgets are documented at [docs.streamlit.io](https://docs.streamlit.io).

---

## Troubleshooting

**`streamlit` is not recognized**
- Activate the virtual environment and run `pip install -r requirements.txt` again.

**PDF extracts almost nothing**
- The file may be a scan (image). Re-save as a text-based PDF or use DOCX.

**Score feels too high or too low**
- Keyword matching cannot understand context. Treat the score as a **guide**, not a hiring decision.

**Module import errors when running from another directory**
- Always run `streamlit run app.py` from the project root (`03_AI_Resume_Analyzer`).

---

## Dependencies (all free)

| Package | Purpose |
|---------|---------|
| `streamlit` | Web UI |
| `pypdf` | PDF text extraction |
| `python-docx` | DOCX text extraction |
| `rapidfuzz` | Fast fuzzy string matching |

---

## License

Use and modify freely for learning, portfolio projects, and freelancing demos.

---

## Quick test without a real resume

Paste this into the job description after uploading any resume:

```text
We need a Python developer with Django or FastAPI, REST APIs, PostgreSQL,
Docker, AWS, Git, and agile teamwork. Experience with machine learning is a plus.
```

You should see skills like Python, Django, FastAPI, PostgreSQL, Docker, AWS, and Git highlighted when they appear in your resume text.

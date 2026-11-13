"""
Curated technical skills for local resume–job matching (no API required).

All detection uses this dictionary only — generic capitalized words from job
postings are never treated as skills.
"""

from __future__ import annotations

import re
from functools import lru_cache

# Canonical skill id -> display label shown in the UI
CANONICAL_DISPLAY: dict[str, str] = {
    "python": "Python",
    "java": "Java",
    "javascript": "JavaScript",
    "typescript": "TypeScript",
    "cpp": "C++",
    "csharp": "C#",
    "go": "Go",
    "rust": "Rust",
    "ruby": "Ruby",
    "php": "PHP",
    "swift": "Swift",
    "kotlin": "Kotlin",
    "scala": "Scala",
    "r_lang": "R",
    "matlab": "MATLAB",
    "sql": "SQL",
    "html": "HTML",
    "css": "CSS",
    "react": "React",
    "angular": "Angular",
    "vue": "Vue",
    "nextjs": "Next.js",
    "nodejs": "Node.js",
    "express": "Express",
    "django": "Django",
    "flask": "Flask",
    "fastapi": "FastAPI",
    "spring": "Spring",
    "spring_boot": "Spring Boot",
    "dotnet": ".NET",
    "aspnet": "ASP.NET",
    "pandas": "Pandas",
    "numpy": "NumPy",
    "scikit_learn": "Scikit-learn",
    "tensorflow": "TensorFlow",
    "pytorch": "PyTorch",
    "keras": "Keras",
    "machine_learning": "Machine Learning",
    "deep_learning": "Deep Learning",
    "nlp": "NLP",
    "llm": "LLMs",
    "computer_vision": "Computer Vision",
    "data_analysis": "Data Analysis",
    "data_science": "Data Science",
    "statistics": "Statistics",
    "tableau": "Tableau",
    "power_bi": "Power BI",
    "excel": "Excel",
    "etl": "ETL",
    "streamlit": "Streamlit",
    "aws": "AWS",
    "azure": "Azure",
    "gcp": "Google Cloud",
    "docker": "Docker",
    "kubernetes": "Kubernetes",
    "terraform": "Terraform",
    "ansible": "Ansible",
    "jenkins": "Jenkins",
    "github_actions": "GitHub Actions",
    "cicd": "CI/CD",
    "devops": "DevOps",
    "linux": "Linux",
    "bash": "Bash",
    "postgresql": "PostgreSQL",
    "mysql": "MySQL",
    "mongodb": "MongoDB",
    "redis": "Redis",
    "elasticsearch": "Elasticsearch",
    "sqlite": "SQLite",
    "oracle": "Oracle",
    "dynamodb": "DynamoDB",
    "snowflake": "Snowflake",
    "bigquery": "BigQuery",
    "git": "Git/GitHub",
    "gitlab": "GitLab",
    "jira": "Jira",
    "agile": "Agile",
    "scrum": "Scrum",
    "rest_api": "REST API",
    "graphql": "GraphQL",
    "microservices": "Microservices",
    "oauth": "OAuth",
    "jwt": "JWT",
    "pytest": "Pytest",
    "selenium": "Selenium",
    "postman": "Postman",
    "figma": "Figma",
    "ui_ux": "UI/UX",
}

# pattern (lowercase) -> canonical id; longest patterns are matched first at runtime
PATTERN_TO_CANONICAL: dict[str, str] = {
    # Phrases first (duplicates collapse to one canonical id)
    "rest api": "rest_api",
    "rest apis": "rest_api",
    "restful api": "rest_api",
    "rest": "rest_api",
    "scikit-learn": "scikit_learn",
    "scikit learn": "scikit_learn",
    "machine learning": "machine_learning",
    "deep learning": "deep_learning",
    "computer vision": "computer_vision",
    "data analysis": "data_analysis",
    "data science": "data_science",
    "power bi": "power_bi",
    "google cloud": "gcp",
    "spring boot": "spring_boot",
    "github actions": "github_actions",
    "ci/cd": "cicd",
    "ui/ux": "ui_ux",
    "ai/ml": "machine_learning",
    "ai-ml": "machine_learning",
    # Libraries & frameworks
    "python": "python",
    "fastapi": "fastapi",
    "streamlit": "streamlit",
    "pandas": "pandas",
    "numpy": "numpy",
    "tensorflow": "tensorflow",
    "pytorch": "pytorch",
    "keras": "keras",
    "django": "django",
    "flask": "flask",
    "react": "react",
    "angular": "angular",
    "vue": "vue",
    "next.js": "nextjs",
    "nextjs": "nextjs",
    "node.js": "nodejs",
    "nodejs": "nodejs",
    "express": "express",
    "spring": "spring",
    ".net": "dotnet",
    "asp.net": "aspnet",
    "javascript": "javascript",
    "typescript": "typescript",
    "java": "java",
    "c++": "cpp",
    "c#": "csharp",
    "golang": "go",
    "rust": "rust",
    "ruby": "ruby",
    "php": "php",
    "swift": "swift",
    "kotlin": "kotlin",
    "scala": "scala",
    "matlab": "matlab",
    "sql": "sql",
    "html": "html",
    "css": "css",
    # ML / data (aliases → same canonical)
    "sklearn": "scikit_learn",
    "ml": "machine_learning",
    "nlp": "nlp",
    "llms": "llm",
    "llm": "llm",
    "tableau": "tableau",
    "statistics": "statistics",
    "excel": "excel",
    "etl": "etl",
    # Cloud & ops
    "aws": "aws",
    "azure": "azure",
    "gcp": "gcp",
    "docker": "docker",
    "kubernetes": "kubernetes",
    "k8s": "kubernetes",
    "terraform": "terraform",
    "ansible": "ansible",
    "jenkins": "jenkins",
    "devops": "devops",
    "linux": "linux",
    "bash": "bash",
    # Databases
    "postgresql": "postgresql",
    "postgres": "postgresql",
    "mysql": "mysql",
    "mongodb": "mongodb",
    "redis": "redis",
    "elasticsearch": "elasticsearch",
    "sqlite": "sqlite",
    "oracle": "oracle",
    "dynamodb": "dynamodb",
    "snowflake": "snowflake",
    "bigquery": "bigquery",
    # Tools
    "github": "git",
    "git": "git",
    "gitlab": "gitlab",
    "jira": "jira",
    "agile": "agile",
    "scrum": "scrum",
    "graphql": "graphql",
    "microservices": "microservices",
    "api": "rest_api",
    "apis": "rest_api",
    "oauth": "oauth",
    "jwt": "jwt",
    "pytest": "pytest",
    "selenium": "selenium",
    "postman": "postman",
    "figma": "figma",
    # Single-letter R (requires word boundaries in matcher)
    "r": "r_lang",
}

# Backward-compatible export used by older imports
SKILL_KEYWORDS: list[str] = list(PATTERN_TO_CANONICAL.keys())


def canonical_display(canonical_id: str) -> str:
    """Return the UI label for a canonical skill id."""
    return CANONICAL_DISPLAY.get(canonical_id, canonical_id.replace("_", " ").title())


def canonical_skill_name(keyword: str) -> str:
    """Map a raw pattern or canonical id to a display name."""
    lower = keyword.lower().strip()
    if lower in PATTERN_TO_CANONICAL:
        return canonical_display(PATTERN_TO_CANONICAL[lower])
    return canonical_display(lower) if lower in CANONICAL_DISPLAY else keyword.title()


@lru_cache(maxsize=1)
def _sorted_patterns() -> tuple[tuple[str, str], ...]:
    """Patterns ordered longest-first so 'rest api' wins over 'api'."""
    items = list(PATTERN_TO_CANONICAL.items())
    items.sort(key=lambda x: len(x[0]), reverse=True)
    return tuple(items)


def _phrase_regex(pattern: str) -> re.Pattern[str]:
    """Build a regex that matches a skill phrase without partial-word false positives."""
    escaped = re.escape(pattern)
    # Allow phrase boundaries; slash tokens (ai/ml) need relaxed neighbor rules
    if "/" in pattern or "." in pattern or "+" in pattern or "#" in pattern:
        return re.compile(rf"(?<![a-z0-9]){escaped}(?![a-z0-9])", re.IGNORECASE)
    if " " in pattern:
        return re.compile(rf"(?<![a-z0-9]){escaped}(?![a-z0-9])", re.IGNORECASE)
    pattern = pattern.lower()
    if pattern == "r":
        return re.compile(r"(?<![a-z0-9])r(?![a-z0-9/+])", re.IGNORECASE)
    if pattern == "go":
        return re.compile(r"(?<![a-z0-9])go(?![a-z0-9])", re.IGNORECASE)
    return re.compile(rf"(?<![a-z0-9]){escaped}(?![a-z0-9])", re.IGNORECASE)


_PATTERN_REGEX_CACHE: dict[str, re.Pattern[str]] = {}


def _get_pattern_regex(pattern: str) -> re.Pattern[str]:
    if pattern not in _PATTERN_REGEX_CACHE:
        _PATTERN_REGEX_CACHE[pattern] = _phrase_regex(pattern)
    return _PATTERN_REGEX_CACHE[pattern]


def find_canonical_skills_in_text(text: str) -> set[str]:
    """
    Return canonical skill ids found in ``text`` using only the curated dictionary.
    """
    if not text or not text.strip():
        return set()

    normalized = text.lower()
    normalized = re.sub(r"[\u2018\u2019]", "'", normalized)
    found: set[str] = set()

    for pattern, canonical_id in _sorted_patterns():
        if _get_pattern_regex(pattern).search(normalized):
            found.add(canonical_id)

    return found

"""
Tests for keyword scoring logic.
All GPT calls are mocked — no API key required.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from unittest.mock import patch, MagicMock
import json
import pytest

from app import calculate_keyword_score, EXACT_MATCH_ONLY


# ── Helpers ───────────────────────────────────────────────────────────────────

def _mock_gpt_all_not_found(keywords):
    """Returns a mock GPT response saying none of the keywords were found."""
    result = {kw: {'found': False, 'evidence': ''} for kw in keywords}
    mock = MagicMock()
    mock.choices[0].message.content = json.dumps(result)
    return mock


def _mock_gpt_all_found(keywords):
    """Returns a mock GPT response saying all keywords were found semantically."""
    result = {kw: {'found': True, 'evidence': 'found in resume'} for kw in keywords}
    mock = MagicMock()
    mock.choices[0].message.content = json.dumps(result)
    return mock


# ── Tests ─────────────────────────────────────────────────────────────────────

class TestNopenaltyForExtraSkills:
    """Extra skills on the resume that aren't in the JD must not reduce the score."""

    def test_extra_skills_ignored(self):
        """Resume has Python, SQL, R, Tableau. JD requires Python, SQL only. Score = 100%."""
        jd_keywords = ['Python', 'SQL']
        resume = "Data Scientist skilled in Python and SQL and R and Tableau"

        score, found, missing, _ = calculate_keyword_score(jd_keywords, resume)

        assert score == 100
        assert 'Python' in found
        assert 'SQL' in found
        assert missing == []

    def test_many_extra_skills_do_not_reduce_score(self):
        """Ten extra skills on resume — score still only reflects JD coverage."""
        jd_keywords = ['Python']
        resume = "Python, Java, Go, Rust, Scala, C++, Julia, MATLAB, Swift, Kotlin, R"

        score, found, missing, _ = calculate_keyword_score(jd_keywords, resume)

        assert score == 100
        assert 'Python' in found


class TestKeywordFrequencyIrrelevant:
    """Keyword appearing multiple times must score the same as appearing once."""

    def test_repeated_keyword_same_score(self):
        resume_once = "Expert in Python development"
        resume_many = "Python Python Python Python Python development with Python tools in Python"
        jd_keywords = ['Python']

        score_once, _, _, _ = calculate_keyword_score(jd_keywords, resume_once)
        score_many, _, _, _ = calculate_keyword_score(jd_keywords, resume_many)

        assert score_once == score_many == 100

    def test_single_mention_counts_fully(self):
        jd_keywords = ['Docker', 'Python']
        resume = "Experienced Python developer"  # Docker missing

        score, found, missing, _ = calculate_keyword_score(jd_keywords, resume)

        assert 'Python' in found
        assert 'Docker' in missing
        assert score == 50


class TestCrossSectionKeywordDetection:
    """Keywords found in any section of the resume must count."""

    def test_keyword_in_projects_counts(self):
        jd_keywords = ['LightGBM']
        resume = """
EXPERIENCE
Software Engineer at Acme Corp (2020 - 2022)
Built web APIs.

PROJECTS
Credit Risk Model — Trained LightGBM classifier on financial data.
"""
        score, found, missing, _ = calculate_keyword_score(jd_keywords, resume)

        assert 'LightGBM' in found
        assert score == 100

    def test_keyword_in_summary_counts(self):
        jd_keywords = ['SQL']
        resume = """
Data Scientist skilled in SQL and machine learning.

EXPERIENCE
Analyst at Bank (2019 - 2021)
Performed financial modeling.
"""
        score, found, missing, _ = calculate_keyword_score(jd_keywords, resume)

        assert 'SQL' in found
        assert score == 100

    def test_keyword_in_education_counts(self):
        jd_keywords = ['Python']
        resume = """
EDUCATION
B.S. Computer Science, MIT (2018)
Relevant coursework: Python programming, algorithms, data structures.
"""
        score, found, missing, _ = calculate_keyword_score(jd_keywords, resume)

        assert 'Python' in found
        assert score == 100

    def test_keyword_in_certifications_counts(self):
        jd_keywords = ['AWS']
        resume = """
CERTIFICATIONS
AWS Certified Solutions Architect — Associate (2023)
"""
        score, found, missing, _ = calculate_keyword_score(jd_keywords, resume)

        assert 'AWS' in found
        assert score == 100


class TestCaseInsensitiveMatching:
    """Keyword matching must be case-insensitive."""

    def test_lowercase_in_resume_matches_uppercase_jd(self):
        jd_keywords = ['LightGBM']
        resume = "Used lightgbm for gradient boosting"

        score, found, missing, _ = calculate_keyword_score(jd_keywords, resume)

        assert 'LightGBM' in found
        assert score == 100

    def test_mixed_case_matches(self):
        jd_keywords = ['PyTorch']
        resume = "Trained models using PYTORCH framework"

        score, found, missing, _ = calculate_keyword_score(jd_keywords, resume)

        assert 'PyTorch' in found
        assert score == 100


class TestExactMatchOnlyForHardTechTools:
    """Hard technical tools in EXACT_MATCH_ONLY must NOT be matched semantically."""

    @patch('app.client')
    def test_docker_not_matched_by_containerization(self, mock_client):
        """'Docker' in JD but resume only says 'containerization' — must be missing."""
        # GPT should NOT be called for Docker (it's in EXACT_MATCH_ONLY)
        # Even if it were called, it would say found — but it must not be called
        jd_keywords = ['Docker']
        resume = "Experienced with containerization and container orchestration"

        score, found, missing, semantic = calculate_keyword_score(jd_keywords, resume)

        assert 'Docker' in missing
        assert 'Docker' not in found
        assert score == 0
        # GPT must not have been called for a hard tech tool
        mock_client.chat.completions.create.assert_not_called()

    @patch('app.client')
    def test_aws_not_matched_by_cloud(self, mock_client):
        """'AWS' in JD but resume only says 'cloud computing' — must be missing."""
        jd_keywords = ['AWS']
        resume = "Deployed applications on cloud infrastructure and cloud platforms"

        score, found, missing, _ = calculate_keyword_score(jd_keywords, resume)

        assert 'AWS' in missing
        assert score == 0
        mock_client.chat.completions.create.assert_not_called()

    def test_python_exact_match_required(self):
        """'Python' requires exact match — 'programming language' alone doesn't count."""
        jd_keywords = ['Python']
        resume = "Proficient in multiple programming languages and scripting"

        score, found, missing, _ = calculate_keyword_score(jd_keywords, resume)

        assert 'Python' in missing
        assert score == 0


class TestScoreCalculation:
    """Score = found / total_jd_keywords × 100, rounded."""

    def test_partial_coverage(self):
        jd_keywords = ['Python', 'SQL', 'Docker', 'Kubernetes']
        resume = "Python and SQL developer"  # 2/4 = 50%

        score, found, missing, _ = calculate_keyword_score(jd_keywords, resume)

        assert score == 50
        assert len(found) == 2
        assert len(missing) == 2

    def test_zero_coverage(self):
        jd_keywords = ['Kubernetes', 'Airflow']
        resume = "Experienced marketing professional with communication skills"

        score, found, missing, _ = calculate_keyword_score(jd_keywords, resume)

        assert score == 0
        assert found == []

    def test_empty_jd_keywords(self):
        score, found, missing, semantic = calculate_keyword_score([], "Some resume text")
        assert score == 0
        assert found == []
        assert missing == []

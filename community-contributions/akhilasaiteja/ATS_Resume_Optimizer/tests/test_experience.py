"""
Tests for experience extraction and relevance scoring.
All GPT calls are mocked — no API key required.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from unittest.mock import patch, MagicMock
import json
import pytest
from datetime import datetime

from app import (
    calculate_relevant_experience,
    extract_required_experience,
    _parse_date,
    _extract_experience_entries,
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_classification_response(classifications):
    """Build a mock GPT response for relevance classification."""
    mock = MagicMock()
    mock.choices[0].message.content = json.dumps(classifications)
    return mock


def _build_resume(*jobs):
    """
    Helper to build a resume string with job blocks.
    Each job is a dict: {title, company, start, end, bullets}
    """
    lines = ["John Doe\njohndoe@email.com\n\nEXPERIENCE\n"]
    for j in jobs:
        lines.append(f"{j['title']} | {j['company']}")
        lines.append(f"{j['start']} – {j['end']}")
        for b in j.get('bullets', []):
            lines.append(f"• {b}")
        lines.append("")
    lines.append("EDUCATION\nB.S. Computer Science\n2015 – 2019")
    return '\n'.join(lines)


# ── Tests: extract_required_experience ────────────────────────────────────────

class TestExtractRequiredExperience:
    def test_plus_years_pattern(self):
        jd = "We require 3+ years of experience in data science."
        assert extract_required_experience(jd) == 3

    def test_range_pattern(self):
        jd = "Seeking candidates with 2-5 years of relevant experience."
        assert extract_required_experience(jd) == 2

    def test_minimum_pattern(self):
        jd = "Minimum 4 years of software engineering experience required."
        assert extract_required_experience(jd) == 4

    def test_at_least_pattern(self):
        jd = "At least 2 years working with machine learning models."
        assert extract_required_experience(jd) == 2

    def test_or_more_pattern(self):
        jd = "5 or more years of experience in data engineering."
        assert extract_required_experience(jd) == 5

    def test_no_requirement_returns_none(self):
        jd = "Looking for a talented data scientist to join our team."
        assert extract_required_experience(jd) is None


# ── Tests: _parse_date ────────────────────────────────────────────────────────

class TestParseDate:
    def test_present_returns_today(self):
        result = _parse_date('Present', use_gpt_fallback=False)
        assert result is not None
        assert result.year == datetime.now().year

    def test_current_returns_today(self):
        result = _parse_date('Current', use_gpt_fallback=False)
        assert result is not None
        assert result.month == datetime.now().month

    def test_now_returns_today(self):
        result = _parse_date('Now', use_gpt_fallback=False)
        assert result is not None

    def test_abbreviated_month_year(self):
        result = _parse_date('Jan 2022', use_gpt_fallback=False)
        assert result is not None
        assert result.year == 2022
        assert result.month == 1

    def test_full_month_year(self):
        result = _parse_date('September 2020', use_gpt_fallback=False)
        assert result is not None
        assert result.year == 2020
        assert result.month == 9

    def test_year_only(self):
        result = _parse_date('2019', use_gpt_fallback=False)
        assert result is not None
        assert result.year == 2019

    def test_invalid_returns_none_no_fallback(self):
        result = _parse_date('definitely not a date', use_gpt_fallback=False)
        assert result is None


# ── Tests: relevance classification ──────────────────────────────────────────

class TestIrrelevantExperienceZero:
    """Completely unrelated roles should contribute 0 years."""

    @patch('app.client')
    def test_radio_presenter_to_ds_zero(self, mock_client):
        mock_client.chat.completions.create.return_value = _make_classification_response([
            {
                'job_number': 1,
                'job_title': 'Radio Presenter',
                'relevance': 'none',
                'multiplier': 0.0,
                'reason': 'Broadcasting has no overlap with Data Science'
            }
        ])

        resume = _build_resume({
            'title': 'Radio Presenter',
            'company': 'All India Radio',
            'start': 'Jan 2018',
            'end': 'Dec 2019',
            'bullets': ['Hosted morning show', 'Presented news segments']
        })
        jd = "Data Scientist with 3+ years of experience in ML and Python."

        relevant_years, breakdown, _ = calculate_relevant_experience(
            resume, 'Data Scientist', jd
        )

        assert breakdown[0]['multiplier'] == 0.0
        assert breakdown[0]['counted_years'] == 0.0
        assert relevant_years == 0.0

    @patch('app.client')
    def test_retail_sales_to_ml_engineer_zero(self, mock_client):
        mock_client.chat.completions.create.return_value = _make_classification_response([
            {
                'job_number': 1,
                'job_title': 'Retail Sales Associate',
                'relevance': 'none',
                'multiplier': 0.0,
                'reason': 'Retail sales has no technical overlap with ML Engineering'
            }
        ])

        resume = _build_resume({
            'title': 'Retail Sales Associate',
            'company': 'Supermart',
            'start': 'Jun 2019',
            'end': 'Jun 2021',
            'bullets': ['Assisted customers', 'Managed inventory']
        })

        relevant_years, breakdown, _ = calculate_relevant_experience(
            resume, 'Machine Learning Engineer', "2+ years ML experience required"
        )

        assert breakdown[0]['counted_years'] == 0.0


class TestPartialExperienceHalf:
    """Partially relevant roles should apply 0.5× multiplier."""

    @patch('app.client')
    def test_banking_analyst_to_ds_half(self, mock_client):
        mock_client.chat.completions.create.return_value = _make_classification_response([
            {
                'job_number': 1,
                'job_title': 'Banking Analyst',
                'relevance': 'partial',
                'multiplier': 0.5,
                'reason': 'Analytical work overlaps but domain differs from Data Science'
            }
        ])

        resume = _build_resume({
            'title': 'Banking Analyst',
            'company': 'State Bank of India',
            'start': 'Jan 2020',
            'end': 'Jan 2022',
            'bullets': ['Analyzed credit risk', 'Built Excel models']
        })
        jd = "Data Scientist with 3+ years. Python, SQL required."

        relevant_years, breakdown, _ = calculate_relevant_experience(
            resume, 'Data Scientist', jd
        )

        assert breakdown[0]['multiplier'] == 0.5
        assert breakdown[0]['counted_years'] == pytest.approx(1.0, abs=0.2)

    @patch('app.client')
    def test_swe_to_mle_partial(self, mock_client):
        mock_client.chat.completions.create.return_value = _make_classification_response([
            {
                'job_number': 1,
                'job_title': 'Software Engineer',
                'relevance': 'partial',
                'multiplier': 0.5,
                'reason': 'SWE skills partially transfer to ML Engineering'
            }
        ])

        resume = _build_resume({
            'title': 'Software Engineer',
            'company': 'Tech Corp',
            'start': 'Mar 2019',
            'end': 'Mar 2021',
            'bullets': ['Built REST APIs in Python', 'Deployed services on AWS']
        })

        _, breakdown, _ = calculate_relevant_experience(
            resume, 'Machine Learning Engineer', "2+ years ML required"
        )

        assert breakdown[0]['multiplier'] == 0.5


class TestRelevantExperienceFull:
    """Directly relevant roles should apply 1.0× multiplier."""

    @patch('app.client')
    def test_ml_research_assistant_to_ds_full(self, mock_client):
        mock_client.chat.completions.create.return_value = _make_classification_response([
            {
                'job_number': 1,
                'job_title': 'ML Research Assistant',
                'relevance': 'full',
                'multiplier': 1.0,
                'reason': 'Direct ML/NLP work is fully relevant to Data Scientist role'
            }
        ])

        resume = _build_resume({
            'title': 'ML Research Assistant',
            'company': 'University Lab',
            'start': 'Jun 2021',
            'end': 'Jun 2022',
            'bullets': ['Trained NLP models using PyTorch', 'Published research paper']
        })
        jd = "Data Scientist with 3+ years. NLP and Python required."

        relevant_years, breakdown, _ = calculate_relevant_experience(
            resume, 'Data Scientist', jd
        )

        assert breakdown[0]['multiplier'] == 1.0
        assert breakdown[0]['counted_years'] == pytest.approx(1.0, abs=0.1)

    @patch('app.client')
    def test_data_scientist_to_ds_full(self, mock_client):
        mock_client.chat.completions.create.return_value = _make_classification_response([
            {
                'job_number': 1,
                'job_title': 'Data Scientist',
                'relevance': 'full',
                'multiplier': 1.0,
                'reason': 'Same role — directly relevant'
            }
        ])

        resume = _build_resume({
            'title': 'Data Scientist',
            'company': 'Analytics Co',
            'start': 'Jan 2020',
            'end': 'Jan 2023',
            'bullets': ['Built predictive models', 'Used Python, SQL, scikit-learn']
        })

        relevant_years, breakdown, _ = calculate_relevant_experience(
            resume, 'Data Scientist', "3+ years experience"
        )

        assert breakdown[0]['multiplier'] == 1.0
        assert relevant_years == pytest.approx(3.0, abs=0.2)


class TestExperienceGapDetection:
    """Gap detection — required years vs relevant years."""

    @patch('app.client')
    def test_gap_reported_correctly(self, mock_client):
        """JD requires 3 years, candidate has 1.5 relevant — gap = 1.5 years."""
        mock_client.chat.completions.create.return_value = _make_classification_response([
            {
                'job_number': 1,
                'job_title': 'ML Research Assistant',
                'relevance': 'full',
                'multiplier': 1.0,
                'reason': 'Directly relevant ML work'
            },
            {
                'job_number': 2,
                'job_title': 'Radio Presenter',
                'relevance': 'none',
                'multiplier': 0.0,
                'reason': 'Not relevant to Data Science'
            }
        ])

        resume = _build_resume(
            {
                'title': 'ML Research Assistant',
                'company': 'University',
                'start': 'Jun 2022',
                'end': 'Dec 2022',  # ~6 months
                'bullets': ['NLP research']
            },
            {
                'title': 'Radio Presenter',
                'company': 'All India Radio',
                'start': 'Jan 2020',
                'end': 'Jan 2022',  # 2 years, 0x
                'bullets': ['Hosted show']
            }
        )
        jd = "Data Scientist with 3+ years required."

        relevant_years, breakdown, required_years = calculate_relevant_experience(
            resume, 'Data Scientist', jd
        )

        assert required_years == 3
        assert relevant_years < required_years  # gap exists
        gap = required_years - relevant_years
        assert gap > 0

    @patch('app.client')
    def test_no_gap_when_requirement_met(self, mock_client):
        mock_client.chat.completions.create.return_value = _make_classification_response([
            {
                'job_number': 1,
                'job_title': 'Data Scientist',
                'relevance': 'full',
                'multiplier': 1.0,
                'reason': 'Same role'
            }
        ])

        resume = _build_resume({
            'title': 'Data Scientist',
            'company': 'Big Tech',
            'start': 'Jan 2020',
            'end': 'Jan 2024',  # 4 years
            'bullets': ['ML models', 'Python, SQL']
        })
        jd = "Data Scientist. 3+ years required."

        relevant_years, _, required_years = calculate_relevant_experience(
            resume, 'Data Scientist', jd
        )

        assert required_years == 3
        assert relevant_years >= required_years


class TestReasonInBreakdown:
    """Each job entry must include a reason explaining the relevance score."""

    @patch('app.client')
    def test_reason_present_in_breakdown(self, mock_client):
        mock_client.chat.completions.create.return_value = _make_classification_response([
            {
                'job_number': 1,
                'job_title': 'Data Analyst',
                'relevance': 'partial',
                'multiplier': 0.5,
                'reason': 'Analytical overlap but less technical than DS'
            }
        ])

        resume = _build_resume({
            'title': 'Data Analyst',
            'company': 'Retail Co',
            'start': 'Jan 2021',
            'end': 'Jan 2023',
            'bullets': ['SQL queries', 'Tableau dashboards']
        })

        _, breakdown, _ = calculate_relevant_experience(
            resume, 'Data Scientist', "2+ years required"
        )

        assert len(breakdown) > 0
        assert breakdown[0]['reason'] != ''
        assert 'analytical' in breakdown[0]['reason'].lower() or len(breakdown[0]['reason']) > 5

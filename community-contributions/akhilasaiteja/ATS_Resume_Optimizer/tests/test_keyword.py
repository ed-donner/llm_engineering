"""
Tests for keyword extraction and semantic matching.
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

def _make_gpt_response(result_dict):
    mock = MagicMock()
    mock.choices[0].message.content = json.dumps(result_dict)
    return mock


# ── Tests ─────────────────────────────────────────────────────────────────────

class TestMissingSkillsDetection:
    """Correctly identifies skills required by JD but not in the resume."""

    def test_missing_hard_tool_detected(self):
        jd_keywords = ['Python', 'Docker', 'Kubernetes']
        resume = "Python developer with experience in web services"

        _, found, missing, _ = calculate_keyword_score(jd_keywords, resume)

        assert 'Python' in found
        assert 'Docker' in missing
        assert 'Kubernetes' in missing

    def test_all_present_no_missing(self):
        jd_keywords = ['Python', 'SQL', 'AWS']
        resume = "Python, SQL, and AWS cloud developer"

        _, _, missing, _ = calculate_keyword_score(jd_keywords, resume)

        assert missing == []

    def test_partial_missing(self):
        jd_keywords = ['Python', 'SQL', 'Spark', 'Airflow']
        resume = "Python and SQL analyst. No big data experience."

        _, found, missing, _ = calculate_keyword_score(jd_keywords, resume)

        assert 'Python' in found
        assert 'SQL' in found
        assert 'Spark' in missing
        assert 'Airflow' in missing


class TestSemanticMatchForSoftSkills:
    """Soft skills not in EXACT_MATCH_ONLY should be checked via GPT semantic layer."""

    @patch('app.client')
    def test_collaboration_matched_via_semantic(self, mock_client):
        """'partnered with cross-functional teams' should match 'collaboration' via GPT."""
        mock_client.chat.completions.create.return_value = _make_gpt_response({
            'collaboration': {'found': True, 'evidence': 'partnered with cross-functional teams'}
        })

        jd_keywords = ['collaboration']
        resume = "Partnered with cross-functional teams to deliver data pipelines on time."

        score, found, missing, semantic = calculate_keyword_score(jd_keywords, resume)

        assert 'collaboration' in found
        assert score == 100
        assert any(m['keyword'] == 'collaboration' for m in semantic)

    @patch('app.client')
    def test_communication_matched_semantically(self, mock_client):
        """'presented findings to stakeholders' should match 'communication' via GPT."""
        mock_client.chat.completions.create.return_value = _make_gpt_response({
            'communication': {'found': True, 'evidence': 'presented findings to stakeholders'}
        })

        jd_keywords = ['communication']
        resume = "Regularly presented findings to senior stakeholders and leadership."

        _, found, missing, semantic = calculate_keyword_score(jd_keywords, resume)

        assert 'communication' in found
        assert missing == []

    @patch('app.client')
    def test_soft_skill_not_found_stays_missing(self, mock_client):
        """GPT returns false — soft skill genuinely missing."""
        mock_client.chat.completions.create.return_value = _make_gpt_response({
            'leadership': {'found': False, 'evidence': ''}
        })

        jd_keywords = ['leadership']
        resume = "Data analyst working independently on SQL queries."

        _, found, missing, _ = calculate_keyword_score(jd_keywords, resume)

        assert 'leadership' in missing
        assert 'leadership' not in found


class TestNoSemanticMatchForHardTools:
    """Hard technical tools must NEVER be matched via GPT semantic layer."""

    @patch('app.client')
    def test_docker_exact_match_only(self, mock_client):
        """GPT must not be called for Docker — it is in EXACT_MATCH_ONLY."""
        jd_keywords = ['Docker']
        resume = "Experience with container orchestration and CI/CD pipelines."

        score, found, missing, _ = calculate_keyword_score(jd_keywords, resume)

        # Docker is not in resume exactly → must be missing
        assert 'Docker' in missing
        assert score == 0
        # GPT must NOT have been called
        mock_client.chat.completions.create.assert_not_called()

    @patch('app.client')
    def test_kubernetes_exact_match_only(self, mock_client):
        jd_keywords = ['Kubernetes']
        resume = "Managed container deployments at scale using orchestration tools."

        _, found, missing, _ = calculate_keyword_score(jd_keywords, resume)

        assert 'Kubernetes' in missing
        mock_client.chat.completions.create.assert_not_called()

    @patch('app.client')
    def test_mixed_hard_and_soft_skills(self, mock_client):
        """Hard tools stay exact-match; soft skills go to GPT batch."""
        mock_client.chat.completions.create.return_value = _make_gpt_response({
            'teamwork': {'found': True, 'evidence': 'collaborated with team'}
        })

        jd_keywords = ['Docker', 'teamwork']
        resume = "Collaborated effectively with team members on data projects."
        # Docker not in resume → missing (exact only)
        # teamwork not in resume exactly → goes to GPT → found semantically

        _, found, missing, semantic = calculate_keyword_score(jd_keywords, resume)

        assert 'Docker' in missing
        assert 'teamwork' in found
        assert any(m['keyword'] == 'teamwork' for m in semantic)
        # GPT called once for the soft skill batch only
        mock_client.chat.completions.create.assert_called_once()


class TestExactMatchOnlySet:
    """Verify the EXACT_MATCH_ONLY set contains the expected tools."""

    def test_core_languages_in_set(self):
        for lang in ['Python', 'SQL', 'R', 'Java']:
            assert lang in EXACT_MATCH_ONLY, f"{lang} should be in EXACT_MATCH_ONLY"

    def test_cloud_providers_in_set(self):
        for cloud in ['AWS', 'GCP', 'Azure']:
            assert cloud in EXACT_MATCH_ONLY

    def test_ml_frameworks_in_set(self):
        for fw in ['TensorFlow', 'PyTorch', 'scikit-learn', 'LightGBM', 'XGBoost']:
            assert fw in EXACT_MATCH_ONLY

    def test_devops_tools_in_set(self):
        for tool in ['Docker', 'Kubernetes', 'Airflow']:
            assert tool in EXACT_MATCH_ONLY

    def test_soft_skill_not_in_set(self):
        """Soft skills must NOT be in EXACT_MATCH_ONLY so they can be semantically matched."""
        soft_skills = ['collaboration', 'communication', 'leadership', 'teamwork']
        for skill in soft_skills:
            assert skill not in EXACT_MATCH_ONLY, (
                f"'{skill}' should NOT be in EXACT_MATCH_ONLY — it's a soft skill"
            )

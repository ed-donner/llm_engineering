"""Integration tests for the Gradio app interface."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from app import extract_profile_from_text
from models.cats import CatProfile, Cat, CatMatch


@pytest.fixture
def mock_framework():
    """Mock the TuxedoLinkFramework."""
    with patch('app.framework') as mock:
        # Create a mock result
        mock_cat = Cat(
            id="test_1",
            name="Test Cat",
            breed="Persian",
            age="young",
            gender="female",
            size="medium",
            city="New York",
            state="NY",
            source="test",
            organization_name="Test Rescue",
            url="https://example.com/cat/test_1",
            description="A friendly and playful cat"
        )
        
        mock_match = CatMatch(
            cat=mock_cat,
            match_score=0.95,
            vector_similarity=0.92,
            attribute_match_score=0.98,
            explanation="Great match for your preferences"
        )
        
        mock_result = Mock()
        mock_result.matches = [mock_match]
        mock_result.search_time = 0.5
        mock.search.return_value = mock_result
        
        yield mock


@pytest.fixture
def mock_profile_agent():
    """Mock the ProfileAgent."""
    with patch('app.profile_agent') as mock:
        mock_profile = CatProfile(
            user_location="10001",
            max_distance=50,
            personality_description="friendly and playful",
            age_range=["young"],
            good_with_children=True
        )
        mock.extract_profile.return_value = mock_profile
        yield mock


class TestAppInterface:
    """Test the Gradio app interface functions."""
    
    def test_extract_profile_with_valid_input(self, mock_framework, mock_profile_agent):
        """Test that valid user input is processed correctly."""
        user_input = "I want a friendly kitten in NYC"
        
        chat_history, results_html, profile_json = extract_profile_from_text(user_input, use_cache=True)
        
        # Verify chat history format (messages format)
        assert isinstance(chat_history, list)
        assert len(chat_history) == 2
        assert chat_history[0]["role"] == "user"
        assert chat_history[0]["content"] == user_input
        assert chat_history[1]["role"] == "assistant"
        assert "Found" in chat_history[1]["content"] or "match" in chat_history[1]["content"].lower()
        
        # Verify profile agent was called with correct format
        mock_profile_agent.extract_profile.assert_called_once()
        call_args = mock_profile_agent.extract_profile.call_args[0][0]
        assert isinstance(call_args, list)
        assert call_args[0]["role"] == "user"
        assert call_args[0]["content"] == user_input
        
        # Verify results HTML is generated
        assert results_html
        assert "<div" in results_html
        
        # Verify profile JSON is returned
        assert profile_json
    
    def test_extract_profile_with_empty_input(self, mock_framework, mock_profile_agent):
        """Test that empty input uses placeholder text."""
        user_input = ""
        
        chat_history, results_html, profile_json = extract_profile_from_text(user_input, use_cache=True)
        
        # Verify placeholder text was used
        mock_profile_agent.extract_profile.assert_called_once()
        call_args = mock_profile_agent.extract_profile.call_args[0][0]
        assert call_args[0]["content"] != ""
        assert "friendly" in call_args[0]["content"].lower()
        assert "playful" in call_args[0]["content"].lower()
        
        # Verify chat history format
        assert isinstance(chat_history, list)
        assert len(chat_history) == 2
        assert chat_history[0]["role"] == "user"
        assert chat_history[1]["role"] == "assistant"
    
    def test_extract_profile_with_whitespace_input(self, mock_framework, mock_profile_agent):
        """Test that whitespace-only input uses placeholder text."""
        user_input = "   \n\t  "
        
        chat_history, results_html, profile_json = extract_profile_from_text(user_input, use_cache=True)
        
        # Verify placeholder text was used
        mock_profile_agent.extract_profile.assert_called_once()
        call_args = mock_profile_agent.extract_profile.call_args[0][0]
        assert call_args[0]["content"].strip() != ""
    
    def test_extract_profile_error_handling(self, mock_framework, mock_profile_agent):
        """Test error handling when profile extraction fails."""
        user_input = "I want a cat"
        
        # Make profile agent raise an error
        mock_profile_agent.extract_profile.side_effect = Exception("API Error")
        
        chat_history, results_html, profile_json = extract_profile_from_text(user_input, use_cache=True)
        
        # Verify error message is in chat history
        assert isinstance(chat_history, list)
        assert len(chat_history) == 2
        assert chat_history[0]["role"] == "user"
        assert chat_history[1]["role"] == "assistant"
        assert "Error" in chat_history[1]["content"] or "❌" in chat_history[1]["content"]
        
        # Verify empty results
        assert results_html == ""
        assert profile_json == ""
    
    def test_cache_mode_parameter(self, mock_framework, mock_profile_agent):
        """Test that cache mode parameter is passed correctly."""
        user_input = "I want a cat in NYC"
        
        # Test with cache=True
        extract_profile_from_text(user_input, use_cache=True)
        mock_framework.search.assert_called_once()
        assert mock_framework.search.call_args[1]["use_cache"] is True
        
        # Reset and test with cache=False
        mock_framework.reset_mock()
        extract_profile_from_text(user_input, use_cache=False)
        mock_framework.search.assert_called_once()
        assert mock_framework.search.call_args[1]["use_cache"] is False
    
    def test_messages_format_consistency(self, mock_framework, mock_profile_agent):
        """Test that messages format is consistent throughout."""
        user_input = "Show me cats"
        
        chat_history, _, _ = extract_profile_from_text(user_input, use_cache=True)
        
        # Verify all messages have correct format
        for msg in chat_history:
            assert isinstance(msg, dict)
            assert "role" in msg
            assert "content" in msg
            assert msg["role"] in ["user", "assistant"]
            assert isinstance(msg["content"], str)
    
    def test_example_button_scenarios(self, mock_framework, mock_profile_agent):
        """Test example button text scenarios."""
        examples = [
            "I want a friendly family cat in zip code 10001, good with children and dogs",
            "Looking for a playful young kitten near New York City",
            "I need a calm, affectionate adult cat that likes to cuddle",
            "Show me cats good with children in the NYC area"
        ]
        
        for example in examples:
            mock_profile_agent.reset_mock()
            mock_framework.reset_mock()
            
            chat_history, results_html, profile_json = extract_profile_from_text(example, use_cache=True)
            
            # Verify each example is processed
            assert isinstance(chat_history, list)
            assert len(chat_history) == 2
            assert chat_history[0]["content"] == example
            mock_profile_agent.extract_profile.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


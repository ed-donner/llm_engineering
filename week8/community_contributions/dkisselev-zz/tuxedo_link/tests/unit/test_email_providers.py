"""Unit tests for email providers."""

import pytest
from unittest.mock import patch, MagicMock
from agents.email_providers import (
    EmailProvider,
    MailgunProvider,
    SendGridProvider,
    get_email_provider
)


class TestMailgunProvider:
    """Tests for Mailgun email provider."""
    
    @patch.dict('os.environ', {'MAILGUN_API_KEY': 'test-api-key'})
    @patch('agents.email_providers.mailgun_provider.get_mailgun_config')
    @patch('agents.email_providers.mailgun_provider.get_email_config')
    def test_init(self, mock_email_config, mock_mailgun_config):
        """Test Mailgun provider initialization."""
        mock_mailgun_config.return_value = {
            'domain': 'test.mailgun.org'
        }
        mock_email_config.return_value = {
            'from_name': 'Test App',
            'from_email': 'test@test.com'
        }
        
        provider = MailgunProvider()
        
        assert provider.api_key == 'test-api-key'
        assert provider.domain == 'test.mailgun.org'
        assert provider.default_from_name == 'Test App'
        assert provider.default_from_email == 'test@test.com'
    
    @patch.dict('os.environ', {})
    @patch('agents.email_providers.mailgun_provider.get_mailgun_config')
    @patch('agents.email_providers.mailgun_provider.get_email_config')
    def test_init_missing_api_key(self, mock_email_config, mock_mailgun_config):
        """Test that initialization fails without API key."""
        mock_mailgun_config.return_value = {'domain': 'test.mailgun.org'}
        mock_email_config.return_value = {
            'from_name': 'Test', 
            'from_email': 'test@test.com'
        }
        
        with pytest.raises(ValueError, match="MAILGUN_API_KEY"):
            MailgunProvider()
    
    @patch('agents.email_providers.mailgun_provider.requests.post')
    @patch.dict('os.environ', {'MAILGUN_API_KEY': 'test-api-key'})
    @patch('agents.email_providers.mailgun_provider.get_mailgun_config')
    @patch('agents.email_providers.mailgun_provider.get_email_config')
    def test_send_email_success(self, mock_email_config, mock_mailgun_config, mock_post):
        """Test successful email sending."""
        mock_mailgun_config.return_value = {'domain': 'test.mailgun.org'}
        mock_email_config.return_value = {
            'from_name': 'Test App',
            'from_email': 'test@test.com'
        }
        
        # Mock successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        provider = MailgunProvider()
        result = provider.send_email(
            to="recipient@test.com",
            subject="Test Subject",
            html="<p>Test HTML</p>",
            text="Test Text"
        )
        
        assert result is True
        mock_post.assert_called_once()
        
        # Check request parameters
        call_args = mock_post.call_args
        assert call_args[1]['auth'] == ('api', 'test-api-key')
        assert call_args[1]['data']['to'] == 'recipient@test.com'
        assert call_args[1]['data']['subject'] == 'Test Subject'
    
    @patch('agents.email_providers.mailgun_provider.requests.post')
    @patch.dict('os.environ', {'MAILGUN_API_KEY': 'test-api-key'})
    @patch('agents.email_providers.mailgun_provider.get_mailgun_config')
    @patch('agents.email_providers.mailgun_provider.get_email_config')
    def test_send_email_failure(self, mock_email_config, mock_mailgun_config, mock_post):
        """Test email sending failure."""
        mock_mailgun_config.return_value = {'domain': 'test.mailgun.org'}
        mock_email_config.return_value = {
            'from_name': 'Test App',
            'from_email': 'test@test.com'
        }
        
        # Mock failed response
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"
        mock_post.return_value = mock_response
        
        provider = MailgunProvider()
        result = provider.send_email(
            to="recipient@test.com",
            subject="Test",
            html="<p>Test</p>",
            text="Test"
        )
        
        assert result is False
    
    @patch.dict('os.environ', {'MAILGUN_API_KEY': 'test-api-key'})
    @patch('agents.email_providers.mailgun_provider.get_mailgun_config')
    @patch('agents.email_providers.mailgun_provider.get_email_config')
    def test_get_provider_name(self, mock_email_config, mock_mailgun_config):
        """Test provider name."""
        mock_mailgun_config.return_value = {'domain': 'test.mailgun.org'}
        mock_email_config.return_value = {
            'from_name': 'Test',
            'from_email': 'test@test.com'
        }
        
        provider = MailgunProvider()
        assert provider.get_provider_name() == "mailgun"


class TestSendGridProvider:
    """Tests for SendGrid email provider (stub)."""
    
    @patch.dict('os.environ', {'SENDGRID_API_KEY': 'test-api-key'})
    @patch('agents.email_providers.sendgrid_provider.get_email_config')
    def test_init(self, mock_email_config):
        """Test SendGrid provider initialization."""
        mock_email_config.return_value = {
            'from_name': 'Test App',
            'from_email': 'test@test.com'
        }
        
        provider = SendGridProvider()
        
        assert provider.api_key == 'test-api-key'
        assert provider.default_from_name == 'Test App'
        assert provider.default_from_email == 'test@test.com'
    
    @patch.dict('os.environ', {'SENDGRID_API_KEY': 'test-api-key'})
    @patch('agents.email_providers.sendgrid_provider.get_email_config')
    def test_send_email_stub(self, mock_email_config):
        """Test that SendGrid stub always succeeds."""
        mock_email_config.return_value = {
            'from_name': 'Test',
            'from_email': 'test@test.com'
        }
        
        provider = SendGridProvider()
        result = provider.send_email(
            to="test@test.com",
            subject="Test",
            html="<p>Test</p>",
            text="Test"
        )
        
        # Stub should always return True
        assert result is True
    
    @patch.dict('os.environ', {'SENDGRID_API_KEY': 'test-api-key'})
    @patch('agents.email_providers.sendgrid_provider.get_email_config')
    def test_get_provider_name(self, mock_email_config):
        """Test provider name."""
        mock_email_config.return_value = {
            'from_name': 'Test',
            'from_email': 'test@test.com'
        }
        
        provider = SendGridProvider()
        assert provider.get_provider_name() == "sendgrid (stub)"


class TestEmailProviderFactory:
    """Tests for email provider factory."""
    
    @patch('agents.email_providers.factory.get_configured_provider')
    @patch.dict('os.environ', {'MAILGUN_API_KEY': 'test-key'})
    @patch('agents.email_providers.mailgun_provider.get_mailgun_config')
    @patch('agents.email_providers.mailgun_provider.get_email_config')
    def test_get_mailgun_provider(self, mock_email_config, mock_mailgun_config, mock_get_configured):
        """Test getting Mailgun provider."""
        mock_get_configured.return_value = 'mailgun'
        mock_mailgun_config.return_value = {'domain': 'test.mailgun.org'}
        mock_email_config.return_value = {
            'from_name': 'Test',
            'from_email': 'test@test.com'
        }
        
        provider = get_email_provider()
        
        assert isinstance(provider, MailgunProvider)
    
    @patch('agents.email_providers.factory.get_configured_provider')
    @patch.dict('os.environ', {})
    @patch('agents.email_providers.sendgrid_provider.get_email_config')
    def test_get_sendgrid_provider(self, mock_email_config, mock_get_configured):
        """Test getting SendGrid provider."""
        mock_get_configured.return_value = 'sendgrid'
        mock_email_config.return_value = {
            'from_name': 'Test',
            'from_email': 'test@test.com'
        }
        
        provider = get_email_provider()
        
        assert isinstance(provider, SendGridProvider)
    
    @patch('agents.email_providers.factory.get_configured_provider')
    def test_unknown_provider(self, mock_get_configured):
        """Test that unknown provider raises error."""
        mock_get_configured.return_value = 'unknown'
        
        with pytest.raises(ValueError, match="Unknown email provider"):
            get_email_provider()
    
    @patch.dict('os.environ', {'MAILGUN_API_KEY': 'test-key'})
    @patch('agents.email_providers.mailgun_provider.get_mailgun_config')
    @patch('agents.email_providers.mailgun_provider.get_email_config')
    def test_explicit_provider_name(self, mock_email_config, mock_mailgun_config):
        """Test explicitly specifying provider name."""
        mock_mailgun_config.return_value = {'domain': 'test.mailgun.org'}
        mock_email_config.return_value = {
            'from_name': 'Test',
            'from_email': 'test@test.com'
        }
        
        provider = get_email_provider('mailgun')
        
        assert isinstance(provider, MailgunProvider)


import pytest
from unittest.mock import MagicMock, patch
from services.llm_service import GeminiProvider, OllamaProvider, get_llm_service
from config import settings

@pytest.fixture
def gemini_provider():
    with patch('google.generativeai.configure'):
        with patch('google.generativeai.GenerativeModel') as MockModel:
            provider = GeminiProvider()
            provider.model = MockModel.return_value
            return provider

@pytest.fixture
def ollama_provider():
    return OllamaProvider()

def test_gemini_summarize_text(gemini_provider):
    mock_response = MagicMock()
    mock_response.text = "Summary"
    gemini_provider.model.generate_content.return_value = mock_response
    
    summary = gemini_provider.summarize_text("Long text")
    
    assert summary == "Summary"
    gemini_provider.model.generate_content.assert_called_once()

def test_gemini_generate_embedding(gemini_provider):
    with patch('google.generativeai.embed_content') as mock_embed:
        mock_embed.return_value = {'embedding': [0.1, 0.2, 0.3]}
        
        embedding = gemini_provider.generate_embedding("Text")
        
        assert embedding == [0.1, 0.2, 0.3]
        mock_embed.assert_called_once()

@patch('requests.post')
def test_ollama_summarize_text(mock_post, ollama_provider):
    mock_response = MagicMock()
    mock_response.json.return_value = {
        'choices': [{'message': {'content': 'Ollama Summary'}}]
    }
    mock_response.raise_for_status.return_value = None
    mock_post.return_value = mock_response

    summary = ollama_provider.summarize_text("Long text")
    
    assert summary == "Ollama Summary"
    mock_post.assert_called_once()

@patch('requests.post')
def test_ollama_generate_embedding(mock_post, ollama_provider):
    mock_response = MagicMock()
    mock_response.json.return_value = {
        'data': [{'embedding': [0.4, 0.5, 0.6]}]
    }
    mock_response.raise_for_status.return_value = None
    mock_post.return_value = mock_response

    embedding = ollama_provider.generate_embedding("Text")
    
    assert embedding == [0.4, 0.5, 0.6]
    mock_post.assert_called_once()

def test_get_llm_service_factory():
    # Test default (local)
    settings.AI_PROVIDER = "local"
    service = get_llm_service()
    assert isinstance(service, OllamaProvider)

    # Test gemini
    settings.AI_PROVIDER = "gemini"
    # We need to mock genai.configure since GeminiProvider init calls it
    with patch('google.generativeai.configure'):
        with patch('google.generativeai.GenerativeModel'):
            service = get_llm_service()
            assert isinstance(service, GeminiProvider)

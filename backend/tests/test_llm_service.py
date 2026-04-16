import pytest
from unittest.mock import MagicMock, patch
from services.llm_service import GeminiProvider, OllamaProvider, get_llm_service
from config import settings

@pytest.fixture
def gemini_provider():
    with patch('services.llm_service.genai.Client') as MockClient:
        provider = GeminiProvider()
        return provider

@pytest.fixture
def ollama_provider():
    return OllamaProvider()

def test_gemini_summarize_text(gemini_provider):
    mock_response = MagicMock()
    mock_response.text = "Summary"
    gemini_provider.client.models.generate_content.return_value = mock_response
    
    summary = gemini_provider.summarize_text("Long text")
    
    assert summary == "Summary"
    gemini_provider.client.models.generate_content.assert_called_once()

def test_gemini_generate_embedding(gemini_provider):
    mock_response = MagicMock()
    mock_val = MagicMock()
    mock_val.values = [0.1, 0.2, 0.3]
    mock_response.embeddings = [mock_val]
    gemini_provider.client.models.embed_content.return_value = mock_response
    
    embedding = gemini_provider.generate_embedding("Text")
    
    assert embedding == [0.1, 0.2, 0.3]
    gemini_provider.client.models.embed_content.assert_called_once()

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
    with patch('services.llm_service.settings') as mock_settings:
        mock_settings.AI_PROVIDER = "local"
        service = get_llm_service()
        assert isinstance(service, OllamaProvider)

    # Test gemini
    with patch('services.llm_service.settings') as mock_settings:
        mock_settings.AI_PROVIDER = "gemini"
        with patch('services.llm_service.genai.Client'):
            service = get_llm_service()
            assert isinstance(service, GeminiProvider)

def test_ollama_model_fallbacks():
    # Reset settings to ensure no leftover state
    with patch('services.llm_service.settings') as mock_settings:
        mock_settings.LITELLM_BASE_URL = "http://localhost:4000/v1"
        mock_settings.LITELLM_API_KEY = ""
        mock_settings.OLLAMA_CHAT_MODEL = "chat-model"
        mock_settings.OLLAMA_SUMMARIZATION_MODEL = None
        mock_settings.OLLAMA_ENTITY_MODEL = None
        mock_settings.OLLAMA_CLASSIFICATION_MODEL = None
        mock_settings.OLLAMA_EMBEDDING_MODEL = "embed-model"

        provider = OllamaProvider()
        assert provider.chat_model == "chat-model"
        assert provider.summarization_model == "chat-model"  # Fallback
        assert provider.entity_model == "chat-model"         # Fallback
        assert provider.classification_model == "chat-model" # Fallback

def test_ollama_custom_models():
    with patch('services.llm_service.settings') as mock_settings:
        mock_settings.LITELLM_BASE_URL = "http://localhost:4000/v1"
        mock_settings.LITELLM_API_KEY = ""
        mock_settings.OLLAMA_CHAT_MODEL = "chat-model"
        mock_settings.OLLAMA_SUMMARIZATION_MODEL = "sum-model"
        mock_settings.OLLAMA_ENTITY_MODEL = "ent-model"
        mock_settings.OLLAMA_CLASSIFICATION_MODEL = "class-model"
        mock_settings.OLLAMA_EMBEDDING_MODEL = "embed-model"

        provider = OllamaProvider()
        assert provider.chat_model == "chat-model"
        assert provider.summarization_model == "sum-model"
        assert provider.entity_model == "ent-model"
        assert provider.classification_model == "class-model"

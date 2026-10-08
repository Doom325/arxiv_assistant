import pytest
from unittest.mock import MagicMock, patch
from services.llm_service import GeminiProvider, OllamaProvider, get_llm_service

@pytest.fixture
def gemini_provider():
    with patch('services.llm_service.genai.Client'):
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
        mock_settings.LLM_CHAT_MODEL = "chat-model"
        mock_settings.LLM_SUMMARIZATION_MODEL = None
        mock_settings.LLM_ENTITY_MODEL = None
        mock_settings.LLM_CLASSIFICATION_MODEL = None
        mock_settings.LLM_EMBEDDING_MODEL = "embed-model"

        provider = OllamaProvider()
        assert provider.chat_model == "chat-model"
        assert provider.summarization_model == "chat-model"  # Fallback
        assert provider.entity_model == "chat-model"         # Fallback
        assert provider.classification_model == "chat-model" # Fallback

def test_ollama_custom_models():
    with patch('services.llm_service.settings') as mock_settings:
        mock_settings.LITELLM_BASE_URL = "http://localhost:4000/v1"
        mock_settings.LITELLM_API_KEY = ""
        mock_settings.LLM_CHAT_MODEL = "chat-model"
        mock_settings.LLM_SUMMARIZATION_MODEL = "sum-model"
        mock_settings.LLM_ENTITY_MODEL = "ent-model"
        mock_settings.LLM_CLASSIFICATION_MODEL = "class-model"
        mock_settings.LLM_EMBEDDING_MODEL = "embed-model"

        provider = OllamaProvider()
        assert provider.chat_model == "chat-model"
        assert provider.summarization_model == "sum-model"
        assert provider.entity_model == "ent-model"
        assert provider.classification_model == "class-model"


@patch('requests.post')
def test_ollama_summarize_text_with_model_override(mock_post, ollama_provider):
    """A non-None ``model`` override must be sent in the request payload."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        'choices': [{'message': {'content': 'override Summary'}}]
    }
    mock_response.raise_for_status.return_value = None
    mock_post.return_value = mock_response

    ollama_provider.summarize_text("text", model="custom/model:7b")

    assert mock_post.call_args.kwargs["json"]["model"] == "custom/model:7b"


def test_gemini_summarize_text_with_model_override(gemini_provider):
    mock_response = MagicMock()
    mock_response.text = "ok"
    gemini_provider.client.models.generate_content.return_value = mock_response

    gemini_provider.summarize_text("text", model="gemini-2.5-pro")

    kwargs = gemini_provider.client.models.generate_content.call_args.kwargs
    assert kwargs["model"] == "gemini-2.5-pro"


def test_gemini_list_summarization_models(gemini_provider):
    models = gemini_provider.list_summarization_models()
    assert isinstance(models, list)
    assert gemini_provider.default_summarization_model() in models
    assert "gemini-3.8-flash" in models
    assert "gemini-3.7-flash" in models
    assert "gemini-2.0-flash" not in models


@patch('requests.get')
def test_ollama_list_summarization_models_from_gateway(mock_get):
    """Gateway /models response is unwrapped to a sorted list of ids."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "data": [
            {"id": "z-model"},
            {"id": "a-model"},
            {"id": "m-model"},
        ]
    }
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    provider = OllamaProvider()
    assert provider.list_summarization_models() == ["a-model", "m-model", "z-model"]


@patch('requests.get', side_effect=Exception("connection refused"))
def test_ollama_list_summarization_models_fallback(mock_get):
    """Gateway failure must fall back to configured model names, not raise."""
    with patch('services.llm_service.settings') as mock_settings:
        mock_settings.LITELLM_BASE_URL = "http://localhost:4000/v1"
        mock_settings.LITELLM_API_KEY = ""
        mock_settings.LLM_CHAT_MODEL = "chat-model"
        mock_settings.LLM_SUMMARIZATION_MODEL = "sum-model"
        mock_settings.LLM_ENTITY_MODEL = None
        mock_settings.LLM_CLASSIFICATION_MODEL = "class-model"
        mock_settings.LLM_EMBEDDING_MODEL = "embed-model"

        provider = OllamaProvider()
        models = provider.list_summarization_models()
        assert models[0] == "sum-model"  # ordering preserves precedence
        assert "chat-model" in models
        assert "class-model" in models


@patch('requests.post')
def test_ollama_summarize_text_default_temperature(mock_post, ollama_provider):
    """When temperature is not specified, payload uses the 0.3 default."""
    mock_response = MagicMock()
    mock_response.json.return_value = {'choices': [{'message': {'content': 'ok'}}]}
    mock_response.raise_for_status.return_value = None
    mock_post.return_value = mock_response

    ollama_provider.summarize_text("text")
    assert mock_post.call_args.kwargs["json"]["temperature"] == 0.3


@patch('requests.post')
def test_ollama_summarize_text_with_temperature_override(mock_post, ollama_provider):
    """Caller-supplied temperature wins."""
    mock_response = MagicMock()
    mock_response.json.return_value = {'choices': [{'message': {'content': 'ok'}}]}
    mock_response.raise_for_status.return_value = None
    mock_post.return_value = mock_response

    ollama_provider.summarize_text("text", temperature=0.7)
    assert mock_post.call_args.kwargs["json"]["temperature"] == 0.7


def test_get_summarization_provider_routes_gemini_model_to_gemini():
    """A model from the curated Gemini list must route to GeminiProvider."""
    from services import llm_service as svc
    with patch('services.llm_service.GeminiProvider') as MockG, \
         patch('services.llm_service.OllamaProvider') as MockO:
        svc._gemini_summarization_provider = None
        svc._local_summarization_provider = None

        _, name = svc.get_summarization_provider(svc._GEMINI_SUMMARIZATION_MODELS[0])
        assert name == "gemini"
        MockG.assert_called_once()
        MockO.assert_not_called()


def test_get_summarization_provider_routes_unknown_model_to_local():
    """A model that's not in the Gemini list must route to OllamaProvider (gateway)."""
    from services import llm_service as svc
    with patch('services.llm_service.GeminiProvider') as MockG, \
         patch('services.llm_service.OllamaProvider') as MockO:
        svc._gemini_summarization_provider = None
        svc._local_summarization_provider = None

        _, name = svc.get_summarization_provider("gemma3:27b")
        assert name == "local"
        MockO.assert_called_once()
        MockG.assert_not_called()

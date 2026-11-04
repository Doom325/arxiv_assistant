import pytest
import requests
from unittest.mock import MagicMock, patch
from services.llm_service import (
    GeminiProvider,
    NvidiaProvider,
    OllamaProvider,
    ProviderError,
    _is_retryable_status,
    get_llm_service,
)

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
    """A model that's not in the Gemini or Nvidia list must route to OllamaProvider (gateway)."""
    from services import llm_service as svc
    with patch('services.llm_service.GeminiProvider') as MockG, \
         patch('services.llm_service.OllamaProvider') as MockO, \
         patch('services.llm_service.NvidiaProvider') as MockN:
        svc._gemini_summarization_provider = None
        svc._local_summarization_provider = None
        svc._nvidia_summarization_provider = None

        _, name = svc.get_summarization_provider("gemma3:27b")
        assert name == "local"
        MockO.assert_called_once()
        MockG.assert_not_called()
        MockN.assert_not_called()


def test_get_summarization_provider_routes_nvidia_model_to_nvidia():
    """A model in _NVIDIA_SUMMARIZATION_MODELS routes to NvidiaProvider."""
    from services import llm_service as svc
    with patch('services.llm_service.GeminiProvider') as MockG, \
         patch('services.llm_service.OllamaProvider') as MockO, \
         patch('services.llm_service.NvidiaProvider') as MockN:
        svc._gemini_summarization_provider = None
        svc._local_summarization_provider = None
        svc._nvidia_summarization_provider = None

        _, name = svc.get_summarization_provider(svc._NVIDIA_SUMMARIZATION_MODELS[0])
        assert name == "nvidia"
        MockN.assert_called_once()
        MockG.assert_not_called()
        MockO.assert_not_called()


def test_get_summarization_provider_explicit_provider_param():
    """Explicit provider param wins over model inference."""
    from services import llm_service as svc
    with patch('services.llm_service.NvidiaProvider') as MockN:
        svc._nvidia_summarization_provider = None
        _, name = svc.get_summarization_provider(model="custom-model", provider="nvidia")
        assert name == "nvidia"
        MockN.assert_called_once()


def test_get_summarization_provider_custom_endpoint_param():
    """Custom endpoint param creates a dynamic provider with that base_url."""
    from services import llm_service as svc
    with patch('services.llm_service.NvidiaProvider') as MockN:
        _, name = svc.get_summarization_provider(
            model="meta/llama-3.3-70b-instruct",
            provider="nvidia",
            endpoint="https://my-nim.internal/v1"
        )
        assert name == "nvidia"
        MockN.assert_called_once_with(base_url="https://my-nim.internal/v1")


# ─────────────────────────────────────────────────────
# NVIDIA summarization error surfacing (regression for the generic
# "Summarization failed" that hid the real upstream cause).
# ─────────────────────────────────────────────────────

def _nvidia_provider() -> NvidiaProvider:
    return NvidiaProvider(base_url="https://integrate.api.nvidia.com/v1", api_key="nvapi-test")


def _http_error_response(status: int, body: dict) -> MagicMock:
    """A mock requests.Response whose raise_for_status raises an HTTPError."""
    err_response = MagicMock()
    err_response.status_code = status
    err_response.json.return_value = body
    resp = MagicMock()
    resp.raise_for_status.side_effect = requests.exceptions.HTTPError(response=err_response)
    return resp


def test_is_retryable_status_classifies_transient_vs_structural():
    assert _is_retryable_status(429) is True
    assert _is_retryable_status(408) is True
    assert _is_retryable_status(503) is True
    assert _is_retryable_status(500) is True
    assert _is_retryable_status(401) is False
    assert _is_retryable_status(403) is False
    assert _is_retryable_status(404) is False
    assert _is_retryable_status(400) is False
    assert _is_retryable_status(None) is False


@patch("requests.post")
def test_nvidia_http_429_raises_retryable_provider_error(mock_post):
    """A 429 must surface status + upstream message and be marked retryable."""
    mock_post.return_value = _http_error_response(
        429, {"error": {"message": "Rate limit exceeded"}}
    )
    with pytest.raises(ProviderError) as exc_info:
        _nvidia_provider().summarize_text("paper text")
    err = exc_info.value
    assert err.http_status == 429
    assert err.retryable is True
    assert err.provider == "nvidia"
    assert "429" in err.message and "Rate limit exceeded" in err.message


@patch("requests.post")
def test_nvidia_http_401_is_structural_not_retryable(mock_post):
    """A 401 (bad key) is structural: surfaced, but not flagged for retry."""
    mock_post.return_value = _http_error_response(
        401, {"error": {"message": "invalid API key"}}
    )
    with pytest.raises(ProviderError) as exc_info:
        _nvidia_provider().summarize_text("paper text")
    err = exc_info.value
    assert err.http_status == 401
    assert err.retryable is False
    assert "invalid API key" in err.message


@patch("requests.post")
def test_nvidia_http_404_model_not_found_surfaced(mock_post):
    mock_post.return_value = _http_error_response(
        404, {"detail": "model 'nvidia/bogus' not found"}
    )
    with pytest.raises(ProviderError) as exc_info:
        _nvidia_provider().summarize_text("paper text")
    err = exc_info.value
    assert err.http_status == 404
    assert err.retryable is False
    assert "not found" in err.message


@patch("requests.post")
def test_nvidia_http_500_is_retryable(mock_post):
    mock_post.return_value = _http_error_response(500, {"error": {"message": "server error"}})
    with pytest.raises(ProviderError) as exc_info:
        _nvidia_provider().summarize_text("paper text")
    assert exc_info.value.http_status == 500
    assert exc_info.value.retryable is True


@patch("requests.post", side_effect=requests.exceptions.Timeout("read timed out"))
def test_nvidia_timeout_raises_retryable_provider_error(mock_post):
    with pytest.raises(ProviderError) as exc_info:
        _nvidia_provider().summarize_text("paper text")
    err = exc_info.value
    assert err.retryable is True
    assert err.http_status is None
    assert "timed out" in err.message.lower()


@patch("requests.post", side_effect=requests.exceptions.ConnectionError("refused"))
def test_nvidia_connection_error_raises_retryable_provider_error(mock_post):
    with pytest.raises(ProviderError) as exc_info:
        _nvidia_provider().summarize_text("paper text")
    assert exc_info.value.retryable is True
    assert "connection" in exc_info.value.message.lower()


@patch("requests.post")
def test_nvidia_empty_content_raises_provider_error(mock_post):
    """An empty model response must be a failure, not a blank 'success'."""
    resp = MagicMock()
    resp.raise_for_status.return_value = None
    resp.json.return_value = {"choices": [{"message": {"content": "   "}}]}
    mock_post.return_value = resp
    with pytest.raises(ProviderError) as exc_info:
        _nvidia_provider().summarize_text("paper text")
    assert "empty" in exc_info.value.message.lower()
    assert exc_info.value.retryable is True


@patch("requests.post")
def test_nvidia_malformed_response_raises_provider_error(mock_post):
    """A response missing 'choices' must become a clear ProviderError, not a
    cryptic KeyError bubbling up as 'Summarization failed: 'choices''."""
    resp = MagicMock()
    resp.raise_for_status.return_value = None
    resp.json.return_value = {"unexpected": "shape"}
    mock_post.return_value = resp
    with pytest.raises(ProviderError) as exc_info:
        _nvidia_provider().summarize_text("paper text")
    assert exc_info.value.provider == "nvidia"
    assert "unexpected" in exc_info.value.message.lower()


@patch("requests.post")
def test_nvidia_reasoning_content_fallback_still_returns(mock_post):
    """Empty content but populated reasoning_content is a valid summary."""
    resp = MagicMock()
    resp.raise_for_status.return_value = None
    resp.json.return_value = {
        "choices": [{"message": {"content": "", "reasoning_content": "Reasoned summary"}}]
    }
    mock_post.return_value = resp
    assert _nvidia_provider().summarize_text("paper text") == "Reasoned summary"


@patch("requests.post")
def test_nvidia_surfaced_error_never_leaks_key_or_endpoint(mock_post):
    """A surfaced ProviderError message must never contain the API key,
    'Authorization', or the base URL/host — on any failure path.

    The no-leak property currently holds by construction (messages are built
    from status + parsed response body; str(e) is surfaced on no path). This
    locks it in: if a future edit reintroduces str(e) on, say, the timeout
    path, the raw requests message would carry the endpoint (sk-local on the
    LiteLLM path leaks analogously) and this test would fail.
    """
    secret_key = "nvapi-SUPERSECRETKEY123"
    secret_host = "secret-nim.internal"
    provider = NvidiaProvider(base_url=f"https://{secret_host}/v1", api_key=secret_key)

    def _assert_clean(message: str) -> None:
        assert secret_key not in message
        assert secret_host not in message
        assert "Authorization" not in message

    # HTTP failures: the surfaced message is the parsed body, not str(e).
    for status in (429, 500, 401, 404):
        mock_post.side_effect = None
        mock_post.return_value = _http_error_response(status, {"error": {"message": "upstream said no"}})
        with pytest.raises(ProviderError) as exc_info:
            provider.summarize_text("paper text")
        _assert_clean(exc_info.value.message)

    # Network failures: the raw exception string carries the endpoint, but the
    # surfaced message must be the generic, host-free phrasing.
    for exc in (
        requests.exceptions.Timeout(f"HTTPSConnectionPool(host='{secret_host}'): read timed out"),
        requests.exceptions.ConnectionError(f"cannot connect to https://{secret_host}/v1"),
    ):
        mock_post.return_value = None
        mock_post.side_effect = exc
        with pytest.raises(ProviderError) as exc_info:
            provider.summarize_text("paper text")
        _assert_clean(exc_info.value.message)
    mock_post.side_effect = None

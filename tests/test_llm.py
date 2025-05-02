import pytest
from unittest.mock import MagicMock, patch
import google.generativeai as genai
from google.generativeai.types import GenerateContentResponse, Part, PromptFeedback, BlockReason

# Assuming GeminiClient is in src/llm/gemini.py
from src.llm.gemini import GeminiClient
from src.config import settings

# Mock the genai.configure call
@patch('google.generativeai.configure')
def test_gemini_client_initialization(mock_configure):
    """Tests successful initialization of GeminiClient."""
    # Mock settings to provide an API key
    with patch('src.llm.gemini.settings') as mock_settings:
        mock_settings.GEMINI_API_KEY = "dummy_api_key"
        client = GeminiClient()
        mock_configure.assert_called_once_with(api_key="dummy_api_key")
        assert isinstance(client.model, genai.GenerativeModel) # Check if model is initialized

@patch('google.generativeai.configure')
def test_gemini_client_initialization_no_api_key(mock_configure):
    """Tests initialization failure when no API key is provided."""
    with patch('src.llm.gemini.settings') as mock_settings:
        mock_settings.GEMINI_API_KEY = None # Simulate no API key in settings
        with pytest.raises(ValueError, match="Gemini API key not provided or found in settings."):
            GeminiClient()
        mock_configure.assert_not_called()

@patch('google.generativeai.configure')
@patch('google.generativeai.GenerativeModel')
def test_gemini_client_generate_response_non_streaming_success(mock_generative_model, mock_configure):
    """Tests successful non-streaming response generation."""
    # Configure the mock model instance
    mock_model_instance = MagicMock()
    mock_generative_model.return_value = mock_model_instance

    # Configure the mock response
    mock_response = MagicMock(spec=GenerateContentResponse)
    mock_response.parts = [MagicMock(spec=Part, text="Generated response text.")]
    mock_response.prompt_feedback = None # Simulate no feedback/blocking
    mock_model_instance.generate_content.return_value = mock_response

    with patch('src.llm.gemini.settings') as mock_settings:
        mock_settings.GEMINI_API_KEY = "dummy_api_key"
        client = GeminiClient()

    prompt = "Test prompt"
    response = client.generate_response(prompt, stream=False)

    mock_model_instance.generate_content.assert_called_once_with(prompt, stream=False)
    assert response == "Generated response text."

@patch('google.generativeai.configure')
@patch('google.generativeai.GenerativeModel')
def test_gemini_client_generate_response_non_streaming_blocked(mock_generative_model, mock_configure):
    """Tests non-streaming response handling when the response is blocked."""
    mock_model_instance = MagicMock()
    mock_generative_model.return_value = mock_model_instance

    mock_response = MagicMock(spec=GenerateContentResponse)
    mock_response.parts = [] # Simulate no parts
    mock_response.prompt_feedback = MagicMock(spec=PromptFeedback, block_reason=BlockReason.SAFETY) # Simulate blocking
    mock_model_instance.generate_content.return_value = mock_response

    with patch('src.llm.gemini.settings') as mock_settings:
        mock_settings.GEMINI_API_KEY = "dummy_api_key"
        client = GeminiClient()

    prompt = "Test prompt"
    response = client.generate_response(prompt, stream=False)

    mock_model_instance.generate_content.assert_called_once_with(prompt, stream=False)
    assert "Error: Gemini response blocked or empty. Finish reason: SAFETY" in response

@patch('google.generativeai.configure')
@patch('google.generativeai.GenerativeModel')
def test_gemini_client_generate_response_streaming_success(mock_generative_model, mock_configure):
    """Tests successful streaming response generation."""
    mock_model_instance = MagicMock()
    mock_generative_model.return_value = mock_model_instance

    # Simulate a streaming response (a generator)
    def mock_streaming_response_generator():
        chunk1 = MagicMock(spec=GenerateContentResponse)
        chunk1.parts = [MagicMock(spec=Part, text="Chunk 1 ")]
        yield chunk1
        chunk2 = MagicMock(spec=GenerateContentResponse)
        chunk2.parts = [MagicMock(spec=Part, text="Chunk 2.")]
        yield chunk2

    mock_model_instance.generate_content.return_value = mock_streaming_response_generator()

    with patch('src.llm.gemini.settings') as mock_settings:
        mock_settings.GEMINI_API_KEY = "dummy_api_key"
        client = GeminiClient()

    prompt = "Test prompt"
    response_generator = client.generate_response(prompt, stream=True)

    mock_model_instance.generate_content.assert_called_once_with(prompt, stream=True)

    # Consume the generator and check the output
    chunks = list(response_generator)
    assert chunks == ["Chunk 1 ", "Chunk 2."]

@patch('google.generativeai.configure')
@patch('google.generativeai.GenerativeModel')
def test_gemini_client_generate_response_streaming_error(mock_generative_model, mock_configure):
    """Tests streaming response handling when an error occurs during streaming."""
    mock_model_instance = MagicMock()
    mock_generative_model.return_value = mock_model_instance

    # Simulate a streaming response that raises an exception
    def mock_streaming_response_generator_with_error():
        chunk1 = MagicMock(spec=GenerateContentResponse)
        chunk1.parts = [MagicMock(spec=Part, text="Chunk 1 ")]
        yield chunk1
        raise Exception("Simulated streaming error")

    mock_model_instance.generate_content.return_value = mock_streaming_response_generator_with_error()

    with patch('src.llm.gemini.settings') as mock_settings:
        mock_settings.GEMINI_API_KEY = "dummy_api_key"
        client = GeminiClient()

    prompt = "Test prompt"
    response_generator = client.generate_response(prompt, stream=True)

    mock_model_instance.generate_content.assert_called_once_with(prompt, stream=True)

    # Consume the generator and check the output
    chunks = list(response_generator)
    assert len(chunks) == 2 # Should yield the first chunk and then an error message
    assert chunks[0] == "Chunk 1 "
    assert "Error during streaming: Simulated streaming error" in chunks[1]

@patch('google.generativeai.configure')
@patch('google.generativeai.GenerativeModel')
def test_gemini_client_generate_response_empty_prompt_non_streaming(mock_generative_model, mock_configure):
    """Tests handling of empty prompt in non-streaming mode."""
    mock_model_instance = MagicMock()
    mock_generative_model.return_value = mock_model_instance

    with patch('src.llm.gemini.settings') as mock_settings:
        mock_settings.GEMINI_API_KEY = "dummy_api_key"
        client = GeminiClient()

    response = client.generate_response("", stream=False)

    mock_model_instance.generate_content.assert_not_called() # Should not call API for empty prompt
    assert response == "Error: Prompt cannot be empty."

@patch('google.generativeai.configure')
@patch('google.generativeai.GenerativeModel')
def test_gemini_client_generate_response_empty_prompt_streaming(mock_generative_model, mock_configure):
    """Tests handling of empty prompt in streaming mode."""
    mock_model_instance = MagicMock()
    mock_generative_model.return_value = mock_model_instance

    with patch('src.llm.gemini.settings') as mock_settings:
        mock_settings.GEMINI_API_KEY = "dummy_api_key"
        client = GeminiClient()

    response_generator = client.generate_response("", stream=True)

    mock_model_instance.generate_content.assert_not_called() # Should not call API for empty prompt

    # Consume the generator and check the output
    chunks = list(response_generator)
    assert chunks == ["Error: Prompt cannot be empty."]

# Assuming PromptTemplates is in src/llm/prompts.py
from src.llm.prompts import PromptTemplates

# --- Test PromptTemplates ---

def test_prompt_templates_qa_template():
    """Tests the optimized qa_template."""
    context = "This is some context."
    query = "What is the context?"
    prompt = PromptTemplates.qa_template(context, query)

    assert "Answer the following question based *only* on the provided context." in prompt
    assert 'If the answer is not in the context, state "I don\'t know."' in prompt # Check escaped quote
    assert "Context:\nThis is some context." in prompt
    assert "Question: What is the context?" in prompt
    assert "Answer:" in prompt
    # Ensure removed phrases are gone
    assert "You are a helpful assistant" not in prompt
    assert "Use the context below" not in prompt

def test_prompt_templates_summarize_template():
    """Tests the optimized summarize_template."""
    text = "This is a long text that needs to be summarized. It has multiple sentences."
    prompt = PromptTemplates.summarize_template(text)

    assert "Summarize the following text concisely and informatively." in prompt
    assert "Text:\nThis is a long text that needs to be summarized. It has multiple sentences." in prompt
    assert "Summary:" in prompt
    # Ensure removed phrases are gone
    assert "You are a helpful assistant" not in prompt

def test_prompt_templates_policy_analysis_template():
    """Tests the optimized policy_analysis_template."""
    context = "Policy document content."
    policy_query = "Analyze this policy."
    prompt = PromptTemplates.policy_analysis_template(context, policy_query)

    assert "*Only* using the provided policy document, as a policy expert, analyze the document to answer the following query." in prompt
    assert 'If the answer is not present, state "Information not found in the policy document."' in prompt
    assert "Policy Document:\nPolicy document content." in prompt
    assert "Query: Analyze this policy." in prompt
    assert "Analysis:" in prompt
     # Ensure removed phrases are gone
    assert "You are a policy expert" not in prompt # Check if original phrasing is gone
    assert "Use the policy document below" not in prompt

def test_prompt_templates_document_update_template():
    """Tests the optimized document_update_template."""
    original_text = "Original text."
    suggested_changes = "Suggested changes."
    context = "Surrounding context."
    prompt = PromptTemplates.document_update_template(original_text, suggested_changes, context)

    assert "Update the ORIGINAL TEXT with the SUGGESTED CHANGES, considering the CONTEXT for consistency and maintaining original style. Explain your REASONING." in prompt
    assert "ORIGINAL TEXT:\nOriginal text." in prompt
    assert "SUGGESTED CHANGES:\nSuggested changes." in prompt
    assert "CONTEXT:\nSurrounding context." in prompt
    assert "REVISED TEXT:" in prompt
    assert "REASONING:" in prompt
    # Ensure removed phrases are gone
    assert "You are an AI assistant" not in prompt
    assert "Review the ORIGINAL TEXT" not in prompt # Check if original phrasing is gone

def test_prompt_templates_consistency_check_template():
    """Tests the optimized consistency_check_template."""
    document_section = "Section content."
    related_sections = "Related content."
    prompt = PromptTemplates.consistency_check_template(document_section, related_sections)

    assert "Compare the DOCUMENT SECTION with the RELATED SECTIONS for consistency." in prompt
    assert "Identify and explain any inconsistencies in information, terminology, or style. Suggest resolutions." in prompt
    assert "DOCUMENT SECTION:\nSection content." in prompt
    assert "RELATED SECTIONS:\nRelated content." in prompt
    assert "Consistency Check Results:" in prompt
    # Ensure removed phrases are gone
    assert "You are an AI assistant" not in prompt
    assert "Review the DOCUMENT SECTION" not in prompt # Check if original phrasing is gone
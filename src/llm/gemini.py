import google.generativeai as genai
from typing import List, Dict, Any, Optional
from ..config import settings # Assuming config is in src/

class GeminiClient:
    """
    A wrapper class for interacting with the Google Gemini API.
    Handles API key configuration and provides methods for text generation.
    """
    def __init__(self, api_key: Optional[str] = None):
        """
        Initializes the Gemini client.

        Args:
            api_key: The Google Gemini API key. If None, it attempts to load
                     from the settings (which loads from .env).
        """
        self.api_key = api_key or settings.GEMINI_API_KEY
        if not self.api_key:
            raise ValueError("Gemini API key not provided or found in settings.")

        try:
            genai.configure(api_key=self.api_key)
            # Initialize the GenerativeModel - choose an appropriate model
            # For free tier, 'gemini-pro' is a common choice for text generation
            self.model = genai.GenerativeModel('gemini-pro')
            print("Gemini client initialized successfully with model 'gemini-pro'.")
        except Exception as e:
            print(f"Error configuring Gemini client: {e}")
            raise

    def generate_response(self, prompt: str, stream: bool = False):
        """
        Generates a text response from the Gemini model based on the prompt.
        Supports streaming responses.

        Args:
            prompt: The input prompt string.
            stream: If True, stream the response chunks. If False, return the full response text.

        Returns:
            If stream is True, a generator yielding text chunks.
            If stream is False, the full generated text response string, or an error message.
        """
        if not prompt:
            if stream:
                def empty_generator():
                    yield "Error: Prompt cannot be empty."
                return empty_generator()
            else:
                return "Error: Prompt cannot be empty."

        try:
            response = self.model.generate_content(prompt, stream=stream)

            if stream:
                def streaming_generator():
                    try:
                        for chunk in response:
                            if chunk.parts:
                                yield chunk.text
                            # Add more granular error/block handling for streaming chunks if needed
                    except Exception as e:
                        print(f"Error during streaming response from Gemini: {e}")
                        yield f"\nError during streaming: {e}"
                return streaming_generator()
            else:
                # Non-streaming response handling
                if response.parts:
                    return response.text
                else:
                    # Handle cases where the response might be blocked or empty
                    print(f"Warning: Gemini non-streaming response did not contain text parts. Response: {response}")
                    block_reason = response.prompt_feedback.block_reason if response.prompt_feedback else 'N/A'
                    return f"Error: Gemini response blocked or empty. Finish reason: {block_reason}"

        except Exception as e:
            print(f"Error generating response from Gemini: {e}")
            if stream:
                def error_generator():
                    yield f"Error: Failed to generate response from Gemini. {e}"
                return error_generator()
            else:
                return f"Error: Failed to generate response from Gemini. {e}"

# Example Usage
if __name__ == "__main__":
    print("Attempting to initialize GeminiClient...")
    # Ensure you have your GEMINI_API_KEY set in your .env file
    # or provide it directly: GeminiClient(api_key="YOUR_API_KEY")
    try:
        client = GeminiClient()
        print("\nAttempting to generate a simple non-streaming response...")
        test_prompt_non_stream = "Explain the concept of Retrieval-Augmented Generation (RAG) in one sentence."
        response_non_stream = client.generate_response(test_prompt_non_stream, stream=False)
        print(f"\nPrompt (Non-streaming): {test_prompt_non_stream}")
        print(f"Response (Non-streaming): {response_non_stream}")

        print("\nAttempting to generate a simple streaming response...")
        test_prompt_stream = "Tell me a short story about a brave knight."
        print(f"\nPrompt (Streaming): {test_prompt_stream}")
        print("Response (Streaming):")
        for chunk in client.generate_response(test_prompt_stream, stream=True):
            print(chunk, end="", flush=True)
        print("\n") # Add a newline at the end

        print("\nAttempting to generate response for an empty prompt (non-streaming)...")
        empty_response_non_stream = client.generate_response("", stream=False)
        print(f"Response for empty prompt (non-streaming): {empty_response_non_stream}")

        print("\nAttempting to generate response for an empty prompt (streaming)...")
        print("Response for empty prompt (streaming):")
        for chunk in client.generate_response("", stream=True):
             print(chunk, end="", flush=True)
        print("\n") # Add a newline at the end


    except ValueError as ve:
        print(f"\nInitialization Error: {ve}")
        print("Please ensure your GEMINI_API_KEY is set in the .env file.")
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")
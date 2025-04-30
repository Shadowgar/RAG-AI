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

    def generate_response(self, prompt: str) -> str:
        """
        Generates a text response from the Gemini model based on the prompt.

        Args:
            prompt: The input prompt string.

        Returns:
            The generated text response string, or an error message if generation fails.
        """
        if not prompt:
            return "Error: Prompt cannot be empty."

        try:
            response = self.model.generate_content(prompt)
            # Access the text part of the response
            # Handle potential issues if the response doesn't contain text
            if response.parts:
                 return response.text
            else:
                 # Handle cases where the response might be blocked or empty
                 print(f"Warning: Gemini response did not contain text parts. Response: {response}")
                 return f"Error: Gemini response blocked or empty. Finish reason: {response.prompt_feedback.block_reason if response.prompt_feedback else 'N/A'}"

        except Exception as e:
            print(f"Error generating response from Gemini: {e}")
            return f"Error: Failed to generate response from Gemini. {e}"

# Example Usage
if __name__ == "__main__":
    print("Attempting to initialize GeminiClient...")
    # Ensure you have your GEMINI_API_KEY set in your .env file
    # or provide it directly: GeminiClient(api_key="YOUR_API_KEY")
    try:
        client = GeminiClient()
        print("\nAttempting to generate a simple response...")
        test_prompt = "Explain the concept of Retrieval-Augmented Generation (RAG) in one sentence."
        response = client.generate_response(test_prompt)
        print(f"\nPrompt: {test_prompt}")
        print(f"Response: {response}")

        print("\nAttempting to generate response for an empty prompt...")
        empty_response = client.generate_response("")
        print(f"Response for empty prompt: {empty_response}")

    except ValueError as ve:
        print(f"\nInitialization Error: {ve}")
        print("Please ensure your GEMINI_API_KEY is set in the .env file.")
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")
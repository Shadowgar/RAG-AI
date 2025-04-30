class PromptTemplates:
    """
    A class to store and manage prompt templates for different tasks.
    These templates can be customized and used with the Gemini API.
    """

    @staticmethod
    def qa_template(context: str, query: str) -> str:
        """
        Generates a prompt for question answering based on a given context.

        Args:
            context: The context text to answer the question from.
            query: The question to be answered.

        Returns:
            A formatted prompt string.
        """
        return f"""
        You are a helpful assistant that answers questions based on the provided context.
        Use the context below to answer the query. If the answer is not found in the context,
        say that you don't know, do not make up an answer.

        Context:
        {context}

        Query: {query}

        Answer:
        """

    @staticmethod
    def summarize_template(text: str) -> str:
        """
        Generates a prompt for summarizing a given text.

        Args:
            text: The text to be summarized.

        Returns:
            A formatted prompt string.
        """
        return f"""
        You are a helpful assistant that summarizes the given text.
        Provide a concise and informative summary of the following text:

        Text:
        {text}

        Summary:
        """

    @staticmethod
    def policy_analysis_template(context: str, policy_query: str) -> str:
        """
        Generates a prompt for analyzing a policy document based on a specific query.

        Args:
            context: The policy document text.
            policy_query: The specific question or analysis to perform on the policy.

        Returns:
            A formatted prompt string.
        """
        return f"""
        You are a policy expert that analyzes policy documents based on specific queries.
        Use the policy document below to answer the query. If the answer is not found in the document,
        say that you don't know, do not make up an answer.

        Policy Document:
        {context}

        Query: {policy_query}

        Analysis:
        """

# Example Usage (basic)
if __name__ == "__main__":
    # Example context and query
    example_context = "The company's policy on remote work states that employees can work remotely up to 3 days a week."
    example_query = "How many days a week can employees work remotely?"

    # Generate a QA prompt
    qa_prompt = PromptTemplates.qa_template(example_context, example_query)
    print("QA Prompt:\n", qa_prompt)

    # Generate a summary prompt
    example_text = "This is a long piece of text that needs to be summarized. It contains multiple sentences and key points that should be included in the summary."
    summary_prompt = PromptTemplates.summarize_template(example_text)
    print("\nSummary Prompt:\n", summary_prompt)

    # Generate a policy analysis prompt
    example_policy_query = "What are the requirements for requesting a leave of absence?"
    policy_analysis_prompt = PromptTemplates.policy_analysis_template(example_context, example_policy_query)
    print("\nPolicy Analysis Prompt:\n", policy_analysis_prompt)
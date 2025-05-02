class PromptTemplates:
    """
    A class to store and manage prompt templates for different tasks.
    These templates are designed with token efficiency and clarity for the Gemini API.
    """

    @staticmethod
    def qa_template(context: str, query: str) -> str:
        """
        Generates a prompt for question answering based on a given context.
        Focuses on direct answers from provided text.
        # Optimization: Concise instructions, direct question format.
        """
        # Keep prompt short and focused on direct answer extraction.
        return f"""Answer the following question based *only* on the provided context.
If the answer is not in the context, state "I don't know."

Context:
{context}

Question: {query}

Answer:"""

    @staticmethod
    def summarize_template(text: str) -> str:
        """
        Generates a prompt for summarizing a given text.
        Aims for a concise and informative summary.
        # Optimization: Removed redundant phrases.
        """
        # Removed "You are a helpful assistant" - implicit role.
        return f"""Summarize the following text concisely and informatively.

Text:
{text}

Summary:"""

    @staticmethod
    def policy_analysis_template(context: str, policy_query: str) -> str:
        """
        Generates a prompt for analyzing a policy document based on a specific query.
        Directs the model to act as a policy expert and use only the provided document.
        # Optimization: Emphasized role and source restriction.
        """
        # More direct instructions, stronger emphasis on using only the document.
        return f"""*Only* using the provided policy document, as a policy expert, analyze the document to answer the following query.
If the answer is not present, state "Information not found in the policy document."

Policy Document:
{context}

Query: {policy_query}

Analysis:"""

    @staticmethod
    def document_update_template(original_text: str, suggested_changes: str, context: str) -> str:
        """
        Generates a prompt for reviewing and applying suggested changes to a document section.
        Emphasizes consistency and explanation.
        # Optimization: Removed redundant phrases, clarified task.
        """
        # Clear task, direct instructions, specific output requirements.
        return f"""Update the ORIGINAL TEXT with the SUGGESTED CHANGES, considering the CONTEXT for consistency and maintaining original style. Explain your REASONING.

ORIGINAL TEXT:
{original_text}

SUGGESTED CHANGES:
{suggested_changes}

CONTEXT:
{context}

REVISED TEXT:
REASONING:"""

    @staticmethod
    def consistency_check_template(document_section: str, related_sections: str) -> str:
        """
        Generates a prompt for checking the consistency of a document section
        against related sections.
        Focuses on identifying and explaining inconsistencies.
        # Optimization: Streamlined instructions, direct output request.
        """
        # Direct comparison task, clear output requirements.
        return f"""Compare the DOCUMENT SECTION with the RELATED SECTIONS for consistency.
Identify and explain any inconsistencies in information, terminology, or style. Suggest resolutions.

DOCUMENT SECTION:
{document_section}

RELATED SECTIONS:
{related_sections}

Consistency Check Results:"""

# Example Usage (basic)
if __name__ == "__main__":
    # Example context and query
    example_context = "The company's policy on remote work states that employees can work remotely up to 3 days a week."
    example_query = "How many days a week can employees work remotely?"

    # Generate a QA prompt
    qa_prompt = PromptTemplates.qa_template(example_context, example_query)
    print("QA Prompt:\\n", qa_prompt)

    # Generate a summary prompt
    example_text = "This is a long piece of text that needs to be summarized. It contains multiple sentences and key points that should be included in the summary."
    summary_prompt = PromptTemplates.summarize_template(example_text)
    print("\\nSummary Prompt:\\n", summary_prompt)

    # Generate a policy analysis prompt
    example_policy_query = "What are the requirements for requesting a leave of absence?"
    policy_analysis_prompt = PromptTemplates.policy_analysis_template(example_context, example_query)
    print("\\nPolicy Analysis Prompt:\\n", policy_analysis_prompt)

    # Example document update prompt
    original = "Employees must submit requests 2 weeks in advance."
    suggested = "Requests should be submitted 10 business days prior."
    context_update = "The new policy aims to streamline the request process."
    update_prompt = PromptTemplates.document_update_template(original, suggested, context_update)
    print("\\nDocument Update Prompt:\\n", update_prompt)

    # Example consistency check prompt
    section_to_check = "Employees are allowed 15 vacation days per year."
    related_sections_text = "Section 3.1: Vacation accrual is 1.25 days per month.\\nSection 4.5: Unused vacation days can be rolled over, up to a maximum of 5 days."
    consistency_prompt = PromptTemplates.consistency_check_template(section_to_check, related_sections_text)
    print("\\nConsistency Check Prompt:\\n", consistency_prompt)
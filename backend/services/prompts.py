
# Prompt Centralization Service

SUMMARIZATION_PROMPT = """Please provide a structured and detailed summary of the following research paper.
Format the response with the following clearly labeled sections:

1. **Core Problem**: What specific problem is this paper trying to solve?
2. **Key Innovation**: What is the main novelty or contribution (the "aha!" moment)?
3. **Methodology**: Briefly explain the technical approach.
4. **Key Results**: What were the quantitative or qualitative findings?

Text:
{text}"""

SUMMARIZATION_PROMPT_MLX = """<start_of_turn>user
You are an expert researcher and teacher.
Please provide a comprehensive summary of the research paper provided below.
The summary should be educational and explain the core concepts, methodology, and results to a graduate student.

--- BEGIN PAPER ---
{text}
--- END PAPER ---

**Instruction:**
Based on the paper content above, write a structured and detailed summary.
Format the response with the following clearly labeled sections:

1. **Core Problem**: What specific problem is this paper trying to solve?
2. **Key Innovation**: What is the main novelty or contribution (the "aha!" moment)?
3. **Methodology**: Briefly explain the technical approach.
4. **Key Results**: What were the quantitative or qualitative findings?

Keep the tone educational and suitable for a researcher.
<end_of_turn>
<start_of_turn>model
"""

RETRIEVAL_PROMPT = "title: {title} | document: {content}"

CLUSTERING_PROMPT = "task_type: clustering | query: {content}"

def get_retrieval_prompt(title: str, content: str) -> str:
    return RETRIEVAL_PROMPT.format(title=title, content=content)

def get_clustering_prompt(content: str) -> str:
    return CLUSTERING_PROMPT.format(content=content)

PROMPT_REGISTRY = {
    "gemini_retrieval_v1": {
        "template": RETRIEVAL_PROMPT,
        "version": "1.0.0"
    },
    "gemini_clustering_v1": {
        "template": CLUSTERING_PROMPT,
        "version": "1.0.0"
    }
}

from typing import List
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import BaseMessage

from backend.agents.triage import InvestigationRequest
from backend.agents.evidence import Evaluation
from backend.llm import build_llm, traced_config
from backend.observability.context import correlation_scope

class FilePatch(BaseModel):
    """
    A minimal code change using exact Search and Replace.
    """
    file_path: str = Field(description="The path to the file to modify")
    original_snippet: str = Field(description="The EXACT string to replace. Must include all original whitespace and indentation. Must be unique in the file.")
    new_snippet: str = Field(description="The new string to insert in its place.")
    explanation: str = Field(description="Why this minimal change fixes the root cause.")

class PatchResponse(BaseModel):
    patches: List[FilePatch]

class PatchAgent:
    """
    Generates minimal, syntactically valid patches based on the investigation history
    and confirmed root cause.
    """
    def __init__(self, model_name: str = "meta-llama/llama-3.1-8b-instruct:free"):
        self.llm = build_llm(model_name=model_name, temperature=0)
        self.structured_llm = self.llm.with_structured_output(PatchResponse)
        
    def generate_patch(self, request: InvestigationRequest, root_cause: Evaluation, history_messages: List[BaseMessage], previous_failures: List[str] = None) -> PatchResponse:
        system_prompt = """You are an Expert Software Engineer fixing a bug.
Your job is to generate a precise code patch to fix the identified root cause.
You MUST follow the rule: "smallest change that fixes the root cause over rewriting the whole component."

Use the Search & Replace format. The `original_snippet` MUST exactly match the text in the file, including all leading whitespace, newlines, and indentation.

Bug Context:
Type: {bug_type}
Issue: {observed_behavior}

Confirmed Root Cause:
{root_cause_explanation}

Below is the conversation history of the Investigation Agent, which contains the tool outputs (including the file contents).
Read the file contents carefully to ensure your `original_snippet` matches EXACTLY.
"""
        if previous_failures:
            system_prompt += "\nWARNING: Your previous attempts to patch this bug FAILED validation.\n"
            system_prompt += "Here are the errors from your previous attempts:\n"
            system_prompt += "\n---\n".join(previous_failures)
            system_prompt += "\n\nYou MUST analyze these failures and provide a DIFFERENT, corrected patch that fixes these errors.\n"

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "Conversation History:\n{history}\n\nGenerate the patch.")
        ])
        
        # We format the chat history so the LLM can read the file contents that were searched
        formatted_history = "\n".join([f"{msg.type.upper()}: {msg.content}" for msg in history_messages])
        
        # We format the root cause explanation
        rc_explanation = "\n".join(root_cause.supporting_evidence)
        
        chain = prompt | self.structured_llm
        with correlation_scope(node="patch"):
            result = chain.invoke({
                "bug_type": request.bug_type,
                "observed_behavior": request.observed_behavior,
                "root_cause_explanation": rc_explanation,
                "history": formatted_history
            }, config=traced_config())
        
        return result

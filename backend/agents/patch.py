import os
from typing import List
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import BaseMessage

from backend.agents.triage import InvestigationRequest
from backend.agents.evidence import Evaluation

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
    def __init__(self, model_name: str = "meta-llama/llama-3.1-8b-instruct"):
        self.llm = ChatOpenAI(
            model=model_name,
            base_url="https://openrouter.ai/api/v1",
            api_key=os.environ.get("OPENROUTER_API_KEY", ""),
            temperature=0
        )
        self.structured_llm = self.llm.with_structured_output(PatchResponse)
        
        # We format the root cause explanation
        rc_explanation = "\n".join(root_cause.supporting_evidence)
        
        chain = self.prompt | self.structured_llm
        result = chain.invoke({
            "bug_type": request.bug_type,
            "observed_behavior": request.observed_behavior,
            "root_cause_explanation": rc_explanation,
            "history": formatted_history
        })
        
        return result

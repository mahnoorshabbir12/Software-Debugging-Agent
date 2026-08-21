import os
from typing import Optional, List
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

class InvestigationRequest(BaseModel):
    """
    Structured representation of a software bug or issue.
    """
    bug_type: str = Field(description="The category of the bug (e.g., runtime_error, logical_error, syntax_error, unhandled_exception, configuration_error)")
    affected_endpoint: Optional[str] = Field(description="The API endpoint, UI view, or specific script affected, if applicable")
    suspected_area: str = Field(description="The architectural component or module likely responsible (e.g., database, auth, request_validation)")
    observed_behavior: str = Field(description="What the system is currently doing wrong")
    expected_behavior: str = Field(description="What the system should actually be doing. If the user doesn't specify, infer a logical default (e.g. 'Should return 200 OK without crashing')")
    constraints: List[str] = Field(default_factory=list, description="Any specific library versions, environment details, or constraints mentioned")

class TriageAgent:
    """
    The entry point of the debugging system.
    Converts a messy, natural-language bug report into a structured InvestigationRequest.
    """
    def __init__(self, model_name: str = "meta-llama/llama-3.1-8b-instruct"):
        # We use OpenRouter as our LLM provider
        self.llm = ChatOpenAI(
            model=model_name,
            base_url="https://openrouter.ai/api/v1",
            api_key=os.environ.get("OPENROUTER_API_KEY", ""),
            temperature=0
        )
        
        # Enforce the Pydantic schema
        self.structured_llm = self.llm.with_structured_output(InvestigationRequest)
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert Software Debugging Triage Agent.
Your job is to read an unstructured bug report from a user and extract the core details into a structured JSON payload.
If the user does not specify the 'expected_behavior', you MUST use your engineering knowledge to logically infer it. 
For example, if the user says 'POST /users returns 500', you should infer that 'POST /users should return 201 Created and successfully add a user'.

Bug Report:
"""),
            ("human", "{bug_report}")
        ])
        
    def triage(self, bug_report: str) -> InvestigationRequest:
        """
        Processes a bug report and returns a structured InvestigationRequest.
        """
        chain = self.prompt | self.structured_llm
        result = chain.invoke({"bug_report": bug_report})
        return result

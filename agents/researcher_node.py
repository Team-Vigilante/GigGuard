import json
import os
from typing import Dict, Any
from anthropic import Anthropic
from agents.chromadb_query import build_case_facts_string, query_knowledge_base

# PLACEHOLDER FOR PERSON 4'S GROUNDING PROMPT
# DO NOT FINALIZE OR REMOVE THIS UNTIL PERSON 4 PROVIDES THE TEXT!
GROUNDING_PROMPT = """
[PERSON 4 WILL PROVIDE THE EXACT ANTI-HALLUCINATION GROUNDING PROMPT HERE]
[DO NOT MODIFY THEIR RULES WHEN THEY PROVIDE IT]
"""

RESEARCHER_SYSTEM_PROMPT = f"""
You are the Legal Researcher Agent for GigGuard, a legal advocacy system 
for gig workers in India.

Your job is to analyze the worker's case facts strictly against the retrieved 
legal context and determine if there are any legal violations.

{{GROUNDING_PROMPT}}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
OUTPUT FORMAT — STRICT JSON ONLY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Return ONLY a valid JSON object. No prose. No markdown.
No code blocks. Nothing outside the JSON.

{{
  "violations": [
    {{
      "law": "Name of the law (e.g., Code on Social Security 2020)",
      "section": "Specific section number",
      "retrieved_text": "Exact quote from context used as basis",
      "violation_description": "Clear explanation of how the platform violated this"
    }}
  ],
  "case_strength": "STRONG|MODERATE|WEAK|INSUFFICIENT_BASIS",
  "confidence": 0.0 to 1.0,
  "worker_message": "A plain language explanation for the worker in a friendly tone."
}}
"""

def researcher_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Agent 2: Legal Researcher Node
    
    Uses RAG to find relevant legal provisions and analyzes the case
    facts against those provisions to determine legal violations.
    
    Args:
        state: The current LangGraph state (GigGuardState), must contain 'parsed_data'
        
    Returns:
        A dict containing 'legal_analysis' to update the state.
    """
    parsed_data = state.get("parsed_data", {})
    
    # 1. Build query string from parsed case facts
    case_facts_str = build_case_facts_string(parsed_data)
    
    # 2. Call ChromaDB query function
    retrieved_chunks = query_knowledge_base(case_facts_str, n_results=5)
    
    # Format retrieved chunks for the prompt
    context_str = json.dumps(retrieved_chunks, indent=2)
    
    # 3. Pass retrieved chunks to Claude
    client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    
    user_prompt = f"""
    Please analyze the following case based ONLY on the provided legal context.
    
    CASE FACTS:
    {json.dumps(parsed_data, indent=2)}
    
    RETRIEVED LEGAL CONTEXT:
    {context_str}
    """
    
    response = client.messages.create(
        model="claude-3-5-sonnet-latest",
        max_tokens=1500,
        temperature=0.0,
        system=RESEARCHER_SYSTEM_PROMPT,
        messages=[
            {"role": "user", "content": user_prompt}
        ]
    )
    
    try:
        response_text = response.content[0].text
        start_idx = response_text.find('{')
        end_idx = response_text.rfind('}') + 1
        json_str = response_text[start_idx:end_idx]
        
        legal_analysis = json.loads(json_str)
        
    except (json.JSONDecodeError, IndexError, AttributeError) as e:
        legal_analysis = {
            "violations": [],
            "case_strength": "INSUFFICIENT_BASIS",
            "confidence": 0.0,
            "worker_message": f"An error occurred during legal analysis: {str(e)}"
        }
        
    return {"legal_analysis": legal_analysis}

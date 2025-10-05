import json
import os
from typing import Dict, List

# Load intents from vibe_mapper.json
with open("vibe_mapper.json", "r") as f:
    VIBE_MAPPER = json.load(f)

INTENTS = list(VIBE_MAPPER.keys())

def extract_intent(query: str) -> str:
    """
    Extract intent from natural language query.
    
    First tries deterministic keyword matching, then falls back to LLM if available.
    
    Args:
        query: Natural language query (e.g., "quiet place to study")
        
    Returns:
        Intent string (e.g., "quiet_study")
        
    Examples:
        extract_intent("quiet place to study with outlets") -> "quiet_study"
        extract_intent("where can I play soccer near me") -> "sports"
        extract_intent("random gibberish") -> "quiet_study" (default)
    """
    query_lower = query.lower()
    
    # Deterministic keyword matching
    for intent, config in VIBE_MAPPER.items():
        keywords = config.get("keywords", [])
        if any(keyword in query_lower for keyword in keywords):
            return intent
    
    # LLM fallback (optional)
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        try:
            import openai
            client = openai.OpenAI(api_key=openai_key)
            
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": f"Return JSON only with intent field. Available intents: {INTENTS}"},
                    {"role": "user", "content": f"Query: '{query}'"}
                ],
                temperature=0.1
            )
            
            result = json.loads(response.choices[0].message.content)
            if "intent" in result and result["intent"] in INTENTS:
                return result["intent"]
        except Exception:
            pass  # Fall through to default
    
    # Default fallback
    return "unclear_intent"

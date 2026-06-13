import os

def call_llm(system_prompt: str, user_prompt: str, max_tokens: int = 1500, temperature: float = 0.0) -> str:
    """
    Unified LLM caller. Tries Groq first (for free tier), then Anthropic.
    """
    if os.environ.get("GROQ_API_KEY"):
        from groq import Groq
        client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=temperature,
            max_tokens=max_tokens
        )
        return response.choices[0].message.content
        
    elif os.environ.get("ANTHROPIC_API_KEY"):
        from anthropic import Anthropic
        client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
        response = client.messages.create(
            model="claude-3-5-sonnet-latest",
            max_tokens=max_tokens,
            temperature=temperature,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_prompt}
            ]
        )
        return response.content[0].text
        
    else:
        raise ValueError("No API key found! Set GROQ_API_KEY or ANTHROPIC_API_KEY.")

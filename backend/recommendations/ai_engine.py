"""
AI Recommendation Engine
=========================
Uses the Claude API (claude-haiku) to generate fresh, personalized
recommendations every time the user refreshes.

LEARNING — External API Calls in Django:
  Django views are just Python — you can call any external service from them.
  Here we call the Anthropic API synchronously (simple, fine for learning).
  In a production app you'd add caching and async handling, but this works great.

LEARNING — Structured Output from LLMs:
  LLMs return free-form text, but we need structured data (a list of dicts).
  The technique: instruct the model to return ONLY valid JSON, then parse it
  with json.loads(). We also validate the shape of each item before returning.
  If anything goes wrong, the caller falls back to the static engine.

SETUP:
  1. Install: pip install anthropic
  2. Set your API key as an environment variable before starting the server:
       export ANTHROPIC_API_KEY="sk-ant-..."
     (Get a key at https://console.anthropic.com/)
"""
import os
import json
import anthropic


def get_ai_recommendations(interests: list, remaining_budget: float) -> list:
    """
    Ask Claude to generate unique, personalized recommendations.

    Args:
        interests:        List of interest strings (e.g. ['fitness', 'dining'])
        remaining_budget: How much the user has left this month

    Returns:
        List of recommendation dicts with keys:
          title, description, estimated_cost, budget_tier, interest_category

    Raises:
        Exception if the API key is missing, the call fails, or JSON is unparseable.
        The caller (views.py) catches this and falls back to the static engine.
    """
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY environment variable is not set.")

    client = anthropic.Anthropic(api_key=api_key)

    # Give the model budget context so it knows which price ranges make sense
    if remaining_budget <= 0:
        budget_guidance = "The user has no budget remaining — suggest only free activities."
    elif remaining_budget < 25:
        budget_guidance = f"The user has ${remaining_budget:.0f} left. Suggest only free or very cheap options (under $25)."
    elif remaining_budget < 75:
        budget_guidance = f"The user has ${remaining_budget:.0f} left. Suggest affordable options under $75."
    elif remaining_budget < 200:
        budget_guidance = f"The user has ${remaining_budget:.0f} left. Mix budget-friendly and mid-range options (under $200)."
    else:
        budget_guidance = f"The user has ${remaining_budget:.0f} left. Include a variety of price ranges."

    interests_str = ', '.join(interests) if interests else 'dining, entertainment, outdoor'

    # LEARNING — Prompt Engineering:
    #   Being explicit about the output format (JSON schema, field names, example)
    #   dramatically improves reliability. The model knows exactly what to produce.
    prompt = f"""The user enjoys: {interests_str}
{budget_guidance}

Generate exactly 8 unique, specific activity or purchase recommendations.
Make them creative and varied — no generic suggestions.

Return ONLY a valid JSON array. No explanation, no markdown code fences, just the raw JSON.

Each object must have exactly these fields:
- "title": concise activity name (4-8 words)
- "description": 1-2 sentences, specific and motivating
- "estimated_cost": price range as a string, e.g. "$20 – $40" or "$0"
- "budget_tier": exactly one of "tier1" (under $25), "tier2" ($25–$75), "tier3" ($75–$200), "tier4" ($200+)
- "interest_category": one of the user's listed interests

Example of one item:
{{
  "title": "Sunset Kayak on the River",
  "description": "Rent a single kayak for 2 hours at a local outfitter — no experience needed. Going at golden hour makes it memorable.",
  "estimated_cost": "$25 – $40",
  "budget_tier": "tier2",
  "interest_category": "outdoor"
}}"""

    message = client.messages.create(
        # LEARNING — Model Choice:
        #   claude-haiku is fast and cheap — perfect for structured generation tasks
        #   like this where we just need a JSON list, not complex reasoning.
        model="claude-haiku-4-5-20251001",
        max_tokens=1500,
        messages=[{"role": "user", "content": prompt}]
    )

    raw = message.content[0].text.strip()

    # Strip accidental markdown code fences (```json ... ```) if the model adds them
    if raw.startswith("```"):
        lines = raw.split("\n")
        raw = "\n".join(lines[1:-1])  # remove first and last line (the fence lines)

    recommendations = json.loads(raw)

    # Validate that every required field is present in each item
    required = {"title", "description", "estimated_cost", "budget_tier", "interest_category"}
    return [rec for rec in recommendations if isinstance(rec, dict) and required.issubset(rec.keys())]

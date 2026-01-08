"""AI Analyzer module for Reddit pain point analysis using OpenAI-compatible API."""

import os
from typing import List, Dict
from openai import OpenAI


# System prompt for pain point analysis
SYSTEM_PROMPT = """You are a business analyst and product strategist. Your job is to analyze Reddit posts and identify genuine user pain points that represent business opportunities.

For each batch of posts, you will analyze and extract:
1. **Pain Point Summary**: What specific problem are users complaining about or seeking solutions for?
2. **Target Audience**: Who faces this problem? (e.g., indie hackers, e-commerce sellers, consultants, etc.)
3. **Business Value Score**: 1-5 rating
   - 1: Low value, niche or one-off problem
   - 3: Moderate value, common problem with some willingness to pay
   - 5: High value, frequent, frustrating, expensive problem with clear payment potential
4. **MVP Direction**: 1-2 simple product ideas that could solve this problem

Return your analysis in the specified JSON format. Be specific and actionable. Focus on problems that could lead to viable products or services."""


USER_PROMPT_TEMPLATE = """Analyze these {count} Reddit posts and identify business opportunities based on user pain points.

## Posts to Analyze:
{posts_text}

## Output Format (JSON):
{{
  "opportunities": [
    {{
      "pain_point": "Clear description of the problem users are facing",
      "target_audience": "Who experiences this problem (specific role/occupation)",
      "business_value_score": 1-5,
      "mvp_suggestions": ["Simple solution idea 1", "Simple solution idea 2"],
      "source_posts": ["post title 1", "post title 2"]
    }}
  ]
}}

## Rules:
- Group similar posts into the same opportunity when possible
- Focus on problems with clear business potential
- Score based on frequency, frustration level, and payment willingness
- MVP suggestions should be simple and implementable in days, not months"""


def format_posts_for_analysis(posts: List[Dict]) -> str:
    """Format posts into a readable text block for the LLM."""
    formatted = []
    for i, post in enumerate(posts, 1):
        formatted.append(
            f"[{i}] r/{post['subreddit']}\n"
            f"Title: {post['title']}\n"
            f"Summary: {post['summary']}\n"
            f"Link: {post['link']}"
        )
    return "\n\n".join(formatted)


def analyze_pain_points(posts: List[Dict]) -> Dict:
    """Analyze Reddit posts for pain points using OpenAI-compatible API.

    Uses OPENAI_API_KEY and OPENAI_BASE_URL from environment or .env file.

    Args:
        posts: List of post dictionaries from rss_fetcher

    Returns:
        Analysis results dictionary
    """
    if not posts:
        return {"opportunities": [], "message": "No posts to analyze"}

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not set in environment")

    base_url = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
    model = os.environ.get("OPENAI_MODEL", "gpt-4o")

    client = OpenAI(api_key=api_key, base_url=base_url)

    posts_text = format_posts_for_analysis(posts)
    user_prompt = USER_PROMPT_TEMPLATE.format(
        count=len(posts),
        posts_text=posts_text,
    )

    print(f"\nSending {len(posts)} posts to LLM for analysis...")

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
    )

    # Parse the JSON response
    import json
    try:
        content = response.choices[0].message.content
        # Find JSON block
        start = content.find("{")
        end = content.rfind("}") + 1
        if start != -1 and end != 0:
            json_str = content[start:end]
            result = json.loads(json_str)
        else:
            result = {"raw_response": content, "opportunities": []}
    except (json.JSONDecodeError, AttributeError) as e:
        print(f"Error parsing LLM response: {e}")
        result = {"raw_response": content if 'content' in dir() else "", "opportunities": []}

    return result


def print_analysis_report(analysis: Dict):
    """Print a formatted analysis report."""
    opportunities = analysis.get("opportunities", [])

    if not opportunities:
        print("\nNo opportunities found.")
        return

    separator = "=" * 60
    print(f"\n{separator}")
    print("PAIN POINT ANALYSIS REPORT")
    print(f"Found {len(opportunities)} business opportunities")
    print(f"{separator}\n")

    for i, opp in enumerate(opportunities, 1):
        score = opp.get("business_value_score", 0)
        score_bar = "★" * score + "☆" * (5 - score)

        print(f"[{i}] Pain Point: {opp.get('pain_point', 'N/A')}")
        print(f"    Target Audience: {opp.get('target_audience', 'N/A')}")
        print(f"    Business Value: {score_bar} ({score}/5)")
        print("    MVP Ideas:")
        for idea in opp.get("mvp_suggestions", []):
            print(f"      - {idea}")
        sources = ", ".join(opp.get("source_posts", [])[:3])
        print(f"    Sources: {sources}")
        print()


if __name__ == "__main__":
    # Test the analyzer
    from src.painhunter.rss_fetcher import fetch_reddit_posts

    print("Fetching posts...")
    posts = fetch_reddit_posts(subreddits=["SaaS", "Entrepreneur"], hours_ago=24)

    if posts:
        print("\nAnalyzing with LLM...")
        analysis = analyze_pain_points(posts)
        print_analysis_report(analysis)
    else:
        print("No posts found to analyze.")

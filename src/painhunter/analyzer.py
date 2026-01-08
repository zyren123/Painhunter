"""AI Analyzer module for Reddit pain point analysis using OpenAI-compatible API."""

import os
from typing import List, Dict
from openai import OpenAI


# System prompt for pain point analysis
SYSTEM_PROMPT = """你是一位商业分析师和产品策略师。你的工作是分析 Reddit 帖子并识别真正的用户痛点，这些痛点代表商业机会。

对于每批帖子，你需要分析并提取：
1. **痛点总结**：用户抱怨或寻求解决方案的具体问题是什么？
2. **目标受众**：谁面临这个问题？（例如：独立开发者、电商卖家、咨询师等）
3. **商业价值评分**：1-5 分评级
   - 1: 低价值，小众或一次性问题
   - 3: 中等价值，常见问题，有一定付费意愿
   - 5: 高价值，频繁、令人沮丧、昂贵的问题，具有明确的付费潜力
4. **MVP 方向**：1-2 个可以解决这个问题的简单产品想法

请用中文返回分析结果，使用指定的 JSON 格式。要具体且可操作。专注于可能带来可行产品或服务的问题。"""


USER_PROMPT_TEMPLATE = """分析这 {count} 条 Reddit 帖子，基于用户痛点识别商业机会。

## 待分析的帖子：
{posts_text}

## 输出格式 (JSON)：
{{
  "opportunities": [
    {{
      "pain_point": "用户面临问题的清晰描述",
      "target_audience": "谁面临这个问题（具体角色/职业）",
      "business_value_score": 1-5,
      "mvp_suggestions": ["简单解决方案想法 1", "简单解决方案想法 2"],
      "source_posts": ["帖子标题 1", "帖子标题 2"]
    }}
  ]
}}

## 规则：
- 尽可能将相似的帖子归为同一机会
- 专注于具有明确商业潜力的问题
- 根据频率、沮丧程度和付费意愿进行评分
- MVP 建议应该简单，可在几天内实现，而不是几个月"""


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
        return {"opportunities": [], "message": "没有可分析的帖子"}

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not set in environment")

    base_url = os.environ.get("OPENAI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai/")
    model = os.environ.get("OPENAI_MODEL", "gemini-3-flash-preview")

    client = OpenAI(api_key=api_key, base_url=base_url)

    posts_text = format_posts_for_analysis(posts)
    user_prompt = USER_PROMPT_TEMPLATE.format(
        count=len(posts),
        posts_text=posts_text,
    )

    print(f"\n正在将 {len(posts)} 条帖子发送给 LLM 进行分析...")

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
        print(f"解析 LLM 响应时出错: {e}")
        result = {"raw_response": content if 'content' in dir() else "", "opportunities": []}

    return result


def print_analysis_report(analysis: Dict):
    """打印格式化的分析报告。"""
    opportunities = analysis.get("opportunities", [])

    if not opportunities:
        print("\n未找到商业机会。")
        return

    separator = "=" * 60
    print(f"\n{separator}")
    print("痛点分析报告")
    print(f"发现 {len(opportunities)} 个商业机会")
    print(f"{separator}\n")

    for i, opp in enumerate(opportunities, 1):
        score = opp.get("business_value_score", 0)
        score_bar = "★" * score + "☆" * (5 - score)

        print(f"[{i}] 痛点: {opp.get('pain_point', '无')}")
        print(f"    目标受众: {opp.get('target_audience', '无')}")
        print(f"    商业价值: {score_bar} ({score}/5)")
        print("    MVP 建议:")
        for idea in opp.get("mvp_suggestions", []):
            print(f"      - {idea}")
        sources = ", ".join(opp.get("source_posts", [])[:3])
        print(f"    来源: {sources}")
        print()


if __name__ == "__main__":
    # Test the analyzer
    from src.painhunter.rss_fetcher import fetch_reddit_posts

    print("正在获取帖子...")
    posts = fetch_reddit_posts(subreddits=["SaaS", "Entrepreneur"], hours_ago=24)

    if posts:
        print("\n正在使用 LLM 进行分析...")
        analysis = analyze_pain_points(posts)
        print_analysis_report(analysis)
    else:
        print("未找到可分析的帖子。")

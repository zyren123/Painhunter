"""AI Analyzer module for Reddit pain point analysis using OpenAI-compatible API."""

import asyncio
import os
from typing import List, Dict
from openai import AsyncOpenAI


# System prompt for pain point analysis
SYSTEM_PROMPT = """你是一位浏览器插件产品分析师和独立开发者顾问。你的使命是发现独立开发者可以快速构建并变现的产品机会。

## 核心优先级

**产品形态优先级（按顺序）：**
1. **浏览器插件** - 优先识别，任何涉及浏览器操作、网页增强、用户脚本的需求
2. **轻量级 Web 应用** - 配合浏览器插件使用的辅助服务
3. **其他产品** - 仅在上述都不适用时考虑

## 分析维度

对于每批帖子，你需要分析并提取：

### 1. 痛点总结
用户抱怨或寻求解决方案的具体问题是什么？用一句话精准描述。

### 2. 目标受众
谁面临这个问题？（具体到职业/场景，如：独立站卖家、程序员、内容创作者）

### 3. 产品形态判定
- "browser_extension" - 浏览器插件需求
- "web_app" - 独立 Web 应用
- "saas" - SaaS 服务
- "other" - 其他

### 4. 评分维度 (1-5分)

#### 技术实现难度 (tech_complexity_score)
- 1分: 单文件插件，Claude Code 可在数小时内完成
- 2分: 简单插件 + 本地存储，无需后端
- 3分: 插件 + 简单后端 API (FastAPI/Cloudflare Workers)
- 4分: 复杂插件 + 完整后端 + 认证系统
- 5分: 需要复杂基础设施或第三方集成

#### 变现潜力 (monetization_score)
- 1分: 小众需求，难以规模化
- 2分: 细分市场，潜在用户有限
- 3分: 中等市场，可支撑 $5-15/月定价
- 4分: 较大市场，可支撑 $15-29/月定价
- 5分: 广阔市场，有涨价空间

#### Claude Code 实现可行性 (claude_code_score)
- 1分: Claude Code 可独立完成，无需人工介入
- 3分: 需要少量人工指导和代码审查
- 5分: 需要大量人工干预和复杂架构设计

### 5. MVP 建议格式
必须使用 "【X】插件 + Y 功能" 格式，例如：
- "【标签页管理】Tab 增强插件 + AI 自动分类功能"
- "【评论增强】插件 + 一键模板回复功能"

每个机会给出 1-2 个 MVP 建议。

### 6. 预估定价
给出合理的订阅价格区间（$5-29/月）。

请用中文返回分析结果，使用指定的 JSON 格式。"""


USER_PROMPT_TEMPLATE = """分析这 {count} 条 Reddit 帖子，基于用户痛点识别浏览器插件类商业机会。

## 待分析的帖子：
{posts_text}

## 输出格式 (JSON)：
{{
  "opportunities": [
    {{
      "pain_point": "用户面临问题的精准描述",
      "target_audience": "具体目标用户群体",
      "product_type": "browser_extension | web_app | saas | other",
      "tech_complexity_score": 1-5,
      "monetization_score": 1-5,
      "claude_code_score": 1-5,
      "pricing_estimate": "$X-$Y/月",
      "mvp_suggestions": [
        "【类型】插件 + 核心功能描述"
      ],
      "tech_stack_recommendation": "推荐技术栈",
      "differentiation": "与竞品的差异化点",
      "revenue_potential": "预估月收入（如：1000用户×$10 = $10,000/月）",
      "source_posts": ["帖子标题 1", "帖子标题 2"]
    }}
  ],
  "summary": {{
    "total_opportunities": 5,
    "browser_extension_count": 3,
    "quick_win": "技术复杂度1分，可立即实现的机会"
  }}
}}

## 评分标准

### 技术实现难度 (tech_complexity_score)
- 1: 单文件油猴脚本/简单书签工具
- 2: 简单 Chrome 扩展，manifest V3，基础功能
- 3: 中等复杂度插件，Popup + Content Script + Background，无复杂后端
- 4: 复杂插件，需要后端 API
- 5: 复杂系统，需要数据库、认证、支付

### 变现潜力 (monetization_score)
- 1-2: 小众市场
- 3: 细分市场，可支撑 $5-15/月
- 4: 中等市场，可支撑 $15-29/月
- 5: 大众市场，有涨价空间

### Claude Code 可实现性 (claude_code_score)
- 1: Claude Code 可独立完成全部代码
- 2-3: Claude Code 可完成大部分，需少量人工
- 4-5: 需要大量人工设计和编码

## 关键要求
- 只输出 3-5 个最有价值的机会
- MVP 必须是 Claude Code 可在 1-3 天内实现的产品
- 优先选择浏览器插件类机会
- 预估定价必须落在 $5-29/月 区间"""


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


async def _try_call_llm_async(
    client: AsyncOpenAI,
    messages: List[Dict],
    model: str = None,
    max_retries: int = 2,
) -> str:
    """异步尝试调用 LLM，支持模型递进降级。

    递进顺序：
    1. 环境变量 OPENAI_MODEL 或 'gemini-3-flash-preview'
    2. 'gemini-2.5-flash'
    3. 'gemini-2.5-flash-lite'

    Args:
        client: AsyncOpenAI 客户端
        messages: 消息列表
        model: 首选模型（默认从环境变量读取）
        max_retries: 每个模型的最大重试次数

    Returns:
        LLM 响应内容
    """
    if model is None:
        model = os.environ.get("OPENAI_MODEL", "gemini-3-flash-preview")

    # 模型递进列表
    models = [model]
    if model != "gemini-2.5-flash-lite":
        models.append("gemini-2.5-flash")
    if model != "gemini-2.5-flash-lite":
        models.append("gemini-2.5-flash-lite")

    last_error = None
    for attempt_model in models:
        for attempt in range(max_retries):
            try:
                print(f"  尝试模型: {attempt_model} (第 {attempt + 1} 次)")
                response = await client.chat.completions.create(
                    model=attempt_model,
                    messages=messages,
                )
                return response.choices[0].message.content
            except Exception as e:
                last_error = e
                print(f"  模型 {attempt_model} 调用失败: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(1)
                continue
        # 尝试下一个模型
        print(f"  模型 {attempt_model} 多次失败，尝试下一个模型...")

    raise RuntimeError(f"所有模型调用失败: {last_error}")


async def screen_posts_with_llm(posts: List[Dict]) -> List[Dict]:
    """使用 LLM 语义理解筛选有价值的帖子（异步并发执行）。

    Args:
        posts: 原始帖子列表

    Returns:
        筛选后的有价值帖子列表
    """
    if not posts:
        return []

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not set in environment")

    base_url = os.environ.get("OPENAI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai/")
    client = AsyncOpenAI(api_key=api_key, base_url=base_url)

    # 计算批次大小：目标调用次数 ≤ 15
    import math

    total_posts = len(posts)
    max_calls = 15
    batch_size = math.ceil(total_posts / max_calls)
    max_concurrent = 4  # 最大并发数

    print(f"\nLLM 初筛：共 {total_posts} 条帖子，分 {math.ceil(total_posts / batch_size)} 批处理，并发数: {max_concurrent}")

    screening_prompt = """判断每条 Reddit 帖子是否包含以下特征（只返回 JSON 数组）：

判断标准（满足任意一条即为有价值）：
1. 用户遇到痛点或问题，正在寻求解决方案
2. 用户表达了对现有工具/产品的不满
3. 用户有明确的产品想法或功能需求
4. 适合独立开发者快速构建的浏览器插件或轻量级 Web 应用机会

输出格式（JSON 数组）：
[
  {"index": 0, "is_valuable": true, "reason": "简短理由"},
  {"index": 1, "is_valuable": false, "reason": "..."}
]

只返回 JSON，不要其他内容。"""

    semaphore = asyncio.Semaphore(max_concurrent)

    async def process_batch(batch_start: int) -> List[int]:
        """处理单个批次，返回有价值帖子的索引列表。"""
        async with semaphore:
            batch_end = min(batch_start + batch_size, total_posts)
            batch_posts = posts[batch_start:batch_end]

            posts_text = format_posts_for_analysis(batch_posts)
            messages = [
                {"role": "system", "content": "你是一个帖子筛选助手，只返回 JSON 格式的判断结果。"},
                {"role": "user", "content": f"{screening_prompt}\n\n待筛选的帖子：\n\n{posts_text}"},
            ]

            print(f"  处理批次 {batch_start // batch_size + 1}: 帖子 {batch_start + 1}-{batch_end}")

            valuable_indices = []
            try:
                content = await _try_call_llm_async(client, messages)

                import json
                start = content.find("[")
                end = content.rfind("]") + 1
                if start != -1 and end != 0:
                    json_str = content[start:end]
                    results = json.loads(json_str)
                    for item in results:
                        idx = item.get("index", -1)
                        if idx >= 0 and item.get("is_valuable"):
                            actual_idx = batch_start + idx
                            if actual_idx < total_posts:
                                valuable_indices.append(actual_idx)
                else:
                    print(f"  警告：批次 {batch_start // batch_size + 1} 解析失败")

            except Exception as e:
                print(f"  批次 {batch_start // batch_size + 1} 处理失败: {e}")

            return valuable_indices

    # 并发处理所有批次
    batch_starts = list(range(0, total_posts, batch_size))

    tasks = [process_batch(bs) for bs in batch_starts]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # 收集结果
    all_valuable_indices = []
    for result in results:
        if isinstance(result, Exception):
            print(f"批次处理异常: {result}")
        else:
            all_valuable_indices.extend(result)

    # 返回筛选后的帖子
    valuable_posts = [posts[i] for i in all_valuable_indices if i < len(posts)]
    print(f"\nLLM 初筛完成：保留 {len(valuable_posts)}/{total_posts} 条有价值帖子")

    return valuable_posts


def calculate_overall_score(tech: int, monetize: int, claude: int) -> float:
    """计算综合评分，技术难度权重较低，变现潜力权重较高"""
    # 边界检查，确保分数在 1-5 范围内
    tech = max(1, min(5, tech))
    monetize = max(1, min(5, monetize))
    claude = max(1, min(5, claude))
    return round((tech * 0.2 + monetize * 0.4 + claude * 0.4), 1)


async def analyze_pain_points_by_source(posts: List[Dict]) -> Dict:
    """按 Subreddit 来源分组分析文章（异步执行）。

    流程：
    1. LLM 初筛（保留有价值帖子）- 异步并发
    2. 按 Subreddit 分组
    3. 深度分析每个 Subreddit

    Args:
        posts: List of post dictionaries from rss_fetcher

    Returns:
        Analysis results with source_subreddit field added to each opportunity
    """
    from collections import defaultdict

    if not posts:
        return {"opportunities": [], "message": "没有可分析的帖子"}

    # 1. LLM 初筛 - 保留有价值帖子（异步并发）
    print(f"\n{'='*60}")
    print("阶段 1: LLM 初筛 - 语义理解筛选")
    print(f"{'='*60}")
    valuable_posts = await screen_posts_with_llm(posts)

    if not valuable_posts:
        return {"opportunities": [], "message": "初筛后没有有价值帖子"}

    # 2. 按 subreddit 分组
    print(f"\n{'='*60}")
    print("阶段 2: 按 Subreddit 分组分析")
    print(f"{'='*60}")
    posts_by_subreddit = defaultdict(list)
    for post in valuable_posts:
        posts_by_subreddit[post['subreddit']].append(post)

    all_opportunities = []

    # 3. 逐个 subreddit 深度分析
    for subreddit, group_posts in posts_by_subreddit.items():
        print(f"\n正在分析 r/{subreddit} 的 {len(group_posts)} 条帖子...")

        # 调用现有分析函数（传入单组文章）
        result = await analyze_pain_points(group_posts)

        # 为每个 opportunity 添加 subreddit 标识
        for opp in result.get("opportunities", []):
            opp["source_subreddit"] = subreddit
            all_opportunities.append(opp)

    # 4. 合并结果
    return {
        "opportunities": all_opportunities,
        "summary": {
            "total_opportunities": len(all_opportunities),
            "by_subreddit": {k: len(v) for k, v in posts_by_subreddit.items()},
            "posts_screened": len(posts),
            "posts_after_screening": len(valuable_posts)
        }
    }


async def analyze_pain_points(posts: List[Dict]) -> Dict:
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

    client = AsyncOpenAI(api_key=api_key, base_url=base_url)

    posts_text = format_posts_for_analysis(posts)
    user_prompt = USER_PROMPT_TEMPLATE.format(
        count=len(posts),
        posts_text=posts_text,
    )

    print(f"\n正在将 {len(posts)} 条帖子发送给 LLM 进行分析...")

    response = await client.chat.completions.create(
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

    # Add source post links by matching titles
    # Create a title-to-link mapping from original posts
    title_to_link = {post['title']: post['link'] for post in posts}
    
    # Add links to each opportunity's source posts
    for opp in result.get("opportunities", []):
        source_posts = opp.get("source_posts", [])
        source_links = []
        for title in source_posts:
            # Try exact match first
            link = title_to_link.get(title)
            if link:
                source_links.append({"title": title, "link": link})
            else:
                # Try fuzzy match (case-insensitive, partial match)
                for post_title, post_link in title_to_link.items():
                    if title.lower() in post_title.lower() or post_title.lower() in title.lower():
                        source_links.append({"title": title, "link": post_link})
                        break
                else:
                    # If no match found, still add title but without link
                    source_links.append({"title": title, "link": None})
        opp["source_posts_with_links"] = source_links

    # 计算综合评分
    for opp in result.get("opportunities", []):
        tech = opp.get("tech_complexity_score", 3)
        monetize = opp.get("monetization_score", 3)
        claude = opp.get("claude_code_score", 3)
        opp["overall_score"] = calculate_overall_score(tech, monetize, claude)

        # 标准化产品类型为英文，支持中文和英文输入
        product_type = opp.get("product_type", "other")
        type_map = {
            "浏览器插件": "browser_extension",
            "浏览器插件需求": "browser_extension",
            "web_app": "browser_extension",
            "Web应用": "web_app",
            "独立Web应用": "web_app",
            "saas": "saas",
            "SaaS": "saas",
            "其他": "other",
        }
        opp["product_type"] = type_map.get(product_type, "other")

    return result


def print_analysis_report(analysis: Dict):
    """打印格式化的分析报告。"""
    opportunities = analysis.get("opportunities", [])

    if not opportunities:
        print("\n未找到商业机会。")
        return

    separator = "=" * 60
    print(f"\n{separator}")
    print("痛点分析报告 - 浏览器插件变现机会")
    print(f"发现 {len(opportunities)} 个商业机会")
    print(f"{separator}\n")

    for i, opp in enumerate(opportunities, 1):
        tech = opp.get("tech_complexity_score", 0)
        monetize = opp.get("monetization_score", 0)
        claude = opp.get("claude_code_score", 0)
        overall = opp.get("overall_score", 0)
        product_type = opp.get("product_type", "other")
        pricing = opp.get("pricing_estimate", "待定")

        print(f"[{i}] 痛点: {opp.get('pain_point', '无')}")
        print(f"    产品类型: {product_type}")
        print(f"    目标受众: {opp.get('target_audience', '无')}")
        print(f"    评分: 技术{tech}/5 | 变现{monetize}/5 | Claude{claude}/5 | 综合{overall}/5")
        print(f"    预估定价: {pricing}")
        print("    MVP 建议:")
        for idea in opp.get("mvp_suggestions", []):
            print(f"      - {idea}")
        if opp.get("tech_stack_recommendation"):
            print(f"    技术栈: {opp.get('tech_stack_recommendation')}")
        if opp.get("revenue_potential"):
            print(f"    收入潜力: {opp.get('revenue_potential')}")
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

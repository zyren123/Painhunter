"""Email sender module for Painhunter reports."""

import html
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Tuple
from datetime import datetime


# Email HTML template - Indie Hacker Dashboard Theme
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        /* Reset & Base */
        body {{ margin: 0; padding: 0; background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%); font-family: 'SF Pro Display', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; }}
        .container {{ max-width: 720px; margin: 0 auto; padding: 30px 20px; }}

        /* Header with Gradient Text */
        .header {{ text-align: center; margin-bottom: 30px; position: relative; }}
        .header-icon {{ font-size: 48px; margin-bottom: 10px; }}
        .header-title {{
            font-size: 32px;
            font-weight: 800;
            background: linear-gradient(90deg, #f472b6, #c084fc, #818cf8, #2dd4bf);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin: 0;
            letter-spacing: -0.5px;
        }}
        .header-subtitle {{ color: #94a3b8; font-size: 14px; margin-top: 8px; }}

        /* Meta Info */
        .meta-row {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 25px; padding: 12px 20px; background: rgba(255,255,255,0.03); border-radius: 12px; border: 1px solid rgba(255,255,255,0.08); }}
        .date {{ color: #64748b; font-size: 13px; }}
        .count-badge {{
            background: linear-gradient(135deg, #818cf8, #c084fc);
            color: white;
            padding: 6px 16px;
            border-radius: 20px;
            font-size: 13px;
            font-weight: 600;
        }}

        /* Stats Grid */
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 15px;
            margin-bottom: 30px;
        }}
        .stat-card {{
            background: linear-gradient(145deg, rgba(45, 212, 191, 0.1), rgba(129, 140, 248, 0.1));
            border: 1px solid rgba(45, 212, 191, 0.2);
            border-radius: 16px;
            padding: 20px 15px;
            text-align: center;
            position: relative;
            overflow: hidden;
        }}
        .stat-card::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 3px;
            background: linear-gradient(90deg, #2dd4bf, #818cf8);
        }}
        .stat-card:nth-child(2)::before {{
            background: linear-gradient(90deg, #f472b6, #c084fc);
        }}
        .stat-value {{
            font-size: 36px;
            font-weight: 800;
            background: linear-gradient(135deg, #f8fafc, #cbd5e1);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            line-height: 1.1;
        }}
        .stat-label {{
            color: #64748b;
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-top: 5px;
        }}

        /* Opportunity Cards */
        .section-title {{
            color: #f8fafc;
            font-size: 18px;
            font-weight: 600;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        .section-title span {{ font-size: 20px; }}

        .opportunity {{
            background: linear-gradient(145deg, rgba(30, 41, 59, 0.8), rgba(15, 23, 42, 0.9));
            border: 1px solid rgba(129, 140, 248, 0.15);
            border-radius: 20px;
            padding: 25px;
            margin-bottom: 20px;
            position: relative;
            box-shadow: 0 10px 40px rgba(0,0,0,0.3);
        }}
        .opportunity::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: linear-gradient(90deg, #818cf8, #2dd4bf);
            border-radius: 20px 20px 0 0;
        }}

        /* Pain Point Header */
        .pain-header {{ display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 15px; gap: 15px; }}
        .pain-point {{
            margin: 0;
            color: #f1f5f9;
            font-size: 18px;
            font-weight: 600;
            line-height: 1.4;
            flex: 1;
        }}

        /* Product Type Badge */
        .product-type {{
            padding: 6px 14px;
            border-radius: 8px;
            font-size: 11px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            white-space: nowrap;
        }}
        .type-browser-extension {{ background: rgba(45, 212, 191, 0.15); color: #2dd4bf; border: 1px solid rgba(45, 212, 191, 0.3); }}
        .type-web-app {{ background: rgba(129, 140, 248, 0.15); color: #818cf8; border: 1px solid rgba(129, 140, 248, 0.3); }}
        .type-saas {{ background: rgba(244, 114, 182, 0.15); color: #f472b6; border: 1px solid rgba(244, 114, 182, 0.3); }}
        .type-other {{ background: rgba(100, 116, 139, 0.15); color: #94a3b8; border: 1px solid rgba(100, 116, 139, 0.3); }}

        /* Target Audience */
        .audience {{
            color: #64748b;
            font-size: 13px;
            margin-bottom: 15px;
            padding: 10px 15px;
            background: rgba(255,255,255,0.02);
            border-radius: 8px;
            border-left: 3px solid #818cf8;
        }}
        .audience-label {{ color: #94a3b8; font-weight: 500; }}

        /* Scores Row */
        .scores {{ display: flex; gap: 8px; margin: 15px 0; flex-wrap: wrap; }}
        .score-badge {{
            padding: 6px 12px;
            border-radius: 8px;
            font-size: 12px;
            font-weight: 600;
        }}
        .score-tech {{ background: rgba(99, 102, 241, 0.2); color: #a5b4fc; border: 1px solid rgba(99, 102, 241, 0.3); }}
        .score-monetize {{ background: rgba(34, 197, 94, 0.2); color: #4ade80; border: 1px solid rgba(34, 197, 94, 0.3); }}
        .score-claude {{ background: rgba(251, 191, 36, 0.2); color: #fcd34d; border: 1px solid rgba(251, 191, 36, 0.3); }}
        .score-overall {{ background: rgba(192, 132, 252, 0.2); color: #c084fc; border: 1px solid rgba(192, 132, 252, 0.3); }}

        /* Pricing */
        .pricing {{
            display: inline-block;
            background: linear-gradient(135deg, rgba(34, 197, 94, 0.15), rgba(34, 197, 94, 0.05));
            color: #4ade80;
            padding: 10px 18px;
            border-radius: 10px;
            font-weight: 700;
            font-size: 14px;
            margin: 10px 0;
            border: 1px solid rgba(34, 197, 94, 0.2);
        }}

        /* MVP Section */
        .mvp-section {{
            background: linear-gradient(135deg, rgba(129, 140, 248, 0.08), rgba(45, 212, 191, 0.05));
            border-radius: 12px;
            padding: 15px;
            margin: 15px 0;
            border: 1px solid rgba(129, 140, 248, 0.1);
        }}
        .mvp-title {{
            color: #c084fc;
            font-size: 12px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 12px;
        }}
        .mvp-item {{
            background: rgba(129, 140, 248, 0.1);
            padding: 10px 14px;
            border-radius: 8px;
            margin: 6px 0;
            color: #e2e8f0;
            font-size: 13px;
            border-left: 3px solid #818cf8;
        }}

        /* Tech Stack & Revenue */
        .tech-stack {{
            color: #94a3b8;
            font-size: 13px;
            margin: 8px 0;
            padding: 8px 0;
            border-top: 1px solid rgba(255,255,255,0.05);
        }}
        .revenue {{
            color: #4ade80;
            font-size: 14px;
            font-weight: 600;
            margin: 8px 0;
        }}

        /* Links */
        .links-section {{ margin-top: 15px; }}
        .link-button {{
            display: inline-block;
            padding: 8px 16px;
            background: rgba(129, 140, 248, 0.15);
            color: #818cf8;
            text-decoration: none;
            border-radius: 8px;
            font-size: 12px;
            font-weight: 600;
            margin-right: 8px;
            margin-bottom: 8px;
            border: 1px solid rgba(129, 140, 248, 0.3);
        }}
        .link-button:hover {{
            background: rgba(129, 140, 248, 0.25);
        }}

        /* Subreddit Badge */
        .subreddit-badge {{
            background: rgba(129, 140, 248, 0.15);
            color: #818cf8;
            padding: 4px 10px;
            border-radius: 6px;
            font-size: 11px;
            font-weight: 600;
        }}

        /* Footer */
        .footer {{
            text-align: center;
            margin-top: 40px;
            padding-top: 25px;
            border-top: 1px solid rgba(255,255,255,0.08);
        }}
        .footer-text {{ color: #475569; font-size: 12px; }}
        .footer-brand {{
            font-weight: 700;
            background: linear-gradient(90deg, #818cf8, #2dd4bf);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="header-icon">🎯</div>
            <h1 class="header-title">Painhunter</h1>
            <p class="header-subtitle">Daily Opportunity Report</p>
        </div>

        <div class="meta-row">
            <span class="date">{date}</span>
            <span class="count-badge">✨ {count} Opportunities Found</span>
        </div>

        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value">{plugin_count}</div>
                <div class="stat-label">Browser Extensions</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{webapp_count}</div>
                <div class="stat-label">Web Apps</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{top_pick}</div>
                <div class="stat-label">Top Pick</div>
            </div>
        </div>

        <h2 class="section-title"><span>🚀</span> Opportunities Discovered</h2>

        {content}

        <div class="footer">
            <p class="footer-text">Generated by <span class="footer-brand">Painhunter</span> — Reddit Pain Point Hunter</p>
            <p class="footer-text">Source: r/SaaS, r/Entrepreneur, r/SideProject • Past 24 hours</p>
        </div>
    </div>
</body>
</html>
"""


def _escape_html(text: str) -> str:
    """Escape HTML special characters to prevent XSS."""
    if text is None:
        return ""
    return html.escape(str(text), quote=True)


OPPORTUNITY_TEMPLATE = """
    <div class="opportunity">
        <div class="pain-header">
            <span class="subreddit-badge">r/{subreddit}</span>
            <h2 class="pain-point">💡 {pain_point}</h2>
            <span class="product-type type-{product_type}">{product_type}</span>
        </div>

        <div class="audience">
            <span class="audience-label">Target Audience:</span> {audience}
        </div>

        <div class="scores">
            <span class="score-badge score-tech">Tech {tech_score}</span>
            <span class="score-badge score-monetize">Monetize {monetize_score}</span>
            <span class="score-badge score-claude">Claude {claude_score}</span>
            <span class="score-badge score-overall">Overall {overall_score}</span>
        </div>

        <div class="pricing">💰 {pricing}</div>

        <div class="mvp-section">
            <div class="mvp-title">◆ MVP Suggestions</div>
            {mvp_list}
        </div>

        <div class="tech-stack">⚙️ Tech Stack: {tech_stack}</div>
        <div class="revenue">📈 Revenue: {revenue}</div>

        <div class="links-section">
            {links}
        </div>
    </div>
"""


def format_opportunities_html(opportunities: List[Dict]) -> Tuple[str, Dict]:
    """Format opportunities into HTML and return stats.

    Returns:
        Tuple of (html_content, stats_dict)
    """
    if not opportunities:
        return "<p>No opportunities found today.</p>", {
            "plugin_count": 0,
            "webapp_count": 0,
            "top_pick": "无"
        }

    html_parts = []
    plugin_count = 0
    webapp_count = 0

    for opp in opportunities:
        # Count product types
        product_type = opp.get("product_type", "other")
        if product_type == "browser_extension":
            plugin_count += 1
        elif product_type == "web_app":
            webapp_count += 1

        # MVP items with new class (already escaped)
        mvp_html = "".join(
            f'<div class="mvp-item">• {_escape_html(idea)}</div>' for idea in opp.get("mvp_suggestions", [])
        )


        # Get links from source_posts_with_links if available
        source_links = opp.get("source_posts_with_links", [])
        if source_links:
            # Format links as button-style anchor tags
            link_htmls = []
            for item in source_links[:3]:
                if isinstance(item, dict) and item.get("link"):
                    title = item.get("title", "View Post")
                    link_htmls.append(f'<a href="{item["link"]}" class="link-button">📎 {title}</a>')
            links = "".join(link_htmls) if link_htmls else "No links available"
        else:
            # Fallback: no links available
            links = "No links available"

        # Convert product_type to hyphenated format for CSS class (browser_extension -> browser-extension)
        product_type_hyphenated = product_type.replace("_", "-")

        html_parts.append(
            OPPORTUNITY_TEMPLATE.format(
                subreddit=_escape_html(opp.get("source_subreddit", "unknown")),
                pain_point=_escape_html(opp.get("pain_point", "N/A")),
                product_type=product_type_hyphenated,
                audience=_escape_html(opp.get("target_audience", "N/A")),
                tech_score=opp.get("tech_complexity_score", 0),
                monetize_score=opp.get("monetization_score", 0),
                claude_score=opp.get("claude_code_score", 0),
                overall_score=opp.get("overall_score", 0),
                pricing=_escape_html(opp.get("pricing_estimate", "待定")),
                mvp_list=mvp_html,
                tech_stack=_escape_html(opp.get("tech_stack_recommendation", "未指定")),
                revenue=_escape_html(opp.get("revenue_potential", "待评估")),
                links=links,
            )
        )

    stats = {
        "plugin_count": plugin_count,
        "webapp_count": webapp_count,
        "top_pick": _truncate_text(opportunities[0].get("pain_point", "无"), 10) if opportunities else "无"
    }

    return "".join(html_parts), stats


def _truncate_text(text: str, max_chars: int) -> str:
    """Truncate text to max_chars characters, handling Unicode properly."""
    if not text:
        return ""
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "..."


def generate_html_report(analysis: Dict) -> str:
    """Generate complete HTML email report."""
    opportunities = analysis.get("opportunities", [])
    content, stats = format_opportunities_html(opportunities)

    return HTML_TEMPLATE.format(
        date=datetime.now().strftime("%Y-%m-%d"),
        count=len(opportunities),
        content=content,
        plugin_count=stats.get("plugin_count", 0),
        webapp_count=stats.get("webapp_count", 0),
        top_pick=stats.get("top_pick", "无"),
    )


def send_email(
    smtp_host: str,
    smtp_port: int,
    username: str,
    password: str,
    to_emails: List[str],
    subject: str = None,
    html_body: str = None,
) -> bool:
    """Send email via SMTP.

    Args:
        smtp_host: SMTP server hostname
        smtp_port: SMTP port (usually 587 for TLS)
        username: SMTP login username (usually email address)
        password: SMTP password or app token
        to_emails: List of recipient email addresses
        subject: Email subject (auto-generated if None)
        html_body: HTML content (required)

    Returns:
        True if sent successfully, False otherwise
    """
    if not html_body:
        print("Error: No HTML body provided")
        return False

    # Default subject with date
    if subject is None:
        date_str = datetime.now().strftime("%Y-%m-%d")
        subject = f"🎯 Painhunter Daily Report - {date_str}"

    # Create message
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = username
    msg["To"] = ", ".join(to_emails)

    # Attach HTML
    html_part = MIMEText(html_body, "html")
    msg.attach(html_part)

    try:
        # Connect and send
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(username, password)
            server.sendmail(username, to_emails, msg.as_string())

        print(f"Email sent successfully to {len(to_emails)} recipients")
        return True
    except smtplib.SMTPException as e:
        print(f"Error sending email: SMTP error (code: {e.smtp_code})")
        return False
    except Exception as e:
        print(f"Error sending email: An unexpected error occurred")
        return False


def send_report(
    analysis: Dict,
    smtp_host: str = None,
    smtp_port: int = 587,
    username: str = None,
    password: str = None,
    to_emails: List[str] = None,
) -> bool:
    """Generate and send the daily report via email.

    Reads SMTP settings from environment if not provided.
    """
    # Get settings from environment
    smtp_host = smtp_host or os.environ.get("SMTP_HOST")
    smtp_port = smtp_port or int(os.environ.get("SMTP_PORT", 587))
    username = username or os.environ.get("SMTP_USERNAME")
    password = password or os.environ.get("SMTP_PASSWORD")

    to_emails = to_emails or os.environ.get("TO_EMAILS", "").split(",")

    # Validate required settings
    if not all([smtp_host, username, password, to_emails]):
        missing = []
        if not smtp_host: missing.append("SMTP_HOST")
        if not username: missing.append("SMTP_USERNAME")
        if not password: missing.append("SMTP_PASSWORD")
        if not to_emails or not to_emails[0]: missing.append("TO_EMAILS")
        print(f"Warning: Missing email settings: {', '.join(missing)}")
        print("Set these in .env or environment variables")
        return False

    # Generate HTML report
    html_body = generate_html_report(analysis)

    # Send email
    return send_email(
        smtp_host=smtp_host,
        smtp_port=smtp_port,
        username=username,
        password=password,
        to_emails=[e.strip() for e in to_emails if e.strip()],
        html_body=html_body,
    )


if __name__ == "__main__":
    # Test email generation
    test_analysis = {
        "opportunities": [
            {
                "pain_point": "用户在多个标签页间切换效率低，难以快速找到需要的页面",
                "target_audience": "重度浏览器用户、程序员、内容创作者",
                "product_type": "browser_extension",
                "tech_complexity_score": 2,
                "monetization_score": 4,
                "claude_code_score": 1,
                "overall_score": 2.6,
                "pricing_estimate": "$9-$19/月",
                "mvp_suggestions": [
                    "【标签页管理】Tab 增强插件 + AI 自动分类功能",
                    "【标签页管理】插件 + 搜索和分组功能"
                ],
                "tech_stack_recommendation": "Chrome Extension + localStorage",
                "revenue_potential": "1000用户 × $14 = $14,000/月",
                "source_posts": ["Post 1", "Post 2"],
                "source_posts_with_links": [
                    {"title": "Post 1", "link": "https://reddit.com/r/SaaS/comments/xxx"},
                    {"title": "Post 2", "link": "https://reddit.com/r/Entrepreneur/comments/yyy"}
                ]
            },
            {
                "pain_point": "电商卖家需要快速生成产品描述和广告文案",
                "target_audience": "独立站卖家、Shopify 商家",
                "product_type": "browser_extension",
                "tech_complexity_score": 3,
                "monetization_score": 4,
                "claude_code_score": 2,
                "overall_score": 3.2,
                "pricing_estimate": "$15-$29/月",
                "mvp_suggestions": [
                    "【AI 写作助手】浏览器插件 + 一键生成产品描述"
                ],
                "tech_stack_recommendation": "Chrome Extension + OpenAI API",
                "revenue_potential": "500用户 × $20 = $10,000/月",
                "source_posts": ["Post 3"],
                "source_posts_with_links": [
                    {"title": "Post 3", "link": "https://reddit.com/r/Entrepreneur/comments/zzz"}
                ]
            }
        ]
    }

    print("Testing HTML report generation...")
    html = generate_html_report(test_analysis)
    print(f"Generated {len(html)} characters of HTML")

    # Save to file for preview
    with open("/tmp/test_report.html", "w") as f:
        f.write(html)
    print("Preview saved to /tmp/test_report.html")

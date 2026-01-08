# PRD: 痛点猎人 (Pain Point Hunter - RSS Edition)

## 1. 产品定位
一个轻量化的自动化脚本，通过监听 Reddit 垂直社区的 RSS Feed，利用 Claude AI 自动筛选、分析并提取真实的用户痛点，每天定时发送“商业机会报告”至用户邮箱。

## 2. 核心功能模块

### 2.1 数据采集模块 (RSS Scraper)
*   **目标源：** 自定义 Subreddit 列表（首批：`r/SaaS`, `r/Entrepreneur`, `r/SideProject`, `r/smallbusiness`）。
*   **实现方式：** 使用 Python `feedparser` 库访问 `https://www.reddit.com/r/[SUB]/new/.rss`。
*   **频率限制：** 模拟浏览器 User-Agent，避免被 Reddit 屏蔽。
*   **增量抓取：** 仅处理过去 24 小时内的帖子。

### 2.2 智能过滤模块 (Pre-Filter)
*   **关键词匹配：** 筛选标题或摘要中包含以下词汇的帖子：
    *   *需求类：* "is there an app", "anyone know a tool", "how do I"
    *   *抱怨类：* "frustrated with", "too expensive", "struggling with", "hate it when"
    *   *效率类：* "manual task", "waste of time", "tedious"

### 2.3 AI 深度分析模块 (Claude Intelligence)
将过滤后的帖子列表发送给 Claude，提示词要求：
1.  **痛点提取：** 总结用户到底在烦恼什么？
2.  **受众画像：** 谁遇到了这个问题？（如：独立站卖家、律师、大学生）
3.  **商业价值评分：** 1-5 分（基于解决难度和付费意愿）。
4.  **解决方案构思：** 给出 1-2 个简单的 MVP（最小可行性产品）方向。

### 2.4 自动化与通知模块 (Delivery)
*   **报告格式：** 清晰的 HTML 邮件。
*   **发送渠道：** 通过 Resend API 或 SMTP 每天定时发送。
*   **调度中心：** 使用 GitHub Actions，每日 UTC 00:00 自动触发。

---

## 3. 技术栈
*   **语言：** Python 3.10+
*   **关键库：** `feedparser` (解析RSS), `httpx` (发送请求), `jinja2` (生成 HTML 邮件模版)。
*   **AI：** Claude API (Anthropic)。
*   **基础设施：** GitHub 仓库 + GitHub Actions (免费)。

---

## 4. 实施路线图 (MVP 阶段)

### 第一阶段：脚手架搭建 (Day 1)
1.  让 Claude Code 创建项目结构。
2.  实现 RSS 抓取逻辑，确保能拿到帖子的 Title 和 Link。
3.  配置 `.env` 文件处理敏感信息（Claude API Key, Email Secret）。

### 第二阶段：AI 集成 (Day 1-2)
1.  编写专门针对“痛点发现”的 Prompt。
2.  测试 Claude 对 Reddit 帖子的总结效果，优化过滤算法。

### 第三阶段：自动化部署 (Day 2)
1.  集成邮件发送服务。
2.  编写 GitHub Actions `.yml` 文件，实现云端每日自动运行。
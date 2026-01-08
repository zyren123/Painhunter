-使用uv管理环境，.venv激活环境

## 项目配置记录

### 环境变量配置 (在 .env 文件中配置)

#### LLM 配置 (必需)
| 环境变量 | 说明 | 示例 |
|---------|------|------|
| `OPENAI_API_KEY` | API Key | `sk-xxxxx` |
| `OPENAI_BASE_URL` | API 端点 | `https://llm.baijia.com/v1/` |
| `OPENAI_MODEL` | 模型名称 (可选，默认 gpt-4o) | `doubao/Doubao-Seed-1-8-251215` |

#### 邮件配置 (可选，不配置则不发送邮件)
| 环境变量 | 说明 | 示例 |
|---------|------|------|
| `SMTP_HOST` | SMTP 服务器地址 | `smtp.gmail.com` |
| `SMTP_PORT` | SMTP 端口 (默认 587) | `587` |
| `SMTP_USERNAME` | 发件邮箱 | `sender@gmail.com` |
| `SMTP_PASSWORD` | 密码或 App Token | `xxxxxx` |
| `TO_EMAILS` | 收件人邮箱，多个用逗号分隔 | `user1@email.com,user2@email.com` |

### Subreddit 配置
当前监控的 Subreddits (`main.py`):
- `["SaaS", "Entrepreneur", "SideProject", "smallbusiness"]`
- 可添加: `freelance`, `investing`, `WebDev` 等
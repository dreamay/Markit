"""配置加载与分类规则。"""

import json
from pathlib import Path

# ============================================================
# 自动归类规则：域名关键词 -> 分类名
# ============================================================
CATEGORY_RULES = {
    "开发工具": [
        "github", "gitlab", "bitbucket", "stackoverflow", "npmjs",
        "pypi", "hub.docker", "vercel", "netlify", "heroku",
        "codepen", "jsfiddle", "replit",
    ],
    "编程文档": [
        "docs.python", "developer.mozilla", "devdocs", "readthedocs",
        "docs.rs", "pkg.go.dev", "learn.microsoft", "developer.apple",
    ],
    "AI / 人工智能": [
        "openai", "claude", "anthropic", "huggingface", "kaggle",
        "colab.research.google", "bard.google",
    ],
    "搜索引擎": [
        "google.com", "bing.com", "baidu.com", "duckduckgo",
    ],
    "社交媒体": [
        "twitter", "x.com", "facebook", "instagram", "linkedin",
        "reddit", "mastodon",
    ],
    "视频 / 媒体": [
        "youtube", "bilibili", "vimeo", "netflix", "spotify",
        "twitch",
    ],
    "新闻 / 资讯": [
        "news.ycombinator", "techcrunch", "theverge", "arstechnica",
        "bbc.com", "cnn.com",
    ],
    "知识 / 百科": [
        "wikipedia", "zhihu", "quora", "douban", "wikimedia",
    ],
    "云服务": [
        "console.aws", "cloud.google", "portal.azure", "console.cloud",
    ],
    "刷题 / 学习": [
        "leetcode", "hackerrank", "codeforces", "coursera", "udemy",
        "edx.org", "khanacademy",
    ],
}


def load_config() -> dict:
    """读取 config.json 配置文件，不存在则返回默认值。"""
    config_path = Path(__file__).parent.parent / "config.json"
    defaults = {"category_rules": {}}
    if not config_path.exists():
        return defaults
    try:
        data = json.loads(config_path.read_text(encoding="utf-8"))
        defaults.update(data)
    except Exception as e:
        print(f"警告: 读取 config.json 失败 ({e})，使用默认配置")
    return defaults


def _build_rules(config: dict) -> dict[str, list[str]]:
    """合并内置规则与用户自定义规则（用户规则优先）。"""
    merged = dict(CATEGORY_RULES)
    for cat, keywords in config.get("category_rules", {}).items():
        if keywords:  # 非空列表才覆盖
            merged[cat] = keywords
    return merged

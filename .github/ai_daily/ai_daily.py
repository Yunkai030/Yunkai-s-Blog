"""
24小时无人值守 AI 科技博客 Agent - 阶段一/二核心代码

功能：
1. 从 RSS 源抓取最近 24 小时文章
2. 使用 SQLite 记录已处理 URL，避免重复生成
3. 调用 DeepSeek API 生成符合 Hexo Front-matter 规范的 Markdown
4. 校验输出格式，失败时触发一次修复

运行前：
    pip install -r requirements.txt
    在 .env 里设置 DEEPSEEK_API_KEY，或设置同名环境变量

示例：
    python ai_blog_agent_stage1_2.py
"""

from __future__ import annotations

import asyncio
import hashlib
import os
import re
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlparse

import feedparser
import requests
from bs4 import BeautifulSoup
from dateutil import parser as date_parser
from dotenv import load_dotenv
from openai import AsyncOpenAI, RateLimitError, APIConnectionError, APIStatusError
from pydantic import BaseModel, Field, ValidationError


load_dotenv()


# =========================
# 1. 基础配置
# =========================

RSS_FEEDS = [
    "https://www.anthropic.com/news/rss.xml",
    "https://openai.com/news/rss.xml",
    "https://export.arxiv.org/rss/cs.AI",
    "https://hnrss.org/frontpage",
]

BASE_DIR = Path(__file__).resolve().parent
REPO_ROOT = BASE_DIR.parents[1]
DB_PATH = Path(os.getenv("AI_DAILY_DB_PATH", REPO_ROOT / "data" / "agent_seen_urls.sqlite3"))
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

# 默认写入当前 Hexo 仓库的文章目录。
# 本地或云端都可以通过 HEXO_POSTS_DIR 覆盖。
OUTPUT_DIR = Path(
    os.getenv(
        "HEXO_POSTS_DIR",
        REPO_ROOT / "source" / "_posts",
    )
)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# 例如 .env:
# HEXO_POSTS_DIR=C:\path\to\your\hexo\source\_posts

DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-v4-flash")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
MAX_ARTICLES_PER_RUN = int(os.getenv("MAX_ARTICLES_PER_RUN", "5"))
ARTICLE_LOOKBACK_HOURS = int(os.getenv("ARTICLE_LOOKBACK_HOURS", "24"))
REQUEST_TIMEOUT_SECONDS = 20
MAX_CONTENT_CHARS = 8000


# =========================
# 2. 数据结构
# =========================

@dataclass(frozen=True)
class RawArticle:
    title: str
    url: str
    source: str
    published_at: datetime
    summary: str
    content: str


class HexoFrontMatter(BaseModel):
    """用于校验模型是否生成了 Hexo 需要的关键字段。"""

    title: str = Field(min_length=2)
    date: str = Field(pattern=r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$")
    tags: list[str] = Field(min_length=1)
    categories: str = Field(min_length=1)


# =========================
# 3. SQLite 防重模块
# =========================

class SeenUrlStore:
    """用 SQLite 记录已处理 URL。

    坑点：
    - 不建议只用内存 set，因为 GitHub Actions/cron 每次运行都是新进程。
    - URL 可能很长，实际存 hash 更稳。
    - 状态分 seen/generated/failed，方便后面做失败重试。
    """

    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS articles (
                    url_hash TEXT PRIMARY KEY,
                    url TEXT NOT NULL,
                    title TEXT,
                    source TEXT,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            conn.commit()

    @staticmethod
    def hash_url(url: str) -> str:
        return hashlib.sha256(url.encode("utf-8")).hexdigest()

    def exists(self, url: str) -> bool:
        url_hash = self.hash_url(url)
        with self._connect() as conn:
            row = conn.execute(
                "SELECT 1 FROM articles WHERE url_hash = ?",
                (url_hash,),
            ).fetchone()
        return row is not None

    def mark(self, article: RawArticle, status: str) -> None:
        now = datetime.now(timezone.utc).isoformat()
        url_hash = self.hash_url(article.url)
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO articles(url_hash, url, title, source, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(url_hash) DO UPDATE SET
                    status = excluded.status,
                    updated_at = excluded.updated_at
                """,
                (url_hash, article.url, article.title, article.source, status, now, now),
            )
            conn.commit()


# =========================
# 4. RSS 抓取与正文抽取
# =========================

def parse_entry_datetime(entry: feedparser.FeedParserDict) -> datetime:
    """尽量从 RSS entry 中解析发布时间，缺失时用当前时间。

    坑点：
    - 不同 RSS 字段名不统一：published/updated/created 都可能出现。
    - 一定要转成 timezone-aware datetime，否则跨时区比较容易出 bug。
    """

    raw_value = entry.get("published") or entry.get("updated") or entry.get("created")
    if not raw_value:
        return datetime.now(timezone.utc)

    dt = date_parser.parse(raw_value)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def extract_text_from_url(url: str) -> str:
    """抓取网页正文并清洗成纯文本。

    这是轻量方案，够做 MVP。后续可替换为 trafilatura/readability-lxml，
    正文抽取质量会更好。
    """

    headers = {
        "User-Agent": (
            "Mozilla/5.0 AI-Blog-Agent/0.1 "
            "(personal research project; contact: your_email@example.com)"
        )
    }
    response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT_SECONDS)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    for tag in soup(["script", "style", "noscript", "header", "footer", "nav"]):
        tag.decompose()

    text = soup.get_text(separator="\n")
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return "\n".join(lines)[:MAX_CONTENT_CHARS]


def collect_recent_articles(store: SeenUrlStore) -> list[RawArticle]:
    cutoff = datetime.now(timezone.utc) - timedelta(hours=ARTICLE_LOOKBACK_HOURS)
    articles: list[RawArticle] = []

    for feed_url in RSS_FEEDS:
        feed = feedparser.parse(feed_url)
        source = feed.feed.get("title", urlparse(feed_url).netloc)

        for entry in feed.entries:
            url = entry.get("link")
            title = entry.get("title", "").strip()
            if not url or not title or store.exists(url):
                continue

            published_at = parse_entry_datetime(entry)
            if published_at < cutoff:
                continue

            summary = BeautifulSoup(entry.get("summary", ""), "html.parser").get_text(" ", strip=True)

            try:
                content = extract_text_from_url(url)
            except Exception as exc:
                # 正文抓取失败时仍然可以用 RSS summary 做降级输入。
                content = summary
                print(f"[WARN] 正文抓取失败，使用 summary 降级: {title} ({exc})")

            if not content:
                continue

            articles.append(
                RawArticle(
                    title=title,
                    url=url,
                    source=source,
                    published_at=published_at,
                    summary=summary,
                    content=content,
                )
            )

            if len(articles) >= MAX_ARTICLES_PER_RUN:
                return articles

    return articles


# =========================
# 5. DeepSeek 生成模块
# =========================

def build_generation_prompt(article: RawArticle) -> str:
    return f"""
你是一名资深数据科学家、AI 工程师和中文科技博客作者。

请基于下面的英文/中文技术文章，生成一篇适合发布到 Hexo 博客的中文 Markdown 文章。

硬性要求：
1. 输出必须从 Hexo Front-matter 开始，第一行必须是 ---。
2. Front-matter 必须包含且只需要包含这些字段：
   title, date, tags, categories
3. date 格式必须是 YYYY-MM-DD HH:MM:SS。
4. tags 必须是 YAML 数组，例如 [AI, Data Science, Agent]。
5. categories 固定为 技术动态。
6. Front-matter 结束后再写正文。
7. 正文必须包含：
   - 事件/论文/产品概述
   - 关键技术点
   - 对数据科学或 AI Agent 落地的意义
   - 我的技术点评
   - 原文链接
8. 不要编造原文没有的信息；不确定的地方明确写“原文未说明”。
9. 不要输出解释性开场白，不要把 Markdown 包在代码块里。

原始信息：
标题：{article.title}
来源：{article.source}
发布时间：{article.published_at.strftime("%Y-%m-%d %H:%M:%S")}
链接：{article.url}
摘要：{article.summary}

正文：
{article.content}
""".strip()


def build_repair_prompt(broken_markdown: str, error: str) -> str:
    return f"""
下面是一篇格式有问题的 Hexo Markdown。请只修复格式，不要改变文章事实内容。

错误信息：
{error}

修复要求：
1. 第一行必须是 ---。
2. Front-matter 必须包含 title/date/tags/categories。
3. date 必须是 YYYY-MM-DD HH:MM:SS。
4. tags 必须是 YAML 数组。
5. categories 固定为 技术动态。
6. 不要输出解释，不要包代码块。

待修复 Markdown：
{broken_markdown}
""".strip()


async def call_deepseek_with_retry(
    client: AsyncOpenAI,
    prompt: str,
    max_retries: int = 3,
) -> str:
    """调用 DeepSeek，并处理限流/网络抖动。

    坑点：
    - 生产环境不要无限重试，否则可能把账单或任务队列打爆。
    - RateLimitError 要指数退避。
    - APIStatusError 里 4xx 通常是请求问题，5xx 才更值得重试。
    """

    for attempt in range(max_retries):
        try:
            response = await client.chat.completions.create(
                model=DEEPSEEK_MODEL,
                messages=[
                    {"role": "system", "content": "你是严谨的中文 AI 技术博客作者。"},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                max_tokens=3000,
            )
            return response.choices[0].message.content or ""

        except (RateLimitError, APIConnectionError) as exc:
            wait_seconds = 2 ** attempt
            print(f"[WARN] DeepSeek 调用失败，{wait_seconds}s 后重试: {exc}")
            await asyncio.sleep(wait_seconds)

        except APIStatusError as exc:
            if 500 <= exc.status_code < 600 and attempt < max_retries - 1:
                wait_seconds = 2 ** attempt
                print(f"[WARN] DeepSeek 服务端错误，{wait_seconds}s 后重试: {exc}")
                await asyncio.sleep(wait_seconds)
                continue
            raise

    raise RuntimeError("DeepSeek API 多次重试后仍然失败")


# =========================
# 6. Markdown 校验与保存
# =========================

FRONT_MATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)


def parse_simple_front_matter(markdown: str) -> HexoFrontMatter:
    """轻量解析 Hexo Front-matter。

    为了减少依赖，这里只解析本项目要求的简单字段。生产环境建议用 python-frontmatter。
    """

    match = FRONT_MATTER_RE.match(markdown.strip())
    if not match:
        raise ValueError("缺少合法的 Hexo Front-matter")

    raw = match.group(1)
    data: dict[str, object] = {}

    for line in raw.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")

        if key == "tags":
            # 只支持 [AI, Data Science] 这种简单数组，足够约束模型输出。
            if not (value.startswith("[") and value.endswith("]")):
                raise ValueError("tags 必须是 YAML 数组格式，例如 [AI, Data Science]")
            tags = [item.strip().strip('"').strip("'") for item in value[1:-1].split(",")]
            data[key] = [tag for tag in tags if tag]
        else:
            data[key] = value

    return HexoFrontMatter.model_validate(data)


def yaml_quote(value: str) -> str:
    """把模型输出转成 YAML 安全字符串。

    标题里常见的冒号、引号、中文标点都可能让 Hexo front-matter 解析失败，
    因此保存前统一双引号包裹。
    """

    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def normalize_front_matter(markdown: str) -> str:
    """规范化 Hexo Front-matter，避免无人值守时被 YAML 小问题卡住。"""

    clean_markdown = markdown.strip()
    match = FRONT_MATTER_RE.match(clean_markdown)
    if not match:
        raise ValueError("缺少合法的 Hexo Front-matter")

    front_matter = parse_simple_front_matter(clean_markdown)
    body = clean_markdown[match.end():].strip()
    tags = ", ".join(yaml_quote(tag) for tag in front_matter.tags)

    normalized_header = "\n".join(
        [
            "---",
            f"title: {yaml_quote(front_matter.title)}",
            f"date: {yaml_quote(front_matter.date)}",
            f"tags: [{tags}]",
            f"categories: {yaml_quote(front_matter.categories)}",
            "---",
        ]
    )
    return normalized_header + "\n\n" + body


def slugify(text: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9\u4e00-\u9fff]+", "-", text).strip("-").lower()
    return slug[:80] or "ai-post"


def save_markdown(markdown: str, article: RawArticle) -> Path:
    markdown = normalize_front_matter(markdown)
    date_prefix = datetime.now().strftime("%Y-%m-%d")
    filename = f"{date_prefix}-{slugify(article.title)}.md"
    output_path = OUTPUT_DIR / filename
    output_path.write_text(markdown.strip() + "\n", encoding="utf-8")
    return output_path


async def generate_post_for_article(
    client: AsyncOpenAI,
    store: SeenUrlStore,
    article: RawArticle,
) -> None:
    print(f"[INFO] 正在生成: {article.title}")
    store.mark(article, "seen")

    try:
        markdown = await call_deepseek_with_retry(client, build_generation_prompt(article))

        try:
            parse_simple_front_matter(markdown)
        except (ValueError, ValidationError) as exc:
            print(f"[WARN] Markdown 校验失败，触发修复: {exc}")
            markdown = await call_deepseek_with_retry(client, build_repair_prompt(markdown, str(exc)))
            parse_simple_front_matter(markdown)

        output_path = save_markdown(markdown, article)
        store.mark(article, "generated")
        print(f"[OK] 已保存: {output_path}")

    except Exception as exc:
        store.mark(article, "failed")
        print(f"[ERROR] 生成失败: {article.title} ({exc})")


async def main() -> None:
    if not os.getenv("DEEPSEEK_API_KEY"):
        raise RuntimeError("请先在 .env 或环境变量里设置 DEEPSEEK_API_KEY")

    store = SeenUrlStore(DB_PATH)
    articles = collect_recent_articles(store)
    if not articles:
        print("[INFO] 最近 24 小时没有新的可处理文章")
        return

    client = AsyncOpenAI(
        api_key=os.environ["DEEPSEEK_API_KEY"],
        base_url=DEEPSEEK_BASE_URL,
    )

    # 并发数不要太高，避免触发 Rate Limit。MVP 阶段 2-3 个足够。
    semaphore = asyncio.Semaphore(2)

    async def guarded_generate(article: RawArticle) -> None:
        async with semaphore:
            await generate_post_for_article(client, store, article)

    await asyncio.gather(*(guarded_generate(article) for article in articles))


if __name__ == "__main__":
    asyncio.run(main())

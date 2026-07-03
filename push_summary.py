import os
import sys
import time
import json
import re
import requests
import feedparser
from datetime import datetime, timedelta
from urllib.parse import urlencode
from typing import List, Dict
from openai import OpenAI

# =========================
# 环境变量（请先在系统里配置）
# =========================
# DeepSeek
#   OPENAI_API_KEY=<你的 DeepSeek API Key>
#   OPENAI_BASE_URL=https://api.deepseek.com   （也可不设，用下面的默认）
# Notion
#   NOTION_TOKEN=<你的 Notion 集成密钥>
#   PAGE_ID=<要写入的页面或块的 block_id>
# 关键词（可选）
#   QUERY_KEYWORDS="kidney, C3, macrophage"

DEEPSEEK_API_KEY = os.environ.get("OPENAI_API_KEY")
DEEPSEEK_BASE_URL = os.environ.get("OPENAI_BASE_URL", "https://api.deepseek.com")
NOTION_TOKEN = os.environ.get("NOTION_TOKEN")
PAGE_ID = os.environ.get("PAGE_ID")
QUERY_KEYWORDS = os.environ.get("QUERY_KEYWORDS", "kidney, C3, macrophage")

if not DEEPSEEK_API_KEY:
    print("ERROR: 请设置环境变量 OPENAI_API_KEY 为你的 DeepSeek API Key")
    sys.exit(1)
if not NOTION_TOKEN or not PAGE_ID:
    print("ERROR: 请设置环境变量 NOTION_TOKEN 与 PAGE_ID")
    sys.exit(1)

# 初始化 DeepSeek（OpenAI 兼容）客户端
client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)


# 时间
today = datetime.today()
today_fmt = today.strftime("%Y年%m月")
past_date = (today - timedelta(days=30)).strftime("%Y-%m-%d")
today_date_str = today.strftime("%Y-%m-%d")


# =========================
# 工具函数
# =========================
def chunk_text(text: str, chunk_size: int = 1800) -> List[str]:
    """将长文本切成多段，避免 Notion 单块过长"""
    lines = text.splitlines()
    chunks, cur, cur_len = [], [], 0
    for ln in lines:
        ln_len = len(ln) + 1
        if cur_len + ln_len > chunk_size and cur:
            chunks.append("\n".join(cur))
            cur, cur_len = [], 0
        cur.append(ln)
        cur_len += ln_len
    if cur:
        chunks.append("\n".join(cur))
    return chunks


def build_text_blocks(block_type: str, text: str) -> List[Dict]:
    blocks = []
    for piece in chunk_text(text, 1800):
        blocks.append({
            "object": "block",
            "type": block_type,
            block_type: {
                "rich_text": [{"type": "text", "text": {"content": piece}}]
            }
        })
    return blocks


def markdown_to_notion_blocks(markdown_text: str) -> List[Dict]:
    """将基础 Markdown（标题/列表/段落）转换为 Notion blocks。"""
    blocks: List[Dict] = []
    paragraph_lines: List[str] = []

    def flush_paragraph():
        if paragraph_lines:
            text = "\n".join(paragraph_lines).strip()
            blocks.extend(build_text_blocks("paragraph", text))
            paragraph_lines.clear()

    for raw_line in markdown_text.splitlines():
        line = raw_line.rstrip()
        if not line.strip():
            flush_paragraph()
            continue
        if line.startswith("### "):
            flush_paragraph()
            blocks.extend(build_text_blocks("heading_3", line[4:].strip()))
            continue
        if line.startswith("## "):
            flush_paragraph()
            blocks.extend(build_text_blocks("heading_2", line[3:].strip()))
            continue
        if line.startswith("# "):
            flush_paragraph()
            blocks.extend(build_text_blocks("heading_1", line[2:].strip()))
            continue
        if line.startswith(("- ", "* ")):
            flush_paragraph()
            blocks.extend(build_text_blocks("bulleted_list_item", line[2:].strip()))
            continue
        if re.match(r"^\d+\.\s+", line):
            flush_paragraph()
            blocks.extend(build_text_blocks("numbered_list_item", re.sub(r"^\d+\.\s+", "", line)))
            continue
        paragraph_lines.append(line)

    flush_paragraph()
    return blocks


def notion_append_blocks(page_or_block_id: str, blocks: List[Dict]):
    """将 Notion blocks 追加到指定页面/块下"""
    url = f"https://api.notion.com/v1/blocks/{page_or_block_id}/children"
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json"
    }

    payload = {"children": blocks}
    # 轻量重试
    for attempt in range(3):
        res = requests.patch(url, headers=headers, json=payload, timeout=30)
        if res.status_code in (200, 201):
            print("Notion push OK.")
            return
        print(f"Notion push failed [{res.status_code}]: {res.text}")
        if res.status_code in (429, 500, 502, 503, 504):
            time.sleep(2 ** attempt)
            continue
        break
    raise RuntimeError("Push to Notion failed.")


# =========================
# 业务逻辑
# =========================
def fetch_medrxiv_papers(max_results=12) -> List[str]:
    """
    抓取 medRxiv 最近 30 天内的论文，并按关键词在标题/摘要中过滤。
    medRxiv 的公开 API（api.biorxiv.org）本身不支持关键词检索，
    只能按日期区间分页拉取，再在本地做关键词匹配。
    """
    keywords = [kw.strip().lower() for kw in QUERY_KEYWORDS.split(",") if kw.strip()]
    base_url = f"https://api.biorxiv.org/details/medrxiv/{past_date}/{today_date_str}"

    papers: List[str] = []
    cursor = 0
    max_pages = 20  # 安全上限，避免无限翻页

    for _ in range(max_pages):
        url = f"{base_url}/{cursor}"
        try:
            res = requests.get(url, timeout=30)
            res.raise_for_status()
            data = res.json()
        except requests.RequestException as exc:
            print(f"medRxiv fetch failed: {exc}")
            break

        collection = data.get("collection", [])
        if not collection:
            break

        for item in collection:
            title = (item.get("title") or "").strip().replace("\n", " ")
            abstract = (item.get("abstract") or "").lower()
            title_lower = title.lower()
            if keywords and not any(kw in title_lower or kw in abstract for kw in keywords):
                continue
            date = item.get("date", "")
            doi = item.get("doi", "")
            link = f"https://doi.org/{doi}" if doi else ""
            papers.append(f"- [{date}] {title} ({link})")
            if len(papers) >= max_results:
                break

        if len(papers) >= max_results:
            break

        cursor += len(collection)
        messages = data.get("messages") or [{}]
        try:
            total_count = int(messages[0].get("total", 0))
        except (ValueError, TypeError, IndexError):
            total_count = 0
        if cursor >= total_count:
            break

    if not papers:
        papers.append("- （近30天未抓到相关 medRxiv 论文）")
    return papers[:max_results]


def fetch_pubmed_papers(max_results=12) -> List[str]:
    """抓取 PubMed 最近 30 天内匹配关键词的论文（NCBI E-utilities）。"""
    keywords = [kw.strip() for kw in QUERY_KEYWORDS.split(",") if kw.strip()]
    term = " AND ".join(keywords) if keywords else "kidney"

    esearch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    esearch_params = {
        "db": "pubmed",
        "term": term,
        "retmax": max_results,
        "sort": "date",
        "reldate": 30,
        "datetype": "pdat",
        "retmode": "json"
    }
    try:
        res = requests.get(esearch_url, params=esearch_params, timeout=30)
        res.raise_for_status()
        id_list = res.json().get("esearchresult", {}).get("idlist", [])
    except requests.RequestException as exc:
        print(f"PubMed esearch failed: {exc}")
        return ["- （PubMed 检索失败）"]

    if not id_list:
        return ["- （近30天未抓到相关 PubMed 论文）"]

    esummary_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
    esummary_params = {
        "db": "pubmed",
        "id": ",".join(id_list),
        "retmode": "json"
    }

    papers: List[str] = []
    try:
        res = requests.get(esummary_url, params=esummary_params, timeout=30)
        res.raise_for_status()
        result = res.json().get("result", {})
        for pmid in result.get("uids", id_list):
            item = result.get(pmid, {})
            title = (item.get("title") or "").strip().replace("\n", " ")
            date = item.get("pubdate", "")
            link = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
            papers.append(f"- [{date}] {title} ({link})")
    except requests.RequestException as exc:
        print(f"PubMed esummary failed: {exc}")
        return ["- （PubMed 摘要抓取失败）"]

    if not papers:
        papers.append("- （近30天未抓到相关 PubMed 论文）")
    return papers[:max_results]


def generate_summary_from_papers(
    medrxiv_papers: List[str],
    pubmed_papers: List[str]
) -> str:
    """用 DeepSeek 生成 Markdown 总结（OpenAI 兼容 Chat Completions）"""
    medrxiv_markdown = "\n".join(medrxiv_papers) if medrxiv_papers else "- （近30天未抓到相关 medRxiv 论文）"
    pubmed_markdown = "\n".join(pubmed_papers) if pubmed_papers else "- （近30天未抓到相关 PubMed 论文）"
    prompt = f"""
以下是近 30 天内与“{QUERY_KEYWORDS}”相关的 medRxiv 论文列表，以及 PubMed 论文列表，请根据它们总结当前该领域的关键趋势、热点方向和研究关注点。输出请使用 Markdown，并按以下格式：

## {today_fmt} 研究热点论文总结

### 🔍 趋势概览
（由模型生成的简洁要点，避免空话套话，尽量引用论文中的可验证信号）

### 📄 medRxiv 论文列表
{medrxiv_markdown}

### 📄 PubMed 论文列表
{pubmed_markdown}
""".strip()

    # 轻量重试
    for attempt in range(3):
        try:
            resp = client.chat.completions.create(
                model="deepseek-reasoner",  # 或 "deepseek-reasoner"
                messages=[
                    {"role": "system", "content": "你是一位专业的生物医学研究分析助手"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5
            )
            return resp.choices[0].message.content
        except Exception as e:
            print(f"DeepSeek API 调用失败（第 {attempt+1} 次）: {e}")
            time.sleep(1.5 * (attempt + 1))
    raise RuntimeError("DeepSeek 生成失败，请检查网络/API Key/额度。")


def main():
    print(f"Keywords: {QUERY_KEYWORDS}")
    print("Fetching medRxiv...")
    medrxiv_papers = fetch_medrxiv_papers(max_results=12)
    print("Fetching PubMed...")
    pubmed_papers = fetch_pubmed_papers(max_results=12)

    print("Generating summary with DeepSeek...")
    summary_md = generate_summary_from_papers(medrxiv_papers, pubmed_papers)
    notion_blocks = markdown_to_notion_blocks(summary_md)

    print("Pushing to Notion...")
    notion_append_blocks(PAGE_ID, notion_blocks)

    print("Done.")


if __name__ == "__main__":
    main()

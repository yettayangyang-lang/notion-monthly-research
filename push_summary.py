"""
models.py

Data models for Kidney Literature Monitor.

所有数据源（PubMed、medRxiv）最终都会转换成统一的数据结构，
便于后续去重、AI总结、Notion写入和CSV导出。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass(slots=True)
class Paper:
    """
    Unified literature model.
    """

    # ---------- Basic ----------
    source: str
    title: str
    abstract: str = ""

    # ---------- Publication ----------
    journal: str = ""
    published_date: str = ""

    # ---------- IDs ----------
    doi: Optional[str] = None
    pmid: Optional[str] = None
    pmcid: Optional[str] = None

    # ---------- Authors ----------
    authors: List[str] = field(default_factory=list)

    # ---------- URL ----------
    url: str = ""

    # ---------- Metadata ----------
    publication_type: List[str] = field(default_factory=list)
    mesh_terms: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)

    volume: str = ""
    issue: str = ""
    pages: str = ""

    language: str = "English"

    is_preprint: bool = False

    # ---------- AI ----------
    ai_summary: str = ""
    ai_tags: List[str] = field(default_factory=list)

    # ---------- Reserved ----------
    extra: dict = field(default_factory=dict)

    @property
    def author_string(self) -> str:
        return ", ".join(self.authors)

    @property
    def citation(self) -> str:

        parts = []

        if self.author_string:
            parts.append(self.author_string)

        if self.title:
            parts.append(self.title)

        if self.journal:
            parts.append(self.journal)

        if self.published_date:
            parts.append(self.published_date)

        return ". ".join(parts)

    @property
    def unique_id(self) -> str:
        """
        用于去重。

        Priority

        DOI
        PMID
        Title
        """

        if self.doi:
            return self.doi.lower().strip()

        if self.pmid:
            return f"PMID:{self.pmid}"

        return self.title.lower().strip()

    def to_markdown(self) -> str:

        md = []

        md.append(f"## {self.title}")
        md.append("")

        md.append(f"- Source: {self.source}")

        if self.journal:
            md.append(f"- Journal: {self.journal}")

        if self.published_date:
            md.append(f"- Published: {self.published_date}")

        if self.author_string:
            md.append(f"- Authors: {self.author_string}")

        if self.doi:
            md.append(f"- DOI: {self.doi}")

        if self.pmid:
            md.append(f"- PMID: {self.pmid}")

        if self.url:
            md.append(f"- URL: {self.url}")

        if self.publication_type:
            md.append(
                "- Publication Type: "
                + ", ".join(self.publication_type)
            )

        if self.mesh_terms:
            md.append(
                "- MeSH: "
                + ", ".join(self.mesh_terms)
            )

        md.append("")

        if self.abstract:

            md.append("### Abstract")
            md.append("")
            md.append(self.abstract)
            md.append("")

        if self.ai_summary:

            md.append("### AI Summary")
            md.append("")
            md.append(self.ai_summary)
            md.append("")

        return "\n".join(md)

    def to_csv_row(self):

        return {

            "Source": self.source,

            "Title": self.title,

            "Journal": self.journal,

            "Published": self.published_date,

            "Authors": self.author_string,

            "DOI": self.doi or "",

            "PMID": self.pmid or "",

            "PMCID": self.pmcid or "",

            "URL": self.url,

            "PublicationType": "; ".join(
                self.publication_type
            ),

            "MeshTerms": "; ".join(
                self.mesh_terms
            ),

            "Abstract": self.abstract,

            "AISummary": self.ai_summary,
        }




        """
        
config.py

统一读取所有配置。

所有模块都不要直接读取环境变量，
而是：

from config import settings

保证整个项目配置统一。

"""

from dataclasses import dataclass
from datetime import datetime, timedelta
import os

from dotenv import load_dotenv


# 自动读取 .env
load_dotenv()


@dataclass(frozen=True)
class Settings:
    """
    项目配置
    """

    # =====================
    # DeepSeek
    # =====================

    DEEPSEEK_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

    DEEPSEEK_BASE_URL: str = os.getenv(
        "OPENAI_BASE_URL",
        "https://api.deepseek.com"
    )

    MODEL_NAME: str = os.getenv(
        "MODEL_NAME",
        "deepseek-reasoner"
    )

    # =====================
    # Notion
    # =====================

    NOTION_TOKEN: str = os.getenv(
        "NOTION_TOKEN",
        ""
    )

    PAGE_ID: str = os.getenv(
        "PAGE_ID",
        ""
    )

    # =====================
    # Literature Search
    # =====================

    QUERY: str = os.getenv(
        "QUERY",
        "(kidney OR renal) AND (C3 OR complement C3) AND macrophage"
    )

    DAYS: int = int(
        os.getenv(
            "DAYS",
            "30"
        )
    )

    MAX_RESULTS: int = int(
        os.getenv(
            "MAX_RESULTS",
            "30"
        )
    )

    LANGUAGE: str = os.getenv(
        "LANGUAGE",
        "english"
    )

    # =====================
    # Output
    # =====================

    OUTPUT_DIR: str = os.getenv(
        "OUTPUT_DIR",
        "outputs"
    )

    REPORT_DIR: str = os.getenv(
        "REPORT_DIR",
        "outputs/reports"
    )

    CSV_DIR: str = os.getenv(
        "CSV_DIR",
        "outputs/csv"
    )

    LOG_DIR: str = os.getenv(
        "LOG_DIR",
        "logs"
    )

    # =====================
    # Runtime
    # =====================

    REQUEST_TIMEOUT: int = int(
        os.getenv(
            "REQUEST_TIMEOUT",
            "30"
        )
    )

    RETRY: int = int(
        os.getenv(
            "RETRY",
            "3"
        )
    )

    USER_AGENT: str = (
        "Kidney-Literature-Monitor/1.0"
    )

    @property
    def today(self):
        return datetime.today()

    @property
    def start_date(self):
        return self.today - timedelta(days=self.DAYS)

    @property
    def report_title(self):

        return self.today.strftime(
            "%Y年%m月 Kidney/C3/Macrophage 文献热点分析"
        )

    @property
    def csv_filename(self):

        return self.today.strftime(
            "%Y_%m_papers.csv"
        )

    @property
    def markdown_filename(self):

        return self.today.strftime(
            "%Y_%m_report.md"
        )


settings = Settings()



"""
utils.py

Common utility functions for Kidney Literature Monitor.

This module intentionally contains only generic helper functions.
No business logic should be placed here.
"""

from __future__ import annotations

import csv
import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Iterable, List

from models import Paper


# ==========================================================
# Logging
# ==========================================================

LOGGER_NAME = "KidneyMonitor"


def setup_logger(level=logging.INFO) -> logging.Logger:
    """
    Configure project logger.

    Safe to call multiple times.
    """

    logger = logging.getLogger(LOGGER_NAME)

    if logger.handlers:
        return logger

    logger.setLevel(level)

    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s - %(message)s",
        "%Y-%m-%d %H:%M:%S",
    )

    console = logging.StreamHandler()
    console.setFormatter(formatter)

    logger.addHandler(console)

    return logger


logger = setup_logger()


# ==========================================================
# Time
# ==========================================================

def today_string() -> str:
    """
    Example
    -------
    2026-07-03
    """

    return datetime.now().strftime("%Y-%m-%d")


def timestamp() -> str:
    """
    Example
    -------
    20260703_104512
    """

    return datetime.now().strftime("%Y%m%d_%H%M%S")


# ==========================================================
# File
# ==========================================================

def ensure_directory(path: str | Path) -> None:
    """
    Create directory if it does not exist.
    """

    Path(path).mkdir(
        parents=True,
        exist_ok=True,
    )


def save_text(
    text: str,
    filename: str,
) -> None:
    """
    Save UTF-8 text.
    """

    Path(filename).parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with open(
        filename,
        "w",
        encoding="utf-8",
    ) as f:

        f.write(text)


def load_text(
    filename: str,
) -> str:
    """
    Load UTF-8 text.
    """

    with open(
        filename,
        "r",
        encoding="utf-8",
    ) as f:

        return f.read()


def save_json(
    data,
    filename: str,
) -> None:
    """
    Save JSON.
    """

    Path(filename).parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with open(
        filename,
        "w",
        encoding="utf-8",
    ) as f:

        json.dump(
            data,
            f,
            indent=2,
            ensure_ascii=False,
        )


# ==========================================================
# CSV
# ==========================================================

def export_csv(
    papers: List[Paper],
    filename: str,
) -> None:
    """
    Export papers to CSV.
    """

    if not papers:
        logger.warning("No papers to export.")
        return

    Path(filename).parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    rows = [
        paper.to_csv_row()
        for paper in papers
    ]

    fieldnames = list(
        rows[0].keys()
    )

    with open(
        filename,
        "w",
        newline="",
        encoding="utf-8",
    ) as f:

        writer = csv.DictWriter(
            f,
            fieldnames=fieldnames,
        )

        writer.writeheader()
        writer.writerows(rows)

    logger.info(
        "CSV exported: %s (%d papers)",
        filename,
        len(rows),
    )


# ==========================================================
# Markdown
# ==========================================================

def export_markdown(
    papers: List[Paper],
    filename: str,
) -> None:
    """
    Export papers to Markdown.
    """

    Path(filename).parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    content = []

    for paper in papers:

        content.append(
            paper.to_markdown()
        )

        content.append("\n---\n")

    save_text(
        "\n".join(content),
        filename,
    )


# ==========================================================
# Deduplication
# ==========================================================

def deduplicate_papers(
    papers: Iterable[Paper],
) -> List[Paper]:
    """
    Remove duplicated papers.

    Priority
    --------
    DOI
    PMID
    Title
    """

    papers = list(papers)

    unique = {}

    for paper in papers:

        unique[
            paper.unique_id
        ] = paper

    result = list(
        unique.values()
    )

    logger.info(
        "Deduplicated: %d -> %d",
        len(papers),
        len(result),
    )

    return result
    # ==========================================================
# Text Cleaning
# ==========================================================

_whitespace = re.compile(r"\s+")


def clean_text(text: str) -> str:
    """
    Normalize whitespace.

    - Remove CR/LF
    - Collapse multiple spaces
    - Strip leading/trailing spaces
    """

    if not text:
        return ""

    text = text.replace("\r", " ")
    text = text.replace("\n", " ")

    text = _whitespace.sub(
        " ",
        text,
    )

    return text.strip()


# ==========================================================
# DOI
# ==========================================================

_DOI_PATTERN = re.compile(
    r"10\.\d{4,9}/[-._;()/:A-Z0-9]+",
    re.IGNORECASE,
)


def extract_doi(text: str):
    """
    Extract DOI from arbitrary text.

    Returns
    -------
    str | None
    """

    if not text:
        return None

    match = _DOI_PATTERN.search(text)

    if match:
        return match.group(0)

    return None


# ==========================================================
# Statistics
# ==========================================================

def print_statistics(
    papers: List[Paper],
) -> None:
    """
    Print simple project statistics.
    """

    total = len(papers)

    pubmed = sum(
        paper.source.lower() == "pubmed"
        for paper in papers
    )

    medrxiv = sum(
        paper.source.lower() == "medrxiv"
        for paper in papers
    )

    logger.info("")
    logger.info("========== Summary ==========")
    logger.info("Total papers : %d", total)
    logger.info("PubMed       : %d", pubmed)
    logger.info("medRxiv      : %d", medrxiv)
    logger.info("=============================")


# ==========================================================
# Collection Helpers
# ==========================================================

def chunk_list(
    items,
    chunk_size: int,
):
    """
    Yield successive chunks.

    Example
    -------
    [1,2,3,4,5], chunk_size=2

    ->
    [1,2]
    [3,4]
    [5]
    """

    if chunk_size <= 0:
        raise ValueError(
            "chunk_size must be positive."
        )

    for i in range(
        0,
        len(items),
        chunk_size,
    ):
        yield items[
            i:i + chunk_size
        ]


# ==========================================================
# Dictionary Helpers
# ==========================================================

def safe_get(
    dictionary,
    *keys,
    default=None,
):
    """
    Safely retrieve nested dictionary values.

    Example
    -------
    safe_get(data, "a", "b", "c")
    """

    current = dictionary

    for key in keys:

        if not isinstance(
            current,
            dict,
        ):
            return default

        current = current.get(key)

        if current is None:
            return default

    return current




"""
pubmed.py

Retrieve literature from PubMed using the NCBI E-utilities API.

Workflow

ESearch
    ↓
PMID list
    ↓
EFetch
    ↓
XML
    ↓
Paper objects
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import List

import requests

from config import settings
from models import Paper
from utils import (
    clean_text,
    extract_doi,
    logger,
)

BASE_URL = (
    "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
)


class PubMedClient:

    def __init__(self):

        self.session = requests.Session()

        self.session.headers.update(
            {
                "User-Agent": settings.USER_AGENT,
            }
        )

    # ======================================================
    # Public
    # ======================================================

    def search(self) -> List[Paper]:

        pmids = self._search_pmids()

        if not pmids:

            logger.info("No PubMed papers found.")

            return []

        logger.info(
            "PubMed returned %d PMIDs.",
            len(pmids),
        )

        return self._fetch_details(pmids)

    # ======================================================
    # Search
    # ======================================================

    def _search_pmids(self) -> List[str]:

        url = f"{BASE_URL}/esearch.fcgi"

        params = {

            "db": "pubmed",

            "term": settings.QUERY,

            "retmode": "json",

            "retmax": settings.MAX_RESULTS,

            "datetype": "pdat",

            "reldate": settings.DAYS,

            "sort": "date",
        }

        response = self.session.get(

            url,

            params=params,

            timeout=settings.REQUEST_TIMEOUT,

        )

        response.raise_for_status()

        data = response.json()

        return data.get(
            "esearchresult",
            {},
        ).get(
            "idlist",
            [],
        )

    # ======================================================
    # Fetch
    # ======================================================

    def _fetch_details(
        self,
        pmids: List[str],
    ) -> List[Paper]:

        url = f"{BASE_URL}/efetch.fcgi"

        response = self.session.get(

            url,

            params={

                "db": "pubmed",

                "id": ",".join(pmids),

                "retmode": "xml",

            },

            timeout=settings.REQUEST_TIMEOUT,

        )

        response.raise_for_status()

        root = ET.fromstring(
            response.text
        )

        papers = []

        for article in root.findall(
            ".//PubmedArticle"
        ):

            try:

                papers.append(
                    self._parse_article(
                        article
                    )
                )

            except Exception as e:

                logger.exception(
                    "Failed to parse article: %s",
                    e,
                )

        return papers

    # ======================================================
    # Parse
    # ======================================================

    def _parse_article(
        self,
        article,
    ) -> Paper:

        medline = article.find(
            "MedlineCitation"
        )

        article_node = medline.find(
            "Article"
        )

        title = clean_text(

            "".join(
                article_node.findtext(
                    "ArticleTitle",
                    default="",
                )
            )
        )

        abstract = self._parse_abstract(
            article_node
        )

        journal = clean_text(

            article_node.findtext(
                "Journal/Title",
                default="",
            )
        )

        authors = self._parse_authors(
            article_node
        )

        published = self._parse_date(
            article_node
        )

        pmid = medline.findtext(
            "PMID",
            default="",
        )

        doi = self._parse_doi(
            article
        )

        pmcid = self._parse_pmcid(
            article
        )

        publication_type = [
            clean_text(node.text)

            for node in article.findall(
                ".//PublicationType"
            )

            if node.text
        ]

        mesh_terms = [
            clean_text(node.text)

            for node in article.findall(
                ".//MeshHeading/DescriptorName"
            )

            if node.text
        ]

        volume = article_node.findtext(
            "Journal/JournalIssue/Volume",
            default="",
        )

        issue = article_node.findtext(
            "Journal/JournalIssue/Issue",
            default="",
        )

        pages = article_node.findtext(
            "Pagination/MedlinePgn",
            default="",
        )

        language = article_node.findtext(
            "Language",
            default="English",
        )

        url = (
            f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
            if pmid
            else ""
        )

        return Paper(

            source="PubMed",

            title=title,

            abstract=abstract,

            journal=journal,

            published_date=published,

            doi=doi,

            pmid=pmid,

            pmcid=pmcid,

            authors=authors,

            url=url,

            publication_type=publication_type,

            mesh_terms=mesh_terms,

            volume=volume,

            issue=issue,

            pages=pages,

            language=language,

            is_preprint=False,
        )
            # ======================================================
    # Helpers
    # ======================================================

    def _parse_abstract(
        self,
        article_node,
    ) -> str:

        abstract_node = article_node.find(
            "Abstract"
        )

        if abstract_node is None:
            return ""

        texts = []

        for node in abstract_node.findall(
            "AbstractText"
        ):

            label = node.attrib.get(
                "Label",
                ""
            )

            text = "".join(
                node.itertext()
            )

            text = clean_text(text)

            if not text:
                continue

            if label:
                texts.append(
                    f"{label}: {text}"
                )
            else:
                texts.append(text)

        return "\n".join(texts)

    def _parse_authors(
        self,
        article_node,
    ) -> List[str]:

        authors = []

        author_list = article_node.find(
            "AuthorList"
        )

        if author_list is None:
            return authors

        for author in author_list.findall(
            "Author"
        ):

            collective = author.findtext(
                "CollectiveName"
            )

            if collective:
                authors.append(
                    clean_text(collective)
                )
                continue

            last = author.findtext(
                "LastName",
                default="",
            )

            fore = author.findtext(
                "ForeName",
                default="",
            )

            name = clean_text(
                f"{fore} {last}"
            )

            if name:
                authors.append(name)

        return authors

    def _parse_date(
        self,
        article_node,
    ) -> str:

        issue = article_node.find(
            "Journal/JournalIssue/PubDate"
        )

        if issue is None:
            return ""

        year = issue.findtext(
            "Year",
            default="",
        )

        month = issue.findtext(
            "Month",
            default="",
        )

        day = issue.findtext(
            "Day",
            default="",
        )

        medline = issue.findtext(
            "MedlineDate",
            default="",
        )

        if year:

            parts = [year]

            if month:
                parts.append(month)

            if day:
                parts.append(day)

            return "-".join(parts)

        return medline

    def _parse_doi(
        self,
        article,
    ):

        for node in article.findall(
            ".//ArticleId"
        ):

            if (
                node.attrib.get("IdType")
                == "doi"
            ):

                return clean_text(
                    node.text or ""
                )

        text = ET.tostring(
            article,
            encoding="unicode",
        )

        return extract_doi(text)

    def _parse_pmcid(
        self,
        article,
    ):

        for node in article.findall(
            ".//ArticleId"
        ):

            if (
                node.attrib.get("IdType")
                == "pmc"
            ):

                return clean_text(
                    node.text or ""
                )

        return None


# ==========================================================
# Convenience Function
# ==========================================================

def search_pubmed() -> List[Paper]:
    """
    Retrieve PubMed papers.

    Returns
    -------
    List[Paper]
    """

    client = PubMedClient()

    return client.search()



"""
medrxiv.py

Retrieve preprints from the medRxiv API.

Workflow

API
    ↓
JSON
    ↓
Paper objects
"""

from __future__ import annotations

from datetime import datetime
from typing import List

import requests

from config import settings
from models import Paper
from utils import (
    clean_text,
    logger,
)

BASE_URL = "https://api.medrxiv.org/details/medrxiv"


class MedRxivClient:

    def __init__(self):

        self.session = requests.Session()

        self.session.headers.update(
            {
                "User-Agent": settings.USER_AGENT,
            }
        )

    # ======================================================
    # Public
    # ======================================================

    def search(self) -> List[Paper]:

        start = settings.start_date.strftime(
            "%Y-%m-%d"
        )

        end = settings.today.strftime(
            "%Y-%m-%d"
        )

        url = (
            f"{BASE_URL}/"
            f"{start}/{end}"
        )

        response = self.session.get(
            url,
            timeout=settings.REQUEST_TIMEOUT,
        )

        response.raise_for_status()

        data = response.json()

        collection = data.get(
            "collection",
            []
        )

        logger.info(
            "medRxiv returned %d records.",
            len(collection),
        )

        papers = []

        query = settings.QUERY.lower()

        for item in collection:

            if not self._match_query(
                item,
                query,
            ):
                continue

            papers.append(
                self._parse_record(item)
            )

            if len(papers) >= settings.MAX_RESULTS:
                break

        return papers

    # ======================================================
    # Parse
    # ======================================================

    def _parse_record(
        self,
        item,
    ) -> Paper:

        title = clean_text(
            item.get("title", "")
        )

        abstract = clean_text(
            item.get("abstract", "")
        )

        authors = self._parse_authors(
            item.get("authors", "")
        )

        doi = clean_text(
            item.get("doi", "")
        )

        published = clean_text(
            item.get("date", "")
        )

        journal = clean_text(
            item.get(
                "server",
                "medRxiv",
            )
        )

        url = (
            f"https://www.medrxiv.org/content/"
            f"{doi}v1"
            if doi
            else ""
        )

        keywords = []

        category = clean_text(
            item.get(
                "category",
                "",
            )
        )

        if category:
            keywords.append(category)

        return Paper(

            source="medRxiv",

            title=title,

            abstract=abstract,

            journal=journal,

            published_date=published,

            doi=doi,

            authors=authors,

            url=url,

            keywords=keywords,

            publication_type=[
                "Preprint"
            ],

            language="English",

            is_preprint=True,
        )

    # ======================================================
    # Helpers
    # ======================================================

    def _parse_authors(
        self,
        author_string: str,
    ) -> List[str]:

        if not author_string:
            return []

        authors = []

        for author in author_string.split(";"):

            author = clean_text(author)

            if author:
                authors.append(author)

        return authors

    def _match_query(
        self,
        item,
        query: str,
    ) -> bool:
        """
        Simple keyword matching.

        The medRxiv API does not support PubMed-style
        Boolean queries, so we perform a lightweight
        local filter using the title and abstract.
        """

        if not query:
            return True

        title = clean_text(
            item.get("title", "")
        ).lower()

        abstract = clean_text(
            item.get("abstract", "")
        ).lower()

        text = f"{title} {abstract}"

        # Extract keywords from the Boolean query
        keywords = []

        for token in (
            query.replace("(", " ")
                 .replace(")", " ")
                 .replace("and", " ")
                 .replace("or", " ")
                 .split()
        ):
            token = token.strip()

            if len(token) < 2:
                continue

            keywords.append(token)

        keywords = list(dict.fromkeys(keywords))

        if not keywords:
            return True

        return any(
            keyword in text
            for keyword in keywords
        )


# ==========================================================
# Convenience Function
# ==========================================================

def search_medrxiv() -> List[Paper]:
    """
    Retrieve medRxiv preprints.

    Returns
    -------
    List[Paper]
    """

    client = MedRxivClient()

    return client.search()

"""
prompt.py

Prompt templates for AI literature summarization.

All prompts should be generated through the helper
functions below so that the wording remains consistent
throughout the project.
"""

from __future__ import annotations

from typing import List

from models import Paper


SYSTEM_PROMPT = """
You are a biomedical research assistant.

Your task is to analyze scientific literature related to kidney disease,
complement biology, macrophages and immunology.

Requirements:

- Be scientifically rigorous.
- Never fabricate findings.
- Distinguish conclusions from hypotheses.
- Keep summaries concise.
- Use professional academic language.
- Respond in Markdown.
""".strip()


def build_summary_prompt(paper: Paper) -> str:
    """
    Build prompt for a single paper.
    """

    return f"""
Please read the following scientific paper.

Title:
{paper.title}

Journal:
{paper.journal}

Published:
{paper.published_date}

Abstract:
{paper.abstract}

Please provide:

# Summary

Summarize the study in approximately 150 words.

# Key Findings

List 3–5 major findings.

# Novelty

Explain what is new about this study.

# Kidney/C3/Macrophage Relevance

Explain why this paper is relevant to kidney disease,
complement C3 or macrophage biology.

# Limitations

Briefly describe the major limitations.

# Suggested Tags

Return 3–8 concise keywords.

Respond in Markdown only.
""".strip()


def build_daily_report_prompt(
    papers: List[Paper],
) -> str:
    """
    Build prompt for a multi-paper literature report.
    """

    literature = []

    for i, paper in enumerate(papers, start=1):

        literature.append(
            f"""
Paper {i}

Title:
{paper.title}

Journal:
{paper.journal}

Published:
{paper.published_date}

Abstract:
{paper.abstract}
""".strip()
        )

    paper_text = "\n\n".join(literature)

    return f"""
You are preparing a monthly literature report for a kidney disease research group.

Below are recently published papers.

{paper_text}

Please produce a Markdown report with the following sections.

# Research Highlights

Summarize the most important advances.

# Emerging Trends

Identify common themes and new research directions.

# Complement C3

Summarize all findings involving complement C3.

# Macrophages

Summarize macrophage-related findings.

# Kidney Disease

Summarize implications for kidney disease.

# Potential Clinical Impact

Discuss possible translational value.

# Future Research Directions

Suggest promising research opportunities.

The report should be concise, scientifically rigorous,
well organized and suitable for direct upload to Notion.

Respond in Markdown only.
""".strip()

"""
deepseek.py

DeepSeek API client for literature summarization.
"""

from __future__ import annotations

from typing import List

from openai import OpenAI

from config import settings
from models import Paper
from prompt import (
    SYSTEM_PROMPT,
    build_summary_prompt,
    build_daily_report_prompt,
)
from utils import (
    chunk_list,
    logger,
)


class DeepSeekClient:
    """
    Wrapper of the OpenAI-compatible DeepSeek API.
    """

    def __init__(self):

        self.client = OpenAI(
            api_key=settings.DEEPSEEK_API_KEY,
            base_url=settings.DEEPSEEK_BASE_URL,
        )

        self.model = settings.MODEL_NAME

    # ======================================================
    # Internal
    # ======================================================

    def _chat(
        self,
        prompt: str,
    ) -> str:

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT,
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            temperature=0.2,
        )

        return (
            response.choices[0]
            .message.content
            .strip()
        )

    # ======================================================
    # Public
    # ======================================================

    def summarize_paper(
        self,
        paper: Paper,
    ) -> str:
        """
        Generate AI summary for one paper.
        """

        logger.info(
            "Summarizing: %s",
            paper.title,
        )

        prompt = build_summary_prompt(
            paper
        )

        summary = self._chat(prompt)

        paper.ai_summary = summary

        return summary

    def summarize_papers(
        self,
        papers: List[Paper],
    ) -> None:
        """
        Summarize papers one by one.
        """

        for paper in papers:

            try:

                self.summarize_paper(
                    paper
                )

            except Exception as e:

                logger.exception(
                    "AI summary failed: %s",
                    e,
                )

                paper.ai_summary = ""


    def generate_report(
        self,
        papers: List[Paper],
    ) -> str:
        """
        Generate a literature report for a collection
        of papers.
        """

        if not papers:
            return "# No literature found."

        logger.info(
            "Generating report (%d papers)...",
            len(papers),
        )

        prompt = build_daily_report_prompt(
            papers
        )

        return self._chat(prompt)

    def batch_generate_report(
        self,
        papers: List[Paper],
        batch_size: int = 20,
    ) -> str:
        """
        Generate reports in batches for large
        literature collections, then merge them.
        """

        if not papers:
            return "# No literature found."

        # Small collections can be processed directly.
        if len(papers) <= batch_size:
            return self.generate_report(papers)

        logger.info(
            "Large collection detected (%d papers), "
            "splitting into batches of %d.",
            len(papers),
            batch_size,
        )

        partial_reports = []

        for index, batch in enumerate(
            chunk_list(papers, batch_size),
            start=1,
        ):

            logger.info(
                "Generating batch %d...",
                index,
            )

            partial_reports.append(
                self.generate_report(batch)
            )

        merge_prompt = f"""
The following are several independently generated
literature reports.

Please merge them into ONE final report.

Requirements:

- Remove duplicated information.
- Preserve all important findings.
- Organize logically.
- Use Markdown.
- Keep a professional scientific style.

Reports:

{chr(10).join(partial_reports)}
""".strip()

        logger.info(
            "Merging partial reports..."
        )

        return self._chat(merge_prompt)


# ==========================================================
# Convenience Function
# ==========================================================

def create_client() -> DeepSeekClient:
    """
    Create a DeepSeek client.
    """

    return DeepSeekClient()




"""
notion.py

Upload literature reports to Notion.
"""

from __future__ import annotations

import requests

from config import settings
from utils import logger


NOTION_VERSION = "2022-06-28"


class NotionClient:
    """
    Simple Notion API client.
    """

    def __init__(self):

        self.headers = {

            "Authorization": f"Bearer {settings.NOTION_TOKEN}",

            "Content-Type": "application/json",

            "Notion-Version": NOTION_VERSION,
        }

    # ======================================================
    # Public
    # ======================================================

    def append_markdown(
        self,
        markdown: str,
        title: str | None = None,
    ):

        """
        Append a Markdown report to an existing Notion page.
        """

        if title is None:

            title = settings.report_title

        children = []

        children.append(

            self._heading_block(title)

        )

        children.extend(

            self._markdown_to_blocks(markdown)

        )

        url = (
            f"https://api.notion.com/v1/blocks/"
            f"{settings.PAGE_ID}/children"
        )

        payload = {

            "children": children

        }

        response = requests.patch(

            url,

            headers=self.headers,

            json=payload,

            timeout=settings.REQUEST_TIMEOUT,

        )

        response.raise_for_status()

        logger.info(

            "Notion upload completed."

        )

    # ======================================================
    # Block Builder
    # ======================================================

    def _heading_block(
        self,
        text: str,
    ):

        return {

            "object": "block",

            "type": "heading_1",

            "heading_1": {

                "rich_text": [

                    {

                        "type": "text",

                        "text": {

                            "content": text

                        },

                    }

                ]

            }

        }

    def _paragraph_block(
        self,
        text: str,
    ):

        return {

            "object": "block",

            "type": "paragraph",

            "paragraph": {

                "rich_text": [

                    {

                        "type": "text",

                        "text": {

                            "content": text

                        },

                    }

                ]

            }

        }


    def _heading2_block(
        self,
        text: str,
    ):

        return {

            "object": "block",

            "type": "heading_2",

            "heading_2": {

                "rich_text": [

                    {

                        "type": "text",

                        "text": {

                            "content": text

                        },

                    }

                ]

            }

        }

    def _heading3_block(
        self,
        text: str,
    ):

        return {

            "object": "block",

            "type": "heading_3",

            "heading_3": {

                "rich_text": [

                    {

                        "type": "text",

                        "text": {

                            "content": text

                        },

                    }

                ]

            }

        }

    # ======================================================
    # Markdown
    # ======================================================

    def _markdown_to_blocks(
        self,
        markdown: str,
    ):

        """
        A lightweight Markdown parser.

        Supported:
        - # Heading
        - ## Heading
        - ### Heading
        - Paragraph
        """

        blocks = []

        lines = markdown.splitlines()

        for line in lines:

            line = line.strip()

            if not line:
                continue

            if line.startswith("### "):

                blocks.append(

                    self._heading3_block(
                        line[4:]
                    )

                )

                continue

            if line.startswith("## "):

                blocks.append(

                    self._heading2_block(
                        line[3:]
                    )

                )

                continue

            if line.startswith("# "):

                blocks.append(

                    self._heading_block(
                        line[2:]
                    )

                )

                continue

            blocks.append(

                self._paragraph_block(
                    line
                )

            )

        return blocks


# ==========================================================
# Convenience Function
# ==========================================================

def create_client() -> NotionClient:
    """
    Create a Notion client.
    """

    return NotionClient()

"""
main.py

Entry point for Kidney Literature Monitor.
"""

from __future__ import annotations

from pathlib import Path

from config import settings
from deepseek import create_client as create_ai_client
from medrxiv import search_medrxiv
from notion import create_client as create_notion_client
from pubmed import search_pubmed
from utils import (
    deduplicate_papers,
    ensure_directory,
    export_csv,
    print_statistics,
    save_text,
    logger,
)


def prepare_directories():
    """
    Create output directories.
    """

    ensure_directory(settings.OUTPUT_DIR)
    ensure_directory(settings.REPORT_DIR)
    ensure_directory(settings.CSV_DIR)
    ensure_directory(settings.LOG_DIR)


def retrieve_papers():
    """
    Retrieve literature from all supported sources.
    """

    logger.info("Searching PubMed...")

    pubmed = search_pubmed()

    logger.info(
        "PubMed papers: %d",
        len(pubmed),
    )

    logger.info("Searching medRxiv...")

    medrxiv = search_medrxiv()

    logger.info(
        "medRxiv papers: %d",
        len(medrxiv),
    )

    papers = deduplicate_papers(
        pubmed + medrxiv
    )

    print_statistics(
        papers
    )

    return papers


def export_results(
    papers,
):
    """
    Export CSV.
    """

    csv_path = (
        Path(settings.CSV_DIR)
        / settings.csv_filename
    )

    export_csv(
        papers,
        str(csv_path),
    )

    return csv_path


def generate_report(
    papers,
):
    """
    Generate AI report.
    """

    ai = create_ai_client()

    report = ai.generate_report(
        papers
    )

    report_path = (
        Path(settings.REPORT_DIR)
        / settings.markdown_filename
    )

    save_text(
        report,
        str(report_path),
    )

    logger.info(
        "Markdown report saved."
    )

    return report, report_path

def upload_to_notion(report: str):
    """
    Upload report to Notion.
    """

    notion = create_notion_client()

    notion.append_markdown(
        markdown=report
    )


def run_pipeline():
    """
    Full pipeline:

    1. Fetch literature
    2. Deduplicate
    3. Export CSV
    4. Generate AI report
    5. Save Markdown
    6. Upload to Notion
    """

    prepare_directories()

    papers = retrieve_papers()

    if not papers:
        logger.info("No papers found. Exit.")
        return

    export_results(papers)

    report, _ = generate_report(papers)

    upload_to_notion(report)

    logger.info("Pipeline completed successfully.")


# ==========================================================
# Entry
# ==========================================================

if __name__ == "__main__":

    run_pipeline()


def upload_to_notion(report: str):
    """
    Upload report to Notion.
    """

    notion = create_notion_client()

    notion.append_markdown(
        markdown=report
    )


def run_pipeline():
    """
    Full pipeline:

    1. Fetch literature
    2. Deduplicate
    3. Export CSV
    4. Generate AI report
    5. Save Markdown
    6. Upload to Notion
    """

    prepare_directories()

    papers = retrieve_papers()

    if not papers:
        logger.info("No papers found. Exit.")
        return

    export_results(papers)

    report, _ = generate_report(papers)

    upload_to_notion(report)

    logger.info("Pipeline completed successfully.")


# ==========================================================
# Entry
# ==========================================================

if __name__ == "__main__":

    run_pipeline()

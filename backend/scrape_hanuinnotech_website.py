"""
Crawl https://www.hanuinnotech.com and produce consolidated RAG documents.

Run: python scrape_hanuinnotech_website.py
Output: sample_docs/hanuinnotech_*.md
"""

from __future__ import annotations

import os
import re
import time
from html import unescape
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup, Tag

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_DIR = os.path.join(_BASE_DIR, "sample_docs", "_scrape_raw")
OUTPUT_DIR = os.path.join(_BASE_DIR, "sample_docs")

BASE_URL = "https://www.hanuinnotech.com/"
ALLOWED_HOSTS = {"www.hanuinnotech.com", "hanuinnotech.com"}

SEED_URLS = [
    f"{BASE_URL}",
    f"{BASE_URL}index.html",
    f"{BASE_URL}agricultureanalytics.html",
    f"{BASE_URL}dairyanalytics.html",
    f"{BASE_URL}datascienceAILabs.html",
    f"{BASE_URL}splcropsanalytics.html",
    f"{BASE_URL}smallfarminfoservices.html",
    f"{BASE_URL}agcommoditymarketsmlmodel.html",
    f"{BASE_URL}riskmodeling.html",
    f"{BASE_URL}nationalsecurity.html",
    f"{BASE_URL}equisenseai.html",
    f"{BASE_URL}sriyaagrivetmonitor.html",
    f"{BASE_URL}jobs.html",
    f"{BASE_URL}celebrating15years/index.html",
    f"{BASE_URL}download_casestudy_Amul.html",
    f"{BASE_URL}download_casestudy_Coco-Cola.html",
    f"{BASE_URL}download_casestudy_Goshalas_Cattle_Shelters_Livestock_Sanctuaries.html",
    f"{BASE_URL}download_casestudy_SKUAST_AI.html",
    f"{BASE_URL}download_casestudy_SplCrops_Tomatoes.html",
    f"{BASE_URL}download_casestudy_heatwavesandfoodsecurity.html",
    f"{BASE_URL}download_casestudy_nationalbanks.html",
    f"{BASE_URL}download_casestudy_mangoyieldanalytics.html",
    f"{BASE_URL}download_casestudy_organicmangoyieldanalytics.html",
    f"{BASE_URL}download_casestudy_fertilizerandcommoditypricesmlmodel.html",
    f"{BASE_URL}download_casestudy_mlmodelcredittoagriculture.html",
    f"{BASE_URL}Intellisys2017_September2017.html",
    f"{BASE_URL}SmartworldCongress_August2017.html",
    f"{BASE_URL}infrastructure.html",
    f"{BASE_URL}mangopricepredict.html",
    f"{BASE_URL}milktocommoditiespricepredict.html",
]

SKIP_HTML_SUFFIXES = {
    "privacypolicy.html",
    "termsofuse.html",
    "PrivacyPolicy.html",
}

SKIP_LINE_PATTERNS = [
    r"^toggle navigation",
    r"^know more",
    r"^order now",
    r"^case study$",
    r"^\*\*prev\*\*",
    r"^\*\*next\*\*",
    r"^request a demo$",
    r"^sales form:",
    r"^click to download",
    r"^please download",
    r"^\*\"\* mandatory",
    r"^download form:",
]

NOISE_TAGS = {"script", "style", "nav", "footer", "header", "noscript", "iframe"}

CONSOLIDATED_DOCS = {
    "hanuinnotech_company_overview.md": [
        "home.md", "index_html.md", "jobs_html.md", "celebrating15years_index_html.md",
        "intellisys2017_september2017_html.md", "smartworldcongress_august2017_html.md",
        "infrastructure_html.md",
    ],
    "hanuinnotech_dairy_and_livestock.md": [
        "dairyanalytics_html.md", "sriyaagrivetmonitor_html.md",
    ],
    "hanuinnotech_agriculture_analytics.md": [
        "agricultureanalytics_html.md",
    ],
    "hanuinnotech_specialty_crops.md": [
        "splcropsanalytics_html.md",
    ],
    "hanuinnotech_solutions_and_markets.md": [
        "smallfarminfoservices_html.md", "agcommoditymarketsmlmodel_html.md",
        "riskmodeling_html.md", "nationalsecurity_html.md",
        "mangopricepredict_html.md", "milktocommoditiespricepredict_html.md",
        "fertilizierpricepredict_html.md", "ruralemptogdppredict_html.md",
    ],
    "hanuinnotech_equine_and_sensors.md": [
        "equisenseai_html.md",
    ],
    "hanuinnotech_data_science_ai.md": [
        "datascienceailabs_html.md", "muraidataanalyticswhitepaper_html.md",
        "request_bookcopy_democratizationofai_html.md",
    ],
    "hanuinnotech_case_studies.md": [
        "download_casestudy_amul_html.md", "download_casestudy_coco_cola_html.md",
        "download_casestudy_goshalas_cattle_shelters_livestock_sanctuaries_html.md",
        "download_casestudy_skuast_ai_html.md", "download_casestudy_splcrops_tomatoes_html.md",
        "download_casestudy_heatwavesandfoodsecurity_html.md",
        "download_casestudy_nationalbanks_html.md", "download_casestudy_mangoyieldanalytics_html.md",
        "download_casestudy_organicmangoyieldanalytics_html.md",
        "download_casestudy_fertilizerandcommoditypricesmlmodel_html.md",
        "download_casestudy_mlmodelcredittoagriculture_html.md",
        # Rich case-study narratives also appear on product/solution pages.
        "dairyanalytics_html.md", "agricultureanalytics_html.md",
        "splcropsanalytics_html.md", "smallfarminfoservices_html.md",
        "agcommoditymarketsmlmodel_html.md", "nationalsecurity_html.md",
    ],
}

CAROUSEL_MARKERS = {
    "established excellence", "sriya agrivet monitor", "horse safety sensors",
    "supply certainty", "for agricultural economies", "vision year 2100",
}


def _normalize_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.netloc not in ALLOWED_HOSTS:
        return ""
    scheme = "https"
    host = "www.hanuinnotech.com"
    path = parsed.path or "/"
    if path.lower() in ("/index.html", "/index.htm"):
        path = "/"
    if path != "/" and path.endswith("/"):
        path = path.rstrip("/")
    return f"{scheme}://{host}{path}"


def _slug_from_url(url: str) -> str:
    path = urlparse(url).path.strip("/") or "home"
    return re.sub(r"[^a-zA-Z0-9]+", "_", path).strip("_").lower()[:80] or "home"


def _clean_text(text: str) -> str:
    text = unescape(text).replace("\xa0", " ")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _should_skip_line(line: str) -> bool:
    lower = line.lower().strip()
    if not lower or len(lower) < 2:
        return True
    for pattern in SKIP_LINE_PATTERNS:
        if re.search(pattern, lower):
            return True
    if lower in {"png", "img", "pdf", "home", "products", "solutions", "about us", "contact us"}:
        return True
    return False


def _discover_links(html: str, base: str) -> set[str]:
    soup = BeautifulSoup(html, "html.parser")
    links = set()
    for anchor in soup.find_all("a", href=True):
        href = urljoin(base, anchor["href"])
        normalized = _normalize_url(href.split("#")[0])
        if normalized:
            links.add(normalized)
    return links


def _discover_pdfs(html: str, base: str) -> set[str]:
    soup = BeautifulSoup(html, "html.parser")
    pdfs = set()
    for anchor in soup.find_all("a", href=True):
        href = anchor["href"]
        if ".pdf" not in href.lower():
            continue
        full = urljoin(base, href)
        if urlparse(full).netloc in ALLOWED_HOSTS:
            pdfs.add(full.split("#")[0])
    return pdfs


def _remove_noise(soup: BeautifulSoup) -> None:
    for tag_name in NOISE_TAGS:
        for el in soup.find_all(tag_name):
            el.decompose()
    for el in soup.select(".navbar, .carousel-control, .carousel-indicators, .breadcrumb"):
        el.decompose()


def _extract_blocks(soup: BeautifulSoup) -> list[str]:
    body = soup.body or soup
    blocks: list[str] = []
    seen: set[str] = set()

    for element in body.descendants:
        if not isinstance(element, Tag):
            continue
        if element.name in {f"h{i}" for i in range(1, 7)}:
            text = _clean_text(element.get_text(" ", strip=True))
            if _should_skip_line(text):
                continue
            level = min(int(element.name[1]), 6)
            block = f"{'#' * level} {text}"
            key = text.lower()
            if key not in seen:
                seen.add(key)
                blocks.append(block)
        elif element.name == "p":
            text = _clean_text(element.get_text(" ", strip=True))
            if _should_skip_line(text) or len(text) < 30:
                continue
            key = text.lower()
            if key not in seen:
                seen.add(key)
                blocks.append(text)
        elif element.name == "li":
            text = _clean_text(element.get_text(" ", strip=True))
            if _should_skip_line(text) or len(text) < 20:
                continue
            item = f"- {text}"
            key = text.lower()
            if key not in seen:
                seen.add(key)
                blocks.append(item)

    return blocks


def _page_to_markdown(url: str, html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    title = _clean_text(soup.title.get_text()) if soup.title else _slug_from_url(url)
    _remove_noise(soup)
    blocks = _extract_blocks(soup)
    lines = [
        f"# {title}",
        "",
        f"**Source:** {url}",
        "",
        (
            "Hannu InnoTech is the internal brand of Hanumayamma Innovations and Technologies Inc., "
            "a Delaware corporation founded in 2010. The company builds AI, IoT sensors, and analytics "
            "for agriculture, dairy, specialty crops, food security, and climate resilience."
        ),
        "",
        *blocks,
    ]
    text = "\n".join(lines)
    return re.sub(r"\n{3,}", "\n\n", text).strip() + "\n"


def _pdf_to_markdown(url: str, pdf_bytes: bytes) -> str:
    if not fitz:
        print("  PyMuPDF not available — skipping PDF extraction")
        return ""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    pages = [page.get_text().strip() for page in doc if page.get_text().strip()]
    body = "\n\n".join(pages)
    title = os.path.basename(urlparse(url).path).replace(".pdf", "").replace("_", " ")
    return (
        f"## {title}\n\n"
        f"**PDF Source:** {url}\n\n"
        f"{body}\n"
    )


def _write_raw(filename: str, content: str) -> None:
    if len(content.strip()) < 150:
        return
    os.makedirs(RAW_DIR, exist_ok=True)
    path = os.path.join(RAW_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def _strip_home_carousel(text: str) -> str:
    """Drop homepage hero-carousel blurbs; keep substantive company sections."""
    lines = text.splitlines()
    out = []
    past_carousel = False
    for line in lines:
        if line.startswith("## Our Company"):
            past_carousel = True
        if not past_carousel:
            heading = line.lstrip("#").strip().lower()
            if heading in CAROUSEL_MARKERS:
                continue
            if line.startswith("## ") and heading not in CAROUSEL_MARKERS:
                # Keep non-carousel early headings like Global Recognition on inner pages.
                if heading in {"our company", "our customers", "case studies"}:
                    past_carousel = True
                else:
                    continue
            elif not past_carousel:
                continue
        out.append(line)
    return "\n".join(out)


def _extract_sections(text: str, section_names: set[str]) -> str:
    lines = text.splitlines()
    out = []
    capture = False
    for line in lines:
        if line.startswith("## "):
            heading = line.lstrip("#").strip().lower()
            capture = any(name in heading for name in section_names)
        if capture:
            out.append(line)
    return "\n".join(out).strip()


def _dedupe_paragraphs(text: str) -> str:
    lines = text.splitlines()
    out = []
    seen = set()
    for line in lines:
        key = line.strip().lower()
        if key.startswith("#") or not key:
            out.append(line)
            continue
        if len(key) < 40:
            out.append(line)
            continue
        if key in seen:
            continue
        seen.add(key)
        out.append(line)
    return "\n".join(out)


def _consolidate(raw_files: dict[str, str], pdf_sections: list[str]) -> None:
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Remove legacy single-file website doc.
    legacy = os.path.join(OUTPUT_DIR, "hanuinnotech_website.md")
    if os.path.exists(legacy):
        os.remove(legacy)

    for out_name, sources in CONSOLIDATED_DOCS.items():
        parts = [
            f"# {out_name.replace('hanuinnotech_', '').replace('.md', '').replace('_', ' ').title()}",
            "",
            "**Official source:** https://www.hanuinnotech.com/",
            "",
            (
                "This document was compiled from Hanumayamma Innovations and Technologies Inc. "
                "(Hannu InnoTech) public website content for internal knowledge retrieval."
            ),
            "",
        ]
        for source in sources:
            if source not in raw_files:
                continue
            content = raw_files[source]
            if out_name == "hanuinnotech_company_overview.md" and source in {"home.md", "index_html.md"}:
                content = _strip_home_carousel(content)
            if out_name == "hanuinnotech_case_studies.md" and source.endswith("_html.md") and not source.startswith("download_"):
                extracted = _extract_sections(
                    content,
                    {"case studies", "global recognition", "customers"},
                )
                if extracted:
                    content = extracted
            parts.append(content)
            parts.append("")

        if out_name == "hanuinnotech_case_studies.md" and pdf_sections:
            parts.append("## Case Study PDFs and Technical Documents\n")
            parts.extend(pdf_sections)

        body = _dedupe_paragraphs("\n".join(parts))
        body = re.sub(r"\n{3,}", "\n\n", body).strip() + "\n"
        out_path = os.path.join(OUTPUT_DIR, out_name)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(body)
        print(f"  consolidated {out_name} ({len(body):,} chars)")


def scrape_website() -> None:
    client = httpx.Client(
        timeout=60.0,
        follow_redirects=True,
        headers={"User-Agent": "HanuInnoTech-RAG-Bot/1.0 (internal knowledge indexing)"},
    )

    to_visit = {_normalize_url(u) for u in SEED_URLS}
    to_visit = {u for u in to_visit if u}
    visited: set[str] = set()
    raw_files: dict[str, str] = {}
    pdf_urls: set[str] = set()

    print("Crawling HTML pages...")
    while to_visit:
        url = to_visit.pop()
        if url in visited:
            continue
        visited.add(url)

        basename = os.path.basename(urlparse(url).path)
        if basename in SKIP_HTML_SUFFIXES:
            continue

        try:
            response = client.get(url)
            response.raise_for_status()
        except Exception as exc:
            print(f"  skip {url}: {exc}")
            continue

        if "html" not in response.headers.get("content-type", "") and not url.endswith(".html"):
            continue

        pdf_urls |= _discover_pdfs(response.text, url)
        for link in _discover_links(response.text, url):
            if link not in visited:
                to_visit.add(link)

        markdown = _page_to_markdown(url, response.text)
        slug = _slug_from_url(url)
        filename = f"{slug}.md"
        _write_raw(filename, markdown)
        if filename not in raw_files or len(markdown) > len(raw_files.get(filename, "")):
            raw_files[filename] = markdown
        time.sleep(0.25)

    print(f"Fetched {len(raw_files)} unique pages. Extracting {len(pdf_urls)} PDFs...")
    pdf_sections: list[str] = []
    for url in sorted(pdf_urls):
        try:
            response = client.get(url)
            response.raise_for_status()
        except Exception as exc:
            print(f"  skip pdf {url}: {exc}")
            continue
        section = _pdf_to_markdown(url, response.content)
        if section and len(section) > 100:
            pdf_sections.append(section)
        time.sleep(0.25)

    client.close()
    print("Building consolidated documents...")
    _consolidate(raw_files, pdf_sections)
    print("Done.")


def main():
    print(f"Scraping {BASE_URL}")
    if os.path.isdir(RAW_DIR):
        for f in os.listdir(RAW_DIR):
            os.remove(os.path.join(RAW_DIR, f))
    scrape_website()


if __name__ == "__main__":
    main()

"""Clean crawled website markdown into a RAG-friendly document."""

import os
import re

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_PATH = os.path.join(_BASE_DIR, "sample_docs", "_hanuinnotech_raw.md")
OUTPUT_PATH = os.path.join(_BASE_DIR, "sample_docs", "hanuinnotech_website.md")


def clean_website_markdown(raw: str) -> str:
    lines = []
    for line in raw.splitlines():
        stripped = line.strip()
        if not stripped:
            lines.append("")
            continue
        if stripped.startswith("Source URL:"):
            continue
        if stripped.startswith("Toggle navigation"):
            continue
        if stripped in {"* Home", "* Contact Us"}:
            continue
        if stripped.startswith("* ") and "**" in stripped and stripped.endswith("**"):
            continue
        if re.match(r"^[*]?\s*(png|img)\s*$", stripped, re.I):
            continue
        if stripped in {"**Prev**", "**Next**", "---"}:
            continue
        if stripped.startswith("Know More") or stripped.startswith("Order Now"):
            continue
        lines.append(line.rstrip())

    text = "\n".join(lines)
    text = re.sub(r"\n{3,}", "\n\n", text)

    header = (
        "# Hanumayamma Innovations and Technologies Inc (Hannu InnoTech)\n\n"
        "Source: https://www.hanuinnotech.com/\n\n"
        "Hannu InnoTech is the internal brand name used alongside Hanumayamma "
        "Innovations and Technologies Inc., a Delaware corporation founded in 2010.\n\n"
    )
    return header + text.strip() + "\n"


def main():
    if not os.path.exists(RAW_PATH):
        print(f"No raw file at {RAW_PATH}; skipping website doc preparation.")
        return

    with open(RAW_PATH, "r", encoding="utf-8") as f:
        raw = f.read()

    cleaned = clean_website_markdown(raw)
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write(cleaned)
    print(f"Wrote {OUTPUT_PATH} ({len(cleaned)} chars)")


if __name__ == "__main__":
    main()

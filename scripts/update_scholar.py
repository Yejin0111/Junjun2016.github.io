#!/usr/bin/env python3
"""
Fetch Google Scholar citation stats and update publications.html.
Extracts data from the HTML meta tag and the gsc_rsb_st table.
"""

import re
import subprocess
import sys


SCHOLAR_URL = "https://scholar.google.com/citations?hl=en&user=Z4LgebkAAAAJ"
PUB_FILE = "publications.html"


def fetch_scholar_page():
    """Fetch Google Scholar profile page using curl."""
    result = subprocess.run(
        [
            "curl", "-s", "-L",
            "-H", "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            SCHOLAR_URL,
        ],
        capture_output=True, text=True, timeout=30,
    )
    if result.returncode != 0:
        print(f"curl failed: {result.stderr}", file=sys.stderr)
        sys.exit(1)
    return result.stdout


def extract_stats(html):
    """Extract citations, h-index, i10-index from Scholar HTML."""

    # Method 1: meta tag — "Cited by 9,875"
    meta_match = re.search(r'Cited by ([\d,]+)', html)
    citations = meta_match.group(1) if meta_match else None

    # Method 2: gsc_rsb_std table cells
    # The table has 3 rows (Citations, h-index, i10-index) x 2 cols (All, Since ...)
    # Each value is in <td class="gsc_rsb_std">VALUE</td>
    std_values = re.findall(r'gsc_rsb_std[^>]*>(\d+)', html)
    # Expected: [citations_all, citations_recent, h_all, h_recent, i10_all, i10_recent]

    if len(std_values) >= 6:
        citations = std_values[0]
        h_index = std_values[2]
        i10_index = std_values[4]
    elif len(std_values) >= 4:
        citations = citations or std_values[0]
        h_index = std_values[2]
        i10_index = None
    else:
        h_index = None
        i10_index = None

    if not citations:
        print("Could not extract citation count from Scholar page.", file=sys.stderr)
        sys.exit(1)

    return {
        "citations": citations,
        "h_index": h_index,
        "i10_index": i10_index,
    }


def format_citations(raw):
    """Format citation count: 9875 -> '9,875'."""
    num = int(raw.replace(",", ""))
    return f"{num:,}"


def update_pub_file(stats):
    """Update the pub-stats div in publications.html."""
    with open(PUB_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    citations_display = format_citations(stats["citations"])
    h_display = stats["h_index"] or "N/A"
    i10_display = stats["i10_index"] or "N/A"

    # Build new stats line
    new_stats_inner = (
        f"\n        {citations_display} citations &nbsp;|&nbsp;\n"
        f"        h-index: {h_display} &nbsp;|&nbsp;\n"
        f"        i10-index: {i10_display}\n"
        f"        &nbsp;|&nbsp; "
        f'<a href="https://scholar.google.com/citations?user=Z4LgebkAAAAJ&hl=zh-CN">Google Scholar</a>\n      '
    )

    # Replace the content of <div class="pub-stats">...</div>
    new_content = re.sub(
        r'(<div class="pub-stats">)(.*?)(</div>)',
        rf'\1{new_stats_inner}\3',
        content,
        count=1,
        flags=re.DOTALL,
    )

    if new_content == content:
        print("No changes needed or pattern not found.")
        return False

    with open(PUB_FILE, "w", encoding="utf-8") as f:
        f.write(new_content)

    print(f"Updated: citations={citations_display}, h-index={h_display}, i10-index={i10_display}")
    return True


def main():
    print("Fetching Google Scholar page...")
    html = fetch_scholar_page()
    print(f"Page length: {len(html)} chars")

    stats = extract_stats(html)
    print(f"Extracted: citations={stats['citations']}, h={stats['h_index']}, i10={stats['i10_index']}")

    changed = update_pub_file(stats)
    if changed:
        print("publications.html updated successfully.")
    else:
        print("No update needed.")


if __name__ == "__main__":
    main()

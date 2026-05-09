#!/usr/bin/env python3
"""Parse a screener.in company page into structured JSON.

Generic across all tickers — no per-company assumptions. Gracefully degrades
when sections are missing (premium-gated insights, no concalls listed, no
credit ratings, etc.).

Usage:
    python scripts/parse_screener.py <TICKER>                         # fetch consolidated
    python scripts/parse_screener.py <TICKER> --standalone            # use standalone URL
    python scripts/parse_screener.py <TICKER> --save                  # write to ~/Documents/equity-research/<TICKER>/screener-data.json
    python scripts/parse_screener.py <TICKER> --out path.json
    python scripts/parse_screener.py --html path/to/local.html        # parse a local file (testing)

Requires: beautifulsoup4. Install in a venv:
    python3 -m venv .venv && .venv/bin/pip install beautifulsoup4
Then run with: .venv/bin/python scripts/parse_screener.py ...
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.error
import urllib.request
from copy import copy
from pathlib import Path
from typing import Any

try:
    from bs4 import BeautifulSoup, Tag
except ImportError:
    sys.exit(
        "beautifulsoup4 is required. Set up a venv and install:\n"
        "    python3 -m venv .venv && .venv/bin/pip install beautifulsoup4\n"
        "Then run: .venv/bin/python scripts/parse_screener.py ..."
    )

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Safari/605.1.15"
)


# ---------- helpers ----------

def fetch(url: str, timeout: int = 30) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", errors="replace")


def text(elem: Tag | None) -> str | None:
    return elem.get_text(" ", strip=True) if elem else None


def parse_number(s: str | None) -> float | int | None:
    """Parse '1,486' -> 1486, '4.48' -> 4.48, '12.93%' -> 12.93, blank/'-' -> None."""
    if s is None:
        return None
    cleaned = s.strip().replace(",", "").replace("%", "").replace("₹", "").strip()
    if not cleaned or cleaned in {"-", "—"}:
        return None
    try:
        if "." in cleaned:
            return float(cleaned)
        return int(cleaned)
    except ValueError:
        return None


def normalize_key(label: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", label.lower()).strip("_")


def text_without_children(a: Tag, drop_selectors: tuple[str, ...] = (".smaller", "div")) -> str | None:
    """Get text of a tag, excluding child elements matching given selectors."""
    if a is None:
        return None
    a2 = copy(a)
    for sel in drop_selectors:
        for c in a2.select(sel):
            c.extract()
    return text(a2)


# ---------- section parsers ----------

def parse_top_ratios(soup: BeautifulSoup) -> dict[str, dict]:
    ul = soup.select_one("#top-ratios")
    if not ul:
        return {}
    out: dict[str, dict] = {}
    for li in ul.select("li"):
        name_elem = li.select_one(".name")
        value_elem = li.select_one(".value")
        if not name_elem:
            continue
        name = text(name_elem)
        if not name:
            continue
        num_elem = li.select_one(".number")
        raw_num = text(num_elem) if num_elem else None
        value = parse_number(raw_num)
        full_value_text = text(value_elem) or ""
        unit = None
        if "%" in full_value_text:
            unit = "pct"
        elif "Cr" in full_value_text:
            unit = "inr_cr"
        elif "₹" in full_value_text:
            unit = "inr"
        # high/low rendered as two numbers — capture both
        numbers = [parse_number(n.string) for n in li.select(".number") if n.string]
        out[normalize_key(name)] = {
            "label": name,
            "value": value,
            "value_2": numbers[1] if len(numbers) > 1 else None,
            "unit": unit,
            "raw": full_value_text or None,
        }
    return out


def parse_company_meta(soup: BeautifulSoup) -> dict[str, Any]:
    name_elem = soup.select_one("#top h1") or soup.select_one(".company-nav h1")
    name = text(name_elem)

    # Sector taxonomy: the breadcrumb in #peers .sub uses anchors with 'title' attrs
    sector: dict[str, str] = {}
    sector_p = soup.select_one("#peers .sub")
    if sector_p:
        for a in sector_p.select("a[title]"):
            tkey = normalize_key(a.get("title", ""))
            if tkey:
                sector[tkey] = text(a)

    # Benchmarks
    benchmarks: list[str] = []
    bench_p = soup.select_one("#benchmarks")
    if bench_p:
        for a in bench_p.select("a.tag"):
            label = text(a)
            if label:
                benchmarks.append(label)

    # Exchange codes — look anywhere on the page
    exchanges: dict[str, str] = {}
    for a in soup.select("a[href*='bseindia.com/stock-share-price']"):
        m = re.search(r"BSE[:\s]+(\d+)", text(a) or "")
        if m:
            exchanges["bse"] = m.group(1)
            break
    for a in soup.select("a[href*='nseindia.com/get-quotes']"):
        m = re.search(r"NSE[:\s]+([A-Z0-9]+)", text(a) or "")
        if m:
            exchanges["nse"] = m.group(1)
            break

    # Company website (first external link that's not an exchange / screener)
    website = None
    for a in soup.select(".company-info a[href^='http'], .company-links a[href^='http']"):
        href = a.get("href", "")
        if not any(d in href for d in ("bseindia", "nseindia", "screener.in")):
            website = href
            break

    about = text(soup.select_one(".company-profile .about p"))
    key_points = text(soup.select_one(".company-profile .commentary"))

    return {
        "name": name,
        "sector_taxonomy": sector,
        "benchmarks": benchmarks,
        "exchange_codes": exchanges,
        "website": website,
        "about": about,
        "key_points": key_points,
    }


def parse_pros_cons(soup: BeautifulSoup) -> dict[str, list[str]] | None:
    section = soup.select_one("#analysis")
    if not section:
        return None
    pros = [text(li) for li in section.select(".pros ul li") if text(li)]
    cons = [text(li) for li in section.select(".cons ul li") if text(li)]
    if not pros and not cons:
        return None
    return {"pros": pros, "cons": cons}


def parse_data_table(section: Tag | None) -> dict | None:
    """Generic parser for #profit-loss / #balance-sheet / #cash-flow / #ratios / #quarters tables."""
    if not section:
        return None
    table = section.select_one("table.data-table")
    if not table:
        return None

    # Column headers — prefer data-date-key, fallback to text
    dates: list[str] = []
    for th in table.select("thead th"):
        date_key = th.get("data-date-key")
        if date_key:
            dates.append(date_key)
        else:
            txt = text(th)
            if txt:
                dates.append(txt)
    # Drop the first empty header (the row-label column)
    if dates and not dates[0]:
        dates = dates[1:]

    rows: dict[str, list] = {}
    for tr in table.select("tbody tr"):
        first_td = tr.select_one("td.text")
        if not first_td:
            continue
        label = text(first_td)
        if not label:
            continue
        # Strip trailing "+" from button-with-schedule rows ("Sales+" -> "Sales")
        label = re.sub(r"\s*\+\s*$", "", label).strip()
        cells = tr.select("td:not(.text)")
        if len(cells) != len(dates):
            # Skip mismatched rows (Raw PDF row, segment headers, etc.)
            continue
        rows[label] = [parse_number(text(c)) for c in cells]

    return {"dates": dates, "rows": rows}


def parse_compounded_growth(soup: BeautifulSoup) -> dict[str, dict]:
    """The four ranges-table blocks under #profit-loss (Sales / Profit / Stock CAGR / ROE)."""
    out: dict[str, dict] = {}
    for table in soup.select("table.ranges-table"):
        header = text(table.select_one("th"))
        if not header:
            continue
        key = normalize_key(header)
        entries: dict[str, float | int | None] = {}
        for tr in table.select("tr"):
            tds = tr.select("td")
            if len(tds) == 2:
                period_raw = text(tds[0]) or ""
                period = period_raw.rstrip(":").strip()
                if period:
                    entries[normalize_key(period)] = parse_number(text(tds[1]))
        if entries:
            out[key] = entries
    return out


def parse_shareholding(section: Tag | None) -> dict | None:
    if not section:
        return None
    table = section.select_one("table.data-table")
    if not table:
        return None
    headers = [text(th) for th in table.select("thead th")]
    if headers and not headers[0]:
        headers = headers[1:]
    rows: dict[str, list] = {}
    for tr in table.select("tbody tr"):
        first_td = tr.select_one("td.text")
        if not first_td:
            continue
        label = text(first_td)
        if not label:
            continue
        label = re.sub(r"\s*\+\s*$", "", label).strip()
        cells = tr.select("td")[1:]
        if len(cells) != len(headers):
            continue
        rows[label] = [parse_number(text(c)) for c in cells]
    return {"dates": headers, "rows": rows}


def parse_annual_reports(soup: BeautifulSoup) -> list[dict]:
    section = soup.select_one(".annual-reports")
    if not section:
        return []
    out: list[dict] = []
    for li in section.select("ul.list-links li"):
        a = li.select_one("a")
        if not a:
            continue
        full = text(a) or ""
        m_year = re.search(r"Financial Year (\d{4})", full)
        fy = int(m_year.group(1)) if m_year else None
        m_src = re.search(r"from\s+(\w+)", full, re.IGNORECASE)
        source = m_src.group(1).upper() if m_src else None
        out.append({"fy": fy, "url": a.get("href"), "source": source})
    return out


def parse_concalls(soup: BeautifulSoup) -> list[dict]:
    section = soup.select_one(".concalls")
    if not section:
        return []
    out: list[dict] = []
    for li in section.select("ul.list-links li"):
        date_div = li.select_one("div.ink-600.font-size-15") or li.select_one("div.ink-600")
        date = text(date_div)
        entry: dict[str, Any] = {"date": date}
        for a in li.select("a.concall-link"):
            label = (text(a) or "").lower()
            if "transcript" in label:
                entry["transcript_url"] = a.get("href")
            elif "ppt" in label:
                entry["ppt_url"] = a.get("href")
            elif label in ("rec", "recording"):
                entry["recording_url"] = a.get("href")
        for btn in li.select("button.concall-link"):
            label = (text(btn) or "").lower()
            if "summary" in label:
                summary_path = btn.get("data-url")
                if summary_path:
                    entry["ai_summary_url"] = (
                        f"https://www.screener.in{summary_path}"
                        if summary_path.startswith("/")
                        else summary_path
                    )
        if any(k.endswith("_url") for k in entry):
            out.append(entry)
    return out


def parse_credit_ratings(soup: BeautifulSoup) -> list[dict]:
    section = soup.select_one(".credit-ratings")
    if not section:
        return []
    out: list[dict] = []
    for li in section.select("ul.list-links li"):
        a = li.select_one("a")
        if not a:
            continue
        url = a.get("href", "")
        sub = text(li.select_one(".smaller"))
        agency = None
        for k, v in (
            ("careratings", "CARE"),
            ("crisil", "CRISIL"),
            ("icra", "ICRA"),
            ("indiaratings", "India Ratings"),
            ("brickworkratings", "Brickwork"),
        ):
            if k in url.lower():
                agency = v
                break
        out.append({"agency": agency, "date_text": sub, "url": url})
    return out


def parse_announcements(soup: BeautifulSoup) -> list[dict]:
    section = soup.select_one("#company-announcements-tab")
    if not section:
        return []
    out: list[dict] = []
    for li in section.select("ul.list-links li"):
        a = li.select_one("a")
        if not a:
            continue
        smaller = a.select_one(".smaller")
        summary = text(smaller) if smaller else None
        title = text_without_children(a)
        days_ago = None
        if summary:
            m = re.match(r"(\d+)d\s*-\s*", summary)
            if m:
                days_ago = int(m.group(1))
                summary = summary[m.end():].strip()
        out.append({
            "title": title,
            "summary": summary,
            "url": a.get("href"),
            "days_ago": days_ago,
        })
    return out


# ---------- top-level ----------

def parse(html: str) -> dict[str, Any]:
    soup = BeautifulSoup(html, "html.parser")

    info_div = soup.select_one("#company-info")
    company_id = info_div.get("data-company-id") if info_div else None
    is_consolidated = (info_div.get("data-consolidated") == "true") if info_div else None

    return {
        "company_id": company_id,
        "is_consolidated": is_consolidated,
        "meta": parse_company_meta(soup),
        "key_ratios": parse_top_ratios(soup),
        "pros_cons": parse_pros_cons(soup),
        "compounded_growth": parse_compounded_growth(soup),
        "quarterly": parse_data_table(soup.select_one("#quarters")),
        "pl_yearly": parse_data_table(soup.select_one("#profit-loss")),
        "balance_sheet_yearly": parse_data_table(soup.select_one("#balance-sheet")),
        "cash_flow_yearly": parse_data_table(soup.select_one("#cash-flow")),
        "ratios_yearly": parse_data_table(soup.select_one("#ratios")),
        "shareholding_quarterly": parse_shareholding(soup.select_one("#quarterly-shp")),
        "shareholding_yearly": parse_shareholding(soup.select_one("#yearly-shp")),
        "annual_reports": parse_annual_reports(soup),
        "concalls": parse_concalls(soup),
        "credit_ratings": parse_credit_ratings(soup),
        "announcements": parse_announcements(soup),
    }


def main() -> int:
    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("ticker", nargs="?", help="BSE/NSE symbol (e.g., ABREL, TCS)")
    p.add_argument("--standalone", action="store_true",
                   help="Use standalone URL instead of consolidated")
    p.add_argument("--html", type=Path, help="Parse a local HTML file instead of fetching")
    p.add_argument("--out", type=Path, help="Write JSON to file (default: stdout)")
    p.add_argument("--save", action="store_true",
                   help="Write to ~/Documents/equity-research/<TICKER>/screener-data.json")
    args = p.parse_args()

    if args.html:
        html = args.html.read_text()
        ticker = args.ticker or args.html.stem.upper()
    elif args.ticker:
        ticker = args.ticker.upper()
        path_segment = "" if args.standalone else "consolidated/"
        url = f"https://www.screener.in/company/{ticker}/{path_segment}"
        try:
            html = fetch(url)
        except urllib.error.HTTPError as e:
            if not args.standalone and e.code in (404, 410):
                # Fall back to standalone — common for companies without consolidated financials
                fallback = f"https://www.screener.in/company/{ticker}/"
                print(f"[warn] consolidated returned {e.code}; falling back to {fallback}",
                      file=sys.stderr)
                try:
                    html = fetch(fallback)
                except Exception as e2:
                    sys.exit(f"Both consolidated and standalone fetches failed: {e}; {e2}")
            else:
                sys.exit(f"Failed to fetch {url}: {e}")
        except Exception as e:
            sys.exit(f"Failed to fetch {url}: {e}")
    else:
        sys.exit("Provide either a ticker or --html FILE")

    data = parse(html)
    data["ticker"] = ticker
    out_json = json.dumps(data, indent=2, default=str, ensure_ascii=False)

    if args.save:
        out_dir = Path.home() / "Documents" / "equity-research" / ticker
        out_dir.mkdir(parents=True, exist_ok=True)
        target = out_dir / "screener-data.json"
        target.write_text(out_json)
        print(f"Wrote {target} ({len(out_json):,} bytes)", file=sys.stderr)
    elif args.out:
        args.out.write_text(out_json)
        print(f"Wrote {args.out} ({len(out_json):,} bytes)", file=sys.stderr)
    else:
        print(out_json)
    return 0


if __name__ == "__main__":
    sys.exit(main())

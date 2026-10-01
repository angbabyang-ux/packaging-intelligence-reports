# -*- coding: utf-8 -*-
"""Runs in GitHub Actions (open internet). Validates the routine's draft issue JSON,
fills real photos, drops stale/photo-less items, renders with the fixed template,
and writes _automation/status/issue-N.json for the routine to read.

Usage: python _automation/pipeline.py _automation/issues/issue-N.json
"""
import datetime as dt
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_issue import build  # noqa: E402
from fill_photos import fetch, find_photo, valid_image  # noqa: E402

MIN_ITEMS = 12
MAX_ITEMS = 20
STALE_GRACE_DAYS = 2

DATE_PATTERNS = [
    r'property=["\']article:published_time["\'][^>]*content=["\'](\d{4}-\d{2}-\d{2})',
    r'content=["\'](\d{4}-\d{2}-\d{2})[^"\']*["\'][^>]*property=["\']article:published_time',
    r'"datePublished"\s*:\s*"(\d{4}-\d{2}-\d{2})',
    r'name=["\'](?:pubdate|publishdate|date|DC\.date\.issued)["\'][^>]*content=["\'](\d{4}-\d{2}-\d{2})',
    r'<time[^>]*datetime=["\'](\d{4}-\d{2}-\d{2})',
]


def published_date(page):
    for p in DATE_PATTERNS:
        m = re.search(p, page, re.I)
        if m:
            try:
                return dt.date.fromisoformat(m.group(1))
            except ValueError:
                pass
    return None


MONTHS = {m: i + 1 for i, m in enumerate(["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"])}


def all_dates(page):
    """Every explicit date in the page, used only when no publish-date metadata exists."""
    out = set()
    for y, m, d in re.findall(r"(20\d\d)-(\d\d)-(\d\d)", page):
        out.add((int(y), int(m), int(d)))
    for d, mon, y in re.findall(r"\b(\d{1,2}) (Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* (20\d\d)", page):
        out.add((int(y), MONTHS[mon.lower()], int(d)))
    for mon, d, y in re.findall(r"\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.? (\d{1,2}), (20\d\d)", page):
        out.add((int(y), MONTHS[mon.lower()], int(d)))
    for y, m, d in re.findall(r"(20\d\d)[./년]\s?(\d{1,2})[./월]\s?(\d{1,2})", page):
        out.add((int(y), int(m), int(d)))
    res = []
    for y, m, d in out:
        try:
            res.append(dt.date(y, m, d))
        except ValueError:
            pass
    return res


def parse_range(r):
    start, end = r.split("~")
    s = dt.date(*map(int, start.split(".")))
    parts = end.split(".")
    e = dt.date(int(parts[0]), int(parts[1]), int(parts[2])) if len(parts) == 3 else dt.date(s.year, int(parts[0]), int(parts[1]))
    return s, e


def main(issue_path):
    repo = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(issue_path))))
    d = json.load(open(issue_path, encoding="utf-8"))
    n = d["number"]
    start, end = parse_range(d["date_range"])
    kept, dropped = [], []
    for it in d["newsletter_items"]:
        final, page = fetch(it["url"])
        pub = published_date(page) if page else None
        event = it.get("event_date")
        in_event = False
        if event:
            try:
                in_event = start <= dt.date.fromisoformat(event) <= end + dt.timedelta(days=7)
            except ValueError:
                pass
        if page and not pub and not in_event:
            dates = all_dates(page)
            lo, hi = start - dt.timedelta(days=STALE_GRACE_DAYS), end + dt.timedelta(days=1)
            if dates and not any(lo <= x <= hi for x in dates) and max(dates) < lo:
                dropped.append({"headline": it["headline"], "reason": f"stale: newest date on page is {max(dates)}"})
                continue
        if pub and pub < start - dt.timedelta(days=STALE_GRACE_DAYS) and not in_event:
            dropped.append({"headline": it["headline"], "reason": f"stale: source published {pub}"})
            continue
        if pub and pub > end + dt.timedelta(days=1):
            dropped.append({"headline": it["headline"], "reason": f"future-dated source {pub}"})
            continue
        if it.get("img") and not valid_image(it["img"], it["url"]):
            it["img"] = ""
        if not it.get("img"):
            _, img = find_photo(it["url"])
            it["img"] = img or ""
        if not it["img"]:
            dropped.append({"headline": it["headline"], "reason": "no verifiable photo"})
            continue
        it["source_published"] = pub.isoformat() if pub else None
        kept.append(it)

    reg = [x for x in kept if x["is_reg"]]
    sig = [x for x in kept if not x["is_reg"]]
    kept = (reg + sig)[:MAX_ITEMS] if len(reg + sig) > MAX_ITEMS else reg + sig
    d["newsletter_items"] = kept

    problems = []
    if len(kept) < MIN_ITEMS:
        problems.append(f"only {len(kept)} newsletter items survived verification (minimum {MIN_ITEMS})")
    if not reg:
        problems.append("no regulation-radar item survived verification")
    if len(d["regulation_current"]) != 5 or len(d["regulation_future"]) != 5:
        problems.append("regulation report must have exactly 5 current + 5 future items")

    # "final" stays False on success until the workflow confirms the page is live on GitHub Pages.
    status = {"number": n, "ok": not problems, "final": bool(problems), "live": None,
              "problems": problems, "dropped": dropped,
              "items": len(kept), "photos": sum(1 for x in kept if x["img"]),
              "checked_at": dt.datetime.now(dt.timezone.utc).isoformat()}
    if not problems:
        json.dump(d, open(issue_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        status["entry"] = build(repo, issue_path)
    os.makedirs(os.path.join(repo, "_automation", "status"), exist_ok=True)
    json.dump(status, open(os.path.join(repo, "_automation", "status", f"issue-{n}.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(json.dumps(status, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main(sys.argv[1])

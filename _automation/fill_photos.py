# -*- coding: utf-8 -*-
"""Insert a real source photo into every newsletter item that lacks one.

Usage: python fill_photos.py newsletter-4.html [more.html ...]
Prints a JSON summary; exit code 0 always (the caller decides on missing count).
"""
import html as htmlmod
import json
import re
import sys
from urllib.parse import urljoin, urlparse

import requests

UAS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36",
    # Many publishers whitelist social crawlers so link previews work.
    "facebookexternalhit/1.1 (+http://www.facebook.com/externalhit_uatext.php)",
    "Twitterbot/1.0",
]
META_KEYS = ["og:image:secure_url", "og:image", "twitter:image", "twitter:image:src"]
BAD_IMG = re.compile(r"(logo|icon|sprite|avatar|favicon|placeholder|blank|pixel|/themes/|default-|\.svg|\.gif|data:)", re.I)


def fetch(url):
    for ua in UAS:
        try:
            r = requests.get(url, headers={"User-Agent": ua, "Accept": "text/html,*/*",
                                           "Accept-Language": "en-US,en;q=0.9,ko;q=0.8"},
                             timeout=20, allow_redirects=True)
            if r.status_code == 200 and "<" in r.text[:2000]:
                return r.url, r.text
        except requests.RequestException:
            pass
    return None, None


def meta_images(page):
    found = []
    for tag in re.findall(r"<meta\b[^>]*>", page, re.I):
        key = re.search(r'(?:property|name|itemprop)\s*=\s*["\']([^"\']+)["\']', tag, re.I)
        val = re.search(r'content\s*=\s*["\']([^"\']+)["\']', tag, re.I)
        if key and val and key.group(1).lower() in META_KEYS + ["image"]:
            found.append((META_KEYS.index(key.group(1).lower()) if key.group(1).lower() in META_KEYS else 9, val.group(1)))
    link = re.search(r'<link\b[^>]*rel=["\']image_src["\'][^>]*href=["\']([^"\']+)', page, re.I)
    if link:
        found.append((10, link.group(1)))
    return [u for _, u in sorted(found)]


def body_images(page):
    out = []
    for m in re.finditer(r"<img\b[^>]*>", page, re.I):
        tag = m.group(0)
        src = re.search(r'(?:data-src|data-lazy-src|src)\s*=\s*["\']([^"\']+)', tag, re.I)
        if src and not BAD_IMG.search(src.group(1)) and re.search(r"\.(jpe?g|png|webp)", src.group(1), re.I):
            out.append(src.group(1))
    return out[:6]


def valid_image(url, referer):
    for ua in UAS:
        try:
            r = requests.get(url, headers={"User-Agent": ua, "Referer": referer}, timeout=20, stream=True)
            ok = r.status_code == 200 and r.headers.get("Content-Type", "").startswith("image/")
            size = int(r.headers.get("Content-Length") or 0)
            if ok and size == 0:
                size = len(r.raw.read(20000, decode_content=True))
            r.close()
            if ok and size > 4000:
                return True
        except requests.RequestException:
            pass
    return False


def find_photo(article_url):
    final, page = fetch(article_url)
    candidates = []
    if page:
        candidates += [("article", u) for u in meta_images(page) + body_images(page)]
    # Last resort: the publisher's own share image, still a genuine source image.
    home = "{0.scheme}://{0.netloc}/".format(urlparse(final or article_url))
    _, hp = fetch(home)
    if hp:
        candidates += [("publisher", u) for u in meta_images(hp)]
    seen = set()
    for kind, u in candidates:
        u = urljoin(final or article_url, htmlmod.unescape(u.strip()))
        if u in seen or BAD_IMG.search(u.split("?")[0]) and kind == "article":
            continue
        seen.add(u)
        if valid_image(u, final or article_url):
            return kind, u
    return None, None


def fill(path):
    s = open(path, encoding="utf-8").read()
    report = []

    def repl(m):
        block = m.group(0)
        if "item-media" in block:
            return block
        url = htmlmod.unescape(re.search(r'item-headline-link" href="([^"]+)"', block).group(1))
        kind, img = find_photo(url)
        report.append({"url": url, "kind": kind, "img": img})
        if not img:
            return block
        media = f'<div class="item-media"><img src="{htmlmod.escape(img, quote=True)}" alt="" loading="lazy"></div>\n'
        return block.replace('<article class="item">\n', '<article class="item">\n' + media, 1) \
            if '<article class="item">\n' in block else block.replace('<article class="item">', '<article class="item">' + media, 1)

    s = re.sub(r'<article class="item">.*?</article>', repl, s, flags=re.S)
    n_media = s.count('class="item-media"')
    s = re.sub(r"사진 \d+", "사진 %d" % n_media, s, count=1)
    open(path, "w", encoding="utf-8").write(s)
    total = s.count('<article class="item">')
    photos = s.count('class="item-media"')
    return {"file": path, "items": total, "photos": photos, "missing": total - photos, "details": report}


if __name__ == "__main__":
    print(json.dumps([fill(p) for p in sys.argv[1:]], ensure_ascii=False, indent=1))

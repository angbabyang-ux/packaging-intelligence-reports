# -*- coding: utf-8 -*-
"""Canonical renderer: _automation/issues/issue-N.json -> newsletter-N.html, regulation-N.html,
issues.json entry, index.html. The visual template is fixed here so every issue looks identical.

Usage: python build_issue.py <repo_root> <issue_json_path>
"""
import html as htmlmod
import json
import os
import sys

BLUE_TAGS = {"글로벌", "인도", "중국", "유럽", "아세안", "미국", "한국", "영국", "일본", "지속가능", "발상혁신"}
BASE_URL = "https://angbabyang-ux.github.io/packaging-intelligence-reports/"
esc = htmlmod.escape


def tag_pill(t):
    cls = "tag tag-blue" if t in BLUE_TAGS else "tag tag-neutral"
    return f'<span class="{cls}">{esc(t)}</span>'


def render_item(it):
    img_html = (f'<div class="item-media"><img src="{esc(it["img"], quote=True)}" alt="" loading="lazy"></div>'
                if it.get("img") else "")
    tags_html = "".join(tag_pill(t) for t in it["tags"])
    headline = f'{it["flag"]} {esc(it["region"])} — {esc(it["headline"])}'
    url = esc(it["url"], quote=True)
    return f'''<article class="item">
{img_html}
<div class="item-body">
<div class="item-tags">{tags_html}</div>
<a class="item-headline-link" href="{url}" target="_blank" rel="noopener"><h3 class="item-headline">{headline}</h3></a>
<div class="item-meta"><span class="meta-date">{esc(it['date'])}</span><span class="meta-sep"> · </span>{esc(it['source'])}</div>
<a class="item-desc-link" href="{url}" target="_blank" rel="noopener"><p class="item-desc">{esc(it['body'])}</p></a>
<div class="item-insight">{esc(it['insight'])}</div>
</div>
</article>'''


NEWSLETTER_CSS = """
:root {
  --paper: #FAF8F4; --ink: #17191D; --ink-soft: #4A4D55; --slate: #6B6F7B;
  --accent: #1B4FE0; --accent-soft: #EEF2FF; --accent-line: #C9D6FB;
  --line: #E6E4DC; --card: #FFFFFF;
  --tag-neutral: #5B5F69; --tag-neutral-line: #DEDCD3;
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    --paper: #14151A; --ink: #F2F1ED; --ink-soft: #C7C6C2; --slate: #93949E;
    --accent: #6E93FF; --accent-soft: #1B2340; --accent-line: #33417A;
    --line: #2A2B30; --card: #1B1C22;
  }
}
:root[data-theme="dark"] {
  --paper: #14151A; --ink: #F2F1ED; --ink-soft: #C7C6C2; --slate: #93949E;
  --accent: #6E93FF; --accent-soft: #1B2340; --accent-line: #33417A;
  --line: #2A2B30; --card: #1B1C22;
}
* { box-sizing: border-box; }
body { margin: 0; background: var(--paper); color: var(--ink);
  font-family: 'IBM Plex Sans KR', 'Apple SD Gothic Neo', 'Malgun Gothic', sans-serif; padding: 0 16px; }
.wrap { max-width: 720px; margin: 0 auto; padding-block: 48px 80px; }
.masthead { padding-bottom: 28px; border-bottom: 2px solid var(--ink); margin-bottom: 32px; }
.kicker { font-size: 12px; letter-spacing: 0.22em; font-weight: 700; color: var(--accent);
  text-transform: uppercase; margin: 0 0 14px; }
.masthead-title { font-family: 'Noto Serif KR', serif; font-weight: 900;
  font-size: clamp(32px, 6vw, 46px); line-height: 1.18; letter-spacing: -0.01em;
  margin: 0 0 18px; text-wrap: balance; }
.meta-bar { display: flex; flex-wrap: wrap; gap: 6px 0; font-size: 13px; color: var(--slate);
  font-variant-numeric: tabular-nums; }
.meta-bar b { color: var(--ink); font-weight: 700; }
.meta-bar .accent { color: var(--accent); font-weight: 700; }
.meta-sep { margin: 0 10px; color: var(--line); }
.summary { border: 1px solid var(--accent-line); background: var(--accent-soft);
  border-radius: 4px; padding: 22px 24px; margin-bottom: 40px; }
.summary-label { font-size: 13px; letter-spacing: 0.1em; font-weight: 700; color: var(--accent);
  margin: 0 0 10px; text-transform: uppercase; }
.summary p { margin: 0; font-size: 15.5px; line-height: 1.75; color: var(--ink); }
.section { margin-bottom: 44px; }
.section-head { display: flex; align-items: baseline; gap: 14px; margin-bottom: 4px;
  border-bottom: 1px solid var(--ink); padding-bottom: 10px; }
.section-kicker { font-size: 12px; letter-spacing: 0.16em; font-weight: 700; color: var(--accent);
  text-transform: uppercase; white-space: nowrap; }
.section-title { font-family: 'Noto Serif KR', serif; font-weight: 700; font-size: 20px;
  margin: 0; color: var(--ink-soft); }
.item-grid { display: flex; flex-direction: column; }
.item { display: grid; grid-template-columns: 168px 1fr; gap: 20px;
  padding: 26px 0; border-bottom: 1px solid var(--line); }
.item:last-child { border-bottom: none; }
.item-media { width: 168px; aspect-ratio: 4 / 3; border-radius: 6px; overflow: hidden;
  background: var(--line); border: 1px solid var(--line); }
.item-media img { width: 100%; height: 100%; object-fit: cover; display: block; }
.item:not(:has(.item-media)) { grid-template-columns: 1fr; }
.item-tags { display: flex; flex-wrap: wrap; gap: 5px; margin-bottom: 9px; }
.tag { font-size: 10.5px; font-weight: 700; padding: 3px 9px; border-radius: 20px;
  white-space: nowrap; line-height: 1.5; }
.tag-blue { border: 1px solid var(--accent-line); color: var(--accent); }
.tag-neutral { border: 1px solid var(--tag-neutral-line); color: var(--tag-neutral); }
a.item-headline-link, a.item-desc-link { text-decoration: none; color: inherit; }
.item-headline { font-family: 'Noto Serif KR', serif; font-weight: 700; font-size: 17.5px;
  line-height: 1.34; letter-spacing: -0.005em; margin: 0 0 6px; color: var(--ink); }
a.item-headline-link:hover .item-headline { color: var(--accent); }
.item-meta { font-size: 12px; color: var(--slate); margin-bottom: 8px; }
.item-desc { font-size: 14px; line-height: 1.64; color: var(--ink-soft); margin: 0 0 10px; max-width: 65ch; }
.item-insight { border-left: 3px solid var(--accent); border-radius: 0 4px 4px 0;
  padding: 8px 14px; font-size: 13px; line-height: 1.6; color: var(--accent); background: var(--accent-soft); }
.footer { margin-top: 56px; padding-top: 20px; border-top: 1px solid var(--line);
  font-size: 11.5px; line-height: 1.8; color: var(--slate); }
@media (max-width: 560px) {
  .item { grid-template-columns: 96px 1fr; gap: 14px; }
  .item-media { width: 96px; }
  .item-headline { font-size: 16px; }
}
"""

FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com">\n'
         '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
         '<link href="https://fonts.googleapis.com/css2?family=Noto+Serif+KR:wght@500;700;900&family=IBM+Plex+Sans+KR:wght@400;500;600;700&display=swap" rel="stylesheet">')


def build_newsletter(d):
    items = d["newsletter_items"]
    reg = [it for it in items if it["is_reg"]]
    sig = [it for it in items if not it["is_reg"]]
    n_photos = sum(1 for it in items if it.get("img"))
    start, end = d["date_range"].split("~")
    return f'''<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>포장재 인텔리전스 {d["number"]}호</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
{FONTS}
<style>{NEWSLETTER_CSS}</style>
</head>
<body>
<div class="wrap">
  <header class="masthead">
    <p class="kicker">PACKAGING INTELLIGENCE · WEEKLY</p>
    <h1 class="masthead-title">{esc(d["masthead_title"])}</h1>
    <div class="meta-bar">
      <span class="accent">{d["number"]}호</span><span class="meta-sep">·</span>
      {esc(start)} &ndash; {esc(end)}<span class="meta-sep">·</span>
      신선 <b>{len(items)}</b>건<span class="meta-sep">·</span>
      규제 <span class="accent">{len(reg)}</span><span class="meta-sep">·</span>
      사진 {n_photos}
    </div>
  </header>

  <div class="summary">
    <p class="summary-label">AI 요약 노트</p>
    <p>{esc(d["summary"])}</p>
  </div>

  <section class="section">
    <div class="section-head">
      <span class="section-kicker">규제 레이더 · REGULATION</span>
      <h2 class="section-title">{esc(d["reg_section_title"])}</h2>
    </div>
    <div class="item-grid">{"".join(render_item(it) for it in reg)}</div>
  </section>

  <section class="section">
    <div class="section-head">
      <span class="section-kicker">이번 주 신호 · SIGNALS</span>
      <h2 class="section-title">그 외 혁신 신호</h2>
    </div>
    <div class="item-grid">{"".join(render_item(it) for it in sig)}</div>
  </section>

  <div class="footer">exj31 Packaging Intelligence · 구글 검색 기반 신호 수집 · 발행 지난 7일 신규 · 팩트 무손실(추측 금지)</div>
</div>
</body>
</html>'''


REG_CSS = """
:root {
  --paper: #FAF8F4; --ink: #17191D; --ink-soft: #4A4D55; --slate: #6B6F7B;
  --accent: #1B4FE0; --accent-soft: #EEF2FF; --accent-line: #C9D6FB;
  --line: #E6E4DC; --card: #FFFFFF;
  --current: #2E75B6; --current-soft: #EBF3FB;
  --future: #7B2D8B; --future-soft: #F5EEF8;
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    --paper: #14151A; --ink: #F2F1ED; --ink-soft: #C7C6C2; --slate: #93949E;
    --accent: #6E93FF; --accent-soft: #1B2340; --accent-line: #33417A;
    --line: #2A2B30; --card: #1B1C22;
    --current: #6FA8E8; --current-soft: #16232F;
    --future: #C48AD1; --future-soft: #241B2A;
  }
}
:root[data-theme="dark"] {
  --paper: #14151A; --ink: #F2F1ED; --ink-soft: #C7C6C2; --slate: #93949E;
  --accent: #6E93FF; --accent-soft: #1B2340; --accent-line: #33417A;
  --line: #2A2B30; --card: #1B1C22;
  --current: #6FA8E8; --current-soft: #16232F;
  --future: #C48AD1; --future-soft: #241B2A;
}
* { box-sizing: border-box; }
body { margin: 0; background: var(--paper); color: var(--ink);
  font-family: 'IBM Plex Sans KR', 'Apple SD Gothic Neo', 'Malgun Gothic', sans-serif; padding: 0 16px; }
.wrap { max-width: 700px; margin: 0 auto; padding-block: 48px 80px; }
.masthead { padding-bottom: 24px; border-bottom: 2px solid var(--ink); margin-bottom: 28px; }
.kicker { font-size: 12px; letter-spacing: 0.2em; font-weight: 700; color: var(--accent);
  text-transform: uppercase; margin: 0 0 14px; }
h1 { font-family: 'Noto Serif KR', serif; font-weight: 900; font-size: clamp(26px, 5vw, 36px);
  line-height: 1.22; margin: 0 0 14px; text-wrap: balance; }
.meta-line { font-size: 13px; color: var(--slate); line-height: 1.7; }
.greeting { border: 1px solid var(--accent-line); background: var(--accent-soft);
  border-radius: 4px; padding: 20px 22px; margin: 28px 0 40px; font-size: 14.5px; line-height: 1.75; color: var(--ink); }
.reg-section { margin-bottom: 40px; }
.section-head { display: flex; align-items: baseline; gap: 12px; margin-bottom: 16px;
  border-bottom: 1px solid var(--ink); padding-bottom: 10px; }
.section-kicker { font-size: 12px; letter-spacing: 0.14em; font-weight: 700; white-space: nowrap; }
.reg-section.current .section-kicker { color: var(--current); }
.reg-section.future .section-kicker { color: var(--future); }
.section-title { font-family: 'Noto Serif KR', serif; font-weight: 700; font-size: 19px; margin: 0; color: var(--ink-soft); }
.reg-grid { display: flex; flex-direction: column; gap: 10px; }
.reg-item { border-left: 4px solid var(--item-accent); border-radius: 0 6px 6px 0;
  padding: 14px 18px; background: var(--card); border-top: 1px solid var(--line);
  border-right: 1px solid var(--line); border-bottom: 1px solid var(--line); }
.reg-item-title { font-weight: 700; font-size: 15px; margin-bottom: 6px; color: var(--ink); }
.reg-item-title a { color: inherit; text-decoration: none; border-bottom: 1px solid var(--item-accent); }
.reg-item-title a:hover { color: var(--item-accent); }
.reg-item-body { font-size: 13.5px; line-height: 1.68; color: var(--ink-soft); margin: 0; }
.footer { margin-top: 50px; padding-top: 20px; border-top: 1px solid var(--line);
  font-size: 11.5px; line-height: 1.8; color: var(--slate); }
"""

NUMS = "①②③④⑤⑥⑦⑧⑨⑩"


def render_reg(it, idx, is_future):
    accent = "var(--future)" if is_future else "var(--current)"
    return f'''<div class="reg-item" style="--item-accent:{accent};">
<div class="reg-item-title"><a href="{esc(it["url"], quote=True)}" target="_blank" rel="noopener">{NUMS[idx]}{esc(it["title"])}</a></div>
<p class="reg-item-body">{esc(it["body"])}</p>
</div>'''


def build_regulation(d):
    start, end = d["date_range"].split("~")
    y = start[:4]
    ks = start.split(".")
    ke = end.split(".")
    end_full = end if len(ke) == 3 else f"{y}.{end}"
    ke = end_full.split(".")
    range_kr = f"{ks[0]}년 {ks[1]}월 {ks[2]}일 ~ {ke[0]}년 {ke[1]}월 {ke[2]}일"
    cur = "".join(render_reg(it, i, False) for i, it in enumerate(d["regulation_current"]))
    fut = "".join(render_reg(it, i, True) for i, it in enumerate(d["regulation_future"]))
    return f'''<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>친환경·포장재 규제 리포트 {d["number"]}호</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
{FONTS}
<style>{REG_CSS}</style>
</head>
<body>
<div class="wrap">
  <header class="masthead">
    <p class="kicker">ECO PACKAGING REGULATION · WEEKLY</p>
    <h1>친환경·포장재 규제 최신 동향 리포트</h1>
    <p class="meta-line">수집 기간: {range_kr} &nbsp;│&nbsp; 키워드: Packaging regulations · eco-friendly policy · Plastic regulations · Cosmetic packaging regulations · PPWR</p>
  </header>

  <div class="greeting">안녕하세요, 최근 1주일간 구글 검색 기반으로 수집한 친환경 포장재 및 규제 관련 주요 동향을 정리하여 전달 드립니다.</div>

  <section class="reg-section current">
    <div class="section-head"><span class="section-kicker">CURRENT TRENDS</span><h2 class="section-title">▶ 현재 동향 (Current Trends)</h2></div>
    <div class="reg-grid">{cur}</div>
  </section>

  <section class="reg-section future">
    <div class="section-head"><span class="section-kicker">FUTURE OUTLOOK</span><h2 class="section-title">▶ 앞으로의 동향 (Future Outlook)</h2></div>
    <div class="reg-grid">{fut}</div>
  </section>

  <div class="footer">본 리포트는 구글 검색 기반 자동 수집 시스템을 통해 작성되었습니다.</div>
</div>
</body>
</html>'''


INDEX_CSS = """
:root {
  --paper: #FAF8F4; --ink: #17191D; --ink-soft: #4A4D55; --slate: #6B6F7B;
  --accent: #1B4FE0; --accent-soft: #EEF2FF; --accent-line: #C9D6FB; --line: #E6E4DC; --card: #FFFFFF;
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    --paper: #14151A; --ink: #F2F1ED; --ink-soft: #C7C6C2; --slate: #93949E;
    --accent: #6E93FF; --accent-soft: #1B2340; --accent-line: #33417A; --line: #2A2B30; --card: #1B1C22;
  }
}
:root[data-theme="dark"] {
  --paper: #14151A; --ink: #F2F1ED; --ink-soft: #C7C6C2; --slate: #93949E;
  --accent: #6E93FF; --accent-soft: #1B2340; --accent-line: #33417A; --line: #2A2B30; --card: #1B1C22;
}
* { box-sizing: border-box; }
body { margin: 0; background: var(--paper); color: var(--ink);
  font-family: 'IBM Plex Sans KR', 'Apple SD Gothic Neo', 'Malgun Gothic', sans-serif; padding: 0 16px; }
.wrap { max-width: 680px; margin: 0 auto; padding-block: 48px 80px; }
.kicker { font-size: 12px; letter-spacing: 0.22em; font-weight: 700; color: var(--accent);
  text-transform: uppercase; margin: 0 0 14px; }
h1 { font-family: 'Noto Serif KR', serif; font-weight: 900; font-size: clamp(28px, 5vw, 38px);
  line-height: 1.2; margin: 0 0 10px; text-wrap: balance; }
.sub { font-size: 14.5px; color: var(--slate); margin: 0 0 40px; line-height: 1.6; }
.issue-list { display: flex; flex-direction: column; border-top: 2px solid var(--ink); }
.issue-row { display: flex; justify-content: space-between; align-items: baseline;
  gap: 16px; padding: 22px 4px; border-bottom: 1px solid var(--line); text-decoration: none; color: inherit; }
.issue-row.reg-row { padding: 0 4px 18px; border-bottom: 1px solid var(--line); }
.issue-row:hover .issue-title { color: var(--accent); }
.issue-no { font-family: 'Noto Serif KR', serif; font-weight: 700; font-size: 13px; color: var(--accent); min-width: 44px; }
.issue-main { flex: 1; }
.issue-title { font-family: 'Noto Serif KR', serif; font-weight: 700; font-size: 18px; margin: 0 0 4px; }
.issue-title-sm { font-size: 13px; color: var(--slate); margin: 0; }
.issue-row.reg-row:hover .issue-title-sm { color: var(--accent); }
.issue-range { font-size: 12.5px; color: var(--slate); font-variant-numeric: tabular-nums; }
.issue-stats { font-size: 12px; color: var(--slate); text-align: right; white-space: nowrap; }
"""


def build_index(issues):
    rows = []
    for i in sorted(issues, key=lambda x: -x["number"]):
        rows.append(f'''<a class="issue-row" href="{BASE_URL}{i['newsletter_path']}" target="_blank" rel="noopener">
      <span class="issue-no">{i['number']}호</span>
      <span class="issue-main">
        <p class="issue-title">{esc(i['masthead_title'])}</p>
        <p class="issue-range">{esc(i['date_range']).replace('~', ' &ndash; ')}</p>
      </span>
      <span class="issue-stats">신선 {i['newsletter_items']}건<br>사진 {i['photo_count']}장</span>
    </a>
    <a class="issue-row reg-row" href="{BASE_URL}{i['regulation_path']}" target="_blank" rel="noopener">
      <span class="issue-no"></span>
      <span class="issue-main">
        <p class="issue-title-sm">→ 친환경·포장재 규제 리포트 (현재 {i['regulation_current']}건 · 앞으로 {i['regulation_future']}건)</p>
      </span>
    </a>''')
    return f'''<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>포장재 인텔리전스 아카이브</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Noto+Serif+KR:wght@700;900&family=IBM+Plex+Sans+KR:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>{INDEX_CSS}</style>
</head>
<body>
<div class="wrap">
  <p class="kicker">PACKAGING INTELLIGENCE · ARCHIVE</p>
  <h1>포장재 인텔리전스</h1>
  <p class="sub">주간 포장재 산업 뉴스레터와 친환경·포장재 규제 동향 리포트를 한 곳에 모았습니다.</p>
  <div class="issue-list">
    {chr(10).join(rows)}
  </div>
</div>
</body>
</html>'''


def build(repo, issue_path):
    d = json.load(open(issue_path, encoding="utf-8"))
    n = d["number"]
    nl_path, reg_path = f"newsletter-{n}.html", f"regulation-{n}.html"
    open(os.path.join(repo, nl_path), "w", encoding="utf-8").write(build_newsletter(d))
    open(os.path.join(repo, reg_path), "w", encoding="utf-8").write(build_regulation(d))
    ipath = os.path.join(repo, "issues.json")
    issues = json.load(open(ipath, encoding="utf-8")) if os.path.exists(ipath) else []
    issues = [i for i in issues if i["number"] != n]
    issues.append({
        "number": n, "date_range": d["date_range"],
        "newsletter_path": nl_path, "regulation_path": reg_path,
        "newsletter_items": len(d["newsletter_items"]),
        "photo_count": sum(1 for it in d["newsletter_items"] if it.get("img")),
        "regulation_current": len(d["regulation_current"]),
        "regulation_future": len(d["regulation_future"]),
        "masthead_title": d["masthead_title"],
    })
    issues.sort(key=lambda i: i["number"])
    json.dump(issues, open(ipath, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    open(os.path.join(repo, "index.html"), "w", encoding="utf-8").write(build_index(issues))
    return issues[-1] if issues[-1]["number"] == n else [i for i in issues if i["number"] == n][0]


if __name__ == "__main__":
    print(json.dumps(build(sys.argv[1], sys.argv[2]), ensure_ascii=False))

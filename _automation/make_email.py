# -*- coding: utf-8 -*-
"""Fixed weekly email (inline styles only; survives Gmail's sanitizer).

Usage: python make_email.py <repo_root> <issue_number>
Prints JSON {"subject": ..., "html": ...}.
"""
import html as htmlmod
import json
import os
import sys

BASE_URL = "https://angbabyang-ux.github.io/packaging-intelligence-reports/"
FONT = "'Apple SD Gothic Neo','Malgun Gothic',sans-serif"
INK, SLATE, ACCENT, FUTURE, LINE = "#17191D", "#6B6F7B", "#1B4FE0", "#7B2D8B", "#E6E4DC"


def issue_row(no, title, date_range, url, stats, accent):
    no_html = (f'<span style="font-weight:700;font-size:13px;color:{accent};min-width:34px;display:inline-block;vertical-align:top;">{no}</span>'
               if no else '<span style="min-width:34px;display:inline-block;"></span>')
    return f'''<tr>
<td style="padding:20px 0;border-bottom:1px solid {LINE};" valign="top">
<a href="{url}" target="_blank" style="text-decoration:none;color:inherit;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr>
<td width="34" valign="top" style="padding-right:10px;">{no_html}</td>
<td valign="top">
<div style="font-weight:700;font-size:17px;color:{INK};margin:0 0 4px;">{title}</div>
<div style="font-size:12.5px;color:{SLATE};">{date_range}</div>
</td>
<td valign="top" align="right" style="font-size:11.5px;color:{SLATE};line-height:1.6;white-space:nowrap;padding-left:12px;">{'<br>'.join(stats)}</td>
</tr></table>
</a>
</td>
</tr>'''


def make(repo, n):
    issues = json.load(open(os.path.join(repo, "issues.json"), encoding="utf-8"))
    i = [x for x in issues if x["number"] == n][0]
    rng = htmlmod.escape(i["date_range"]).replace("~", " &ndash; ")
    nl = issue_row(f'{n}호', htmlmod.escape(i["masthead_title"]), rng, BASE_URL + i["newsletter_path"],
                   [f'신선 {i["newsletter_items"]}건', f'사진 {i["photo_count"]}장'], ACCENT)
    rg = issue_row('', '친환경·포장재 규제 최신 동향', rng, BASE_URL + i["regulation_path"],
                   [f'현재 동향 {i["regulation_current"]}건', f'앞으로의 동향 {i["regulation_future"]}건'], FUTURE)
    body = f'''<div style="max-width:640px;margin:0 auto;font-family:{FONT};padding:36px 20px;">
<p style="font-size:11px;letter-spacing:.2em;font-weight:700;color:{ACCENT};margin:0 0 14px;">PACKAGING INTELLIGENCE &middot; WEEKLY</p>
<h1 style="font-size:30px;font-weight:900;line-height:1.2;margin:0 0 12px;color:{INK};">포장재 인텔리전스</h1>
<p style="font-size:14.5px;color:{SLATE};line-height:1.6;margin:0 0 36px;">주간 포장재 산업 뉴스레터와 친환경&middot;포장재 규제 동향 리포트를 한 곳에 모았습니다.</p>

<div style="margin-bottom:36px;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="border-bottom:2px solid {INK};padding-bottom:10px;margin-bottom:4px;">
<tr><td style="padding-bottom:10px;">
<span style="color:{ACCENT};font-size:16px;">&#9679;</span>
<span style="font-weight:700;font-size:17px;color:{INK};margin-left:10px;">포장재 뉴스레터</span>
</td></tr>
</table>
<p style="font-size:12.5px;color:{SLATE};margin:8px 0 0;">주간 포장재 산업 신호와 규제 레이더를 사진과 함께 정리합니다.</p>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0">
{nl}
</table>
</div>

<div style="margin-bottom:28px;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="border-bottom:2px solid {INK};padding-bottom:10px;margin-bottom:4px;">
<tr><td style="padding-bottom:10px;">
<span style="color:{FUTURE};font-size:16px;">&#9679;</span>
<span style="font-weight:700;font-size:17px;color:{INK};margin-left:10px;">친환경&middot;포장재 규제 최신 동향 리포트</span>
</td></tr>
</table>
<p style="font-size:12.5px;color:{SLATE};margin:8px 0 0;">현재&middot;앞으로의 규제 동향을 원문 링크와 함께 정리합니다.</p>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0">
{rg}
</table>
</div>

<p style="font-size:12.5px;color:{SLATE};margin:0;"><a href="{BASE_URL}" target="_blank" style="color:{ACCENT};text-decoration:none;font-weight:700;">지난 호 전체 보기 &rarr;</a></p>
</div>'''
    subject = f'포장재 인텔리전스 {n}호 — {i["date_range"]}'
    return {"subject": subject, "html": body}


if __name__ == "__main__":
    print(json.dumps(make(sys.argv[1], int(sys.argv[2])), ensure_ascii=False))

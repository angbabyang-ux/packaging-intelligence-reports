#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
packaging_review_email_v4.py
v3와 데이터는 동일(올리브영/아마존/세포라 카테고리별 BEST 5)하지만:
- '포장재 장점/단점'·'포장재 클레임 소지' 열을 제거하고 '제품특징' 열로 교체
  (제품특징 = 실제 스크래핑된 상품명에서 브랜드명을 뺀 나머지 텍스트 — 새로 지어내지 않음)
- 세포라 가격을 원화(KRW)로 환산 표기 (1 EUR ≈ 1,660 KRW, 2026-07-29 기준 근사치 — 실시간 환율 아님)
- 세포라 이미지는 별도로 캡처한 sephora_images_b64.json을 병합해 채운다
리뷰 재스크래핑은 하지 않는다(이번 버전은 리뷰 기반 분석 열 자체가 없음).
"""
import sys, json, re
from datetime import datetime
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')

today = datetime.now().strftime("%Y년 %m월 %d일")
today_tag = datetime.now().strftime("%Y%m%d")

EUR_KRW = 1660  # 근사치, 2026-07-29 기준 (실시간 환율 아님 — 명시 필요)

BASE = Path(__file__).resolve().parent

with open(BASE / "scraped_data.json", encoding="utf-8") as f:
    oy_data = json.load(f)
with open(BASE / "global_scraped.json", encoding="utf-8") as f:
    amazon_data = json.load(f)["아마존"]
with open(BASE / "sephora_final.json", encoding="utf-8") as f:
    sephora_data = json.load(f)

seph_img_path = BASE / "sephora_images_b64.json"
sephora_images = json.loads(seph_img_path.read_text(encoding="utf-8")) if seph_img_path.exists() else {}
print(f"세포라 이미지 캡처본: {len(sephora_images)}개 로드")

def krw_price(raw, site):
    """가격 문자열을 원화 표기로 통일. 이미 원화(올리브영/아마존)면 그대로, 유로(세포라)면 환산."""
    if site != "sephora":
        return raw
    m = re.search(r"([\d.,]+)", raw or "")
    if not m:
        return raw
    val = float(m.group(1).replace(",", ""))
    krw = round(val * EUR_KRW / 100) * 100  # 100원 단위 반올림
    return f"₩{krw:,} (€{val:.2f} 환산, 1EUR≈{EUR_KRW}원)"

def feature_text(p):
    """제품특징 = 상품명에서 브랜드명 중복 제거 후 표시(새 내용 생성 없이 실데이터만 사용)."""
    name = (p.get("name") or "").strip()
    brand = (p.get("brand") or "").strip()
    if brand and name.lower().startswith(brand.lower()):
        name = name[len(brand):].strip(" -–,:")
    return name or "제품명 정보 없음"

# ─── Email HTML ───────────────────────────────────────────────────────────────
CAT_ICONS = {
    "스킨케어":"&#128167;","메이크업":"&#128132;","헤어케어":"&#128134;",
    "향수":"&#127800;","바디케어":"&#129332;","선케어":"&#9728;&#65039;",
    "클렌징":"&#129703;","구강용품":"&#129463;","향수/디퓨저":"&#127800;",
}
S_TD = "padding:6px 5px;border:1px solid #f0f0f0;vertical-align:middle;font-family:'Malgun Gothic',Arial,sans-serif;font-size:11px;"
S_TH = "padding:6px 7px;border:1px solid #ddd;font-weight:600;font-family:'Malgun Gothic',Arial,sans-serif;font-size:11px;text-align:center;white-space:nowrap;"

def build_category_table(cat_name, products, accent, site):
    icon = CAT_ICONS.get(cat_name, "")
    th   = S_TH + f"background-color:#f5f5f5;color:{accent};"
    thead = f"""<tr>
      <td width="28" style="{th}">순위</td>
      <td width="60" style="{th}">이미지</td>
      <td style="{th}text-align:left;">브랜드 / 제품명</td>
      <td width="110" style="{th}">가격(원화)</td>
      <td style="{th}text-align:left;">제품특징</td>
    </tr>"""
    rows = ""
    for i, p in enumerate(products[:5]):
        url    = p.get("url", "#")
        bg     = "#ffffff" if i % 2 == 0 else "#fafafa"
        td     = S_TD + f"background-color:{bg};"
        img    = sephora_images.get(p.get("image_url","")) if site == "sephora" else p.get("image_url","")
        img_tag = (f'<img src="{img}" width="52" height="52" style="width:52px;height:52px;object-fit:cover;border:1px solid #eee;" alt="">'
                   if img else '<div style="width:52px;height:52px;background:#f0f0f0;"></div>')
        name  = p.get("name","").replace("&","&amp;").replace("<","&lt;")
        brand = p.get("brand","").replace("&","&amp;")
        price = krw_price(p.get("price",""), site).replace("&","&amp;")
        feat  = feature_text(p).replace("&","&amp;").replace("<","&lt;")
        rows += f"""<tr>
      <td width="28" style="{td}text-align:center;font-size:12px;font-weight:700;color:{accent};">#{i+1}</td>
      <td width="60" style="{td}text-align:center;">{img_tag}</td>
      <td style="{td}"><div style="color:#999;font-size:10px;margin-bottom:2px;">{brand}</div>
        <a href="{url}" style="color:#222;text-decoration:none;font-weight:600;font-size:11px;">{name}</a></td>
      <td width="110" style="{td}text-align:right;color:{accent};font-weight:700;white-space:nowrap;">{price}</td>
      <td style="{td}font-size:10.5px;line-height:1.5;color:#444;">{feat}</td>
    </tr>"""
    return f"""<tr><td style="padding:0;">
  <table width="100%" cellpadding="0" cellspacing="0" border="0" style="border-collapse:collapse;">
    <tr><td style="padding:14px 16px 8px;font-family:'Malgun Gothic',Arial,sans-serif;">
      <span style="font-size:14px;font-weight:700;color:{accent};border-bottom:2px solid {accent};padding-bottom:3px;">{icon} {cat_name}</span>
    </td></tr>
    <tr><td style="padding:0 16px 16px;">
      <table width="100%" cellpadding="0" cellspacing="0" border="0" style="border-collapse:collapse;">{thead}{rows}</table>
    </td></tr>
  </table>
  <div style="height:1px;background-color:#eeeeee;margin:0 16px;"></div>
</td></tr>"""

def build_site_section(site_name, base_url, color, accent, products_map, cat_order, site, note=""):
    items = [(c, products_map[c]) for c in cat_order if c in products_map]
    cats  = "".join(build_category_table(cat, prods, accent, site) for cat, prods in items)
    note_html = f'<div style="color:rgba(255,255,255,0.6);font-size:10px;margin-top:4px;">{note}</div>' if note else ""
    return f"""<tr><td style="padding:0;">
  <table width="100%" cellpadding="0" cellspacing="0" border="0" style="border-collapse:collapse;">
    <tr><td style="background-color:{color};padding:18px 20px;">
      <div style="color:#fff;font-size:18px;font-weight:700;font-family:'Malgun Gothic',Arial,sans-serif;margin-bottom:3px;">{site_name} 카테고리별 BEST 5</div>
      <div style="color:rgba(255,255,255,0.7);font-size:11px;font-family:'Malgun Gothic',Arial,sans-serif;">기준일: {today}&nbsp;|&nbsp;출처: {base_url}</div>
      {note_html}
    </td></tr>
    {cats}
  </table>
</td></tr>
<tr><td style="height:20px;background-color:#f0f0f0;"></td></tr>"""

oy_order  = ["스킨케어","메이크업","선케어","클렌징","바디케어","헤어케어","구강용품","향수/디퓨저"]
amz_order = ["스킨케어","메이크업","헤어케어","향수"]
sep_order = ["스킨케어","메이크업","헤어케어","향수","바디케어"]

sections = (
    build_site_section("🛒 올리브영 (OliveYoung)", "www.oliveyoung.co.kr",
                       "#007A33", "#005c26", oy_data, oy_order, "oliveyoung") +
    build_site_section("🛍 아마존 (Amazon)", "www.amazon.com",
                       "#232F3E", "#FF9900", amazon_data, amz_order, "amazon") +
    build_site_section("✨ 세포라 (Sephora)", "www.sephora.fr",
                       "#000000", "#cf0248", sephora_data, sep_order, "sephora",
                       note="※ 가격은 참고용 원화 환산가입니다(1EUR≈1,660원, 실시간 환율 아님)")
)

html = f"""<!DOCTYPE html>
<html xmlns:v="urn:schemas-microsoft-com:vml" xmlns:o="urn:schemas-microsoft-com:office:office">
<head>
<meta charset="UTF-8">
<meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
<title>글로벌 뷰티 플랫폼 BEST 5 통합 리포트 · 제품특징</title>
<!--[if gte mso 9]><xml><o:OfficeDocumentSettings><o:AllowPNG/></o:OfficeDocumentSettings></xml><![endif]-->
</head>
<body style="margin:0;padding:16px;background-color:#f0f0f0;font-family:'Malgun Gothic',Arial,sans-serif;">
<table width="980" cellpadding="0" cellspacing="0" border="0" align="center"
       style="background-color:#ffffff;border-collapse:collapse;max-width:980px;width:100%;">
  <tr>
    <td style="background-color:#1a1a2e;padding:24px 24px 20px;">
      <div style="color:#ffffff;font-size:22px;font-weight:700;font-family:'Malgun Gothic',Arial,sans-serif;margin-bottom:6px;">
        &#127799; 글로벌 뷰티 플랫폼 BEST 5 통합 리포트
      </div>
      <div style="color:rgba(255,255,255,0.65);font-size:12px;font-family:'Malgun Gothic',Arial,sans-serif;">
        기준일: {today}&nbsp;&nbsp;|&nbsp;&nbsp;올리브영 · 아마존 · 세포라 3개 플랫폼 통합&nbsp;&nbsp;|&nbsp;&nbsp;가격은 전부 원화 표기
      </div>
    </td>
  </tr>
  {sections}
  <tr>
    <td style="padding:14px 20px;background-color:#f7f7f7;text-align:center;font-size:10px;color:#aaa;font-family:'Malgun Gothic',Arial,sans-serif;">
      ※ 제품특징은 각 사이트에 실제 등록된 상품명을 그대로 옮긴 것입니다(별도 해석·평가 없음). | 생성일: {today}
    </td>
  </tr>
</table>
</body></html>"""

out_path = str(BASE / f"통합리포트_포장재_v4_{today_tag}.html")
with open(out_path, "w", encoding="utf-8") as f:
    f.write(html)
kb = len(html.encode()) / 1024
print(f"\nHTML: {kb:.1f} KB  ({len(html):,} chars) -> {out_path}")

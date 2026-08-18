# -*- coding: utf-8 -*-
"""친환경·포장재 규제 리포트 — 무인 주간 자동 실행용.
RSS 수집 → 중복제거 → 번역 → (로컬 claude CLI로 요약 생성, anthropic API 키 불필요) → 엑셀+HTML.
"""
import sys, os, json, subprocess
from pathlib import Path

# Windows 콘솔이 cp949일 때 특수문자 print가 죽는 문제 방지 (작업 스케줄러 비대화식 실행 대비)
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))
import packaging_news_auto as m

_CLAUDE_ENV = {**os.environ, 'PYTHONIOENCODING': 'utf-8', 'PYTHONUTF8': '1'}


def claude_summarize(articles):
    """anthropic API 키 없이, 로컬 claude CLI로 현재/미래 동향 요약을 생성한다.
    실패 시에도 절대 _default_summary()의 하드코딩된 stale 텍스트는 쓰지 않는다 —
    실패하면 최소한의 사실 나열(지역별 건수)만 담은 요약으로 대체한다."""
    sample = articles[:60]
    lines = "\n".join(f"- [{a['region']}] {a['title_ko'] or a['title']} ({a['date']})" for a in sample)
    prompt = f"""다음은 최근 1주일간 구글 뉴스에서 수집된 친환경·포장재 규제 관련 기사 목록이다 (총 {len(articles)}건 중 샘플 {len(sample)}건).
키워드: Packaging regulations, eco-friendly policy, Plastic regulations, Cosmetic packaging regulations, PPWR

{lines}

위 기사 "제목에 실제로 있는 내용만" 근거로 아래 두 섹션을 작성하라. 기사에 없는 통계·날짜·법률명을 지어내지 마라.
각 섹션은 3~5개 항목, 항목마다 ①②③ 번호 + 짧은 소제목 + 2~3문장 본문.

[현재 동향]
[앞으로의 동향]

JSON만 출력: {{"current":"...","future":"..."}}"""
    try:
        r = subprocess.run(
            ['claude', '-p', '--output-format', 'json', '--model', 'sonnet'],
            input=prompt, capture_output=True, text=True, timeout=180,
            shell=(sys.platform == 'win32'), env=_CLAUDE_ENV, cwd=str(BASE))
        if r.returncode != 0:
            raise RuntimeError(f'claude rc={r.returncode}: {r.stderr[:200]}')
        outer = json.loads(r.stdout)
        if outer.get('is_error'):
            raise RuntimeError(str(outer.get('result'))[:200])
        txt = outer.get('result', '')
        import re
        txt = re.sub(r'^```\w*\s*|\s*```$', '', txt.strip())
        d = json.loads(txt)
        if d.get('current') and d.get('future'):
            return d
        raise RuntimeError('빈 요약')
    except Exception as e:
        print(f'  [경고] claude 요약 실패({e}) - 사실 나열형 대체 요약 사용', flush=True)
        from collections import Counter
        rc = Counter(a['region'] for a in articles)
        top = " / ".join(f"{r}({c}건)" for r, c in rc.most_common(6))
        fallback = (f"①이번 주 수집 현황\n구글 뉴스에서 포장재·친환경 규제 키워드로 총 {len(articles)}건(중복 제거 후)을 "
                    f"수집했다. 지역별 분포: {top}.\n\n"
                    "②자동 요약 생성 실패\nAI 요약 생성이 이번 주는 실패해 상세 동향 서술을 생략한다. "
                    "첨부 엑셀의 기사 목록을 직접 확인해 달라.")
        return {"current": fallback, "future": fallback}


def main():
    print("[1/4] 구글 뉴스 RSS 수집...", flush=True)
    raw = m.collect_all_articles()
    print(f"  총 수집: {len(raw)}건", flush=True)

    print("[2/4] 중복 제거...", flush=True)
    uniq = m.deduplicate(raw)
    print(f"  중복 제거 후: {len(uniq)}건", flush=True)

    print("[3/4] 한국어 번역...", flush=True)
    uniq = m.translate_batch(uniq)

    print("[4/4] 동향 요약 생성(로컬 claude CLI)...", flush=True)
    summary = claude_summarize(uniq)

    m.build_excel(uniq, summary, m.OUTPUT_FILE)
    html = m._build_html_body(uniq, summary)
    out_path = str(Path(r'c:\claude\gh_pages_site\regulation.html'))
    open(out_path, 'w', encoding='utf-8').write(html)
    print(f"HTML: {out_path}")


if __name__ == '__main__':
    main()

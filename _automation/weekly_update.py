# -*- coding: utf-8 -*-
"""포장재 인텔리전스 주간 자동 갱신 — Windows 작업 스케줄러 전용 (사람 검토 없이 바로 게시).

순서: 뉴스레터 파이프라인 재실행 → BEST5 리포트 재생성 → 규제 동향 리포트 재생성
     → 이미지 임베드 → index.html 날짜 갱신 → git commit/push.

주의: 이 스크립트는 팩트체크를 하지 않는다(사용자가 명시적으로 선택한 트레이드오프, 2026-08-06).

2026-08-18: C:\\claude 루트에 흩어져 있던 스크립트·데이터가 통째로 사라지는 사고 이후,
이 폴더(gh_pages_site\\_automation, git으로 버전관리됨) 안으로 전부 옮겼다.
동시에 Windows 콘솔 cp949 인코딩 크래시(이모지/특수문자 print)와,
C:\\claude 워크스페이스가 "신뢰되지 않음" 상태라 claude CLI 호출이 비대화식으로 실패하던
두 가지 버그도 함께 고쳤다(각각: 자식 프로세스에 PYTHONIOENCODING 강제 주입 / ~/.claude.json에
projects["C:/claude"].hasTrustDialogAccepted=true 추가).
"""
import subprocess, sys, os, re
from datetime import datetime
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')

BASE = Path(__file__).resolve().parent          # ...\gh_pages_site\_automation
GH_SITE = BASE.parent                            # ...\gh_pages_site
sys.path.insert(0, str(BASE))
from embed_images_lib import embed_all_images

_ENV = {**os.environ, 'PYTHONIOENCODING': 'utf-8', 'PYTHONUTF8': '1'}

LOG = []
def log(msg):
    print(msg, flush=True)
    LOG.append(msg)

TODAY = datetime.now().strftime('%Y-%m-%d')
TODAY_KR = datetime.now().strftime('%Y년 %m월 %d일')

NEWSLETTER_DIR = Path(r"C:\Users\amore\Downloads\Packaging_Newsletter_인수인계_20260728\exj41. Packaging Newsletter")

log(f"=== 포장재 인텔리전스 주간 자동 갱신 {TODAY} ===")

# ── 1. 뉴스레터 파이프라인 ──────────────────────────────────────────
log("\n[1/3] 포장재 뉴스레터 파이프라인 재실행...")
r = subprocess.run([sys.executable, 'scripts/run_weekly.py'], cwd=str(NEWSLETTER_DIR),
                   capture_output=True, text=True, timeout=5400, env=_ENV)
log(r.stdout[-4000:] if r.stdout else '(출력 없음)')
if r.returncode != 0:
    log(f"  !! run_weekly.py 실패(rc={r.returncode}): {r.stderr[-1500:]}")
else:
    story_src = NEWSLETTER_DIR / 'letters' / f'story_{TODAY}_latest.html'
    if story_src.exists():
        html = story_src.read_text(encoding='utf-8')
        log("  이미지 임베드 중...")
        html = embed_all_images(html)
        (GH_SITE / 'newsletter.html').write_text(html, encoding='utf-8')
        log(f"  newsletter.html 갱신 완료 ({len(html):,}자)")
    else:
        log(f"  !! 레터 파일 없음: {story_src}")

# ── 2. BEST5 제품 특징 리포트 ────────────────────────────────────────
log("\n[2/3] BEST5 제품 특징 리포트 재생성...")
r = subprocess.run([sys.executable, 'packaging_review_email_v4.py'], cwd=str(BASE),
                   capture_output=True, text=True, timeout=600, env=_ENV)
log(r.stdout[-3000:] if r.stdout else '(출력 없음)')
if r.returncode != 0:
    log(f"  !! packaging_review_email_v4.py 실패(rc={r.returncode}): {r.stderr[-1500:]}")
else:
    today_tag = datetime.now().strftime('%Y%m%d')
    best5_src = BASE / f'통합리포트_포장재_v4_{today_tag}.html'
    if best5_src.exists():
        html = best5_src.read_text(encoding='utf-8')
        log("  이미지 임베드 중...")
        html = embed_all_images(html)
        (GH_SITE / 'best5.html').write_text(html, encoding='utf-8')
        log(f"  best5.html 갱신 완료 ({len(html):,}자)")
    else:
        log(f"  !! BEST5 리포트 파일 없음: {best5_src}")

# ── 3. 친환경·포장재 규제 동향 리포트 (regulation.html은 스크립트가 직접 씀) ──
log("\n[3/3] 규제 동향 리포트 재생성...")
r = subprocess.run([sys.executable, 'weekly_regulation_build.py'], cwd=str(BASE),
                   capture_output=True, text=True, timeout=1800, env=_ENV)
log(r.stdout[-3000:] if r.stdout else '(출력 없음)')
if r.returncode != 0:
    log(f"  !! weekly_regulation_build.py 실패(rc={r.returncode}): {r.stderr[-1500:]}")

# ── 4. index.html 날짜만 갱신 ────────────────────────────────────────
idx = GH_SITE / 'index.html'
t = idx.read_text(encoding='utf-8')
t = re.sub(r'\d{4}년 \d{2}월 \d{2}일', TODAY_KR, t)
idx.write_text(t, encoding='utf-8')
log(f"\nindex.html 날짜 갱신: {TODAY_KR}")

# ── 5. git commit & push ────────────────────────────────────────────
log("\n[git] 커밋 및 푸시...")
subprocess.run(['git', 'add', 'index.html', 'newsletter.html', 'best5.html', 'regulation.html'],
               cwd=str(GH_SITE))
r = subprocess.run(['git', '-c', 'user.email=angbabyang@gmail.com', '-c', 'user.name=angbabyang-ux',
                    'commit', '-m', f'Weekly auto-update {TODAY}'],
                   cwd=str(GH_SITE), capture_output=True, text=True)
log(r.stdout + r.stderr)
r = subprocess.run(['git', 'push'], cwd=str(GH_SITE), capture_output=True, text=True)
log(r.stdout + r.stderr)

log(f"\n=== 완료 {TODAY} - https://angbabyang-ux.github.io/packaging-intelligence-reports/ ===")

log_path = BASE / f'weekly_update_log_{TODAY}.txt'
log_path.write_text('\n'.join(LOG), encoding='utf-8')

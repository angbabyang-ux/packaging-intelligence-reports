# -*- coding: utf-8 -*-
"""HTML 내 hotlink 이미지를 base64 JPEG로 임베드하는 공용 헬퍼 (주간 자동화용)."""
import re, io, base64, urllib.request, ssl
from PIL import Image

UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
_CTX = ssl.create_default_context(); _CTX.check_hostname = False; _CTX.verify_mode = ssl.CERT_NONE


def embed_all_images(html, max_width=640, quality=74):
    urls = sorted(set(re.findall(r'src="(https?://[^"]+)"', html)))
    ok = fail = 0
    for u in urls:
        try:
            req = urllib.request.Request(u, headers={'User-Agent': UA, 'Referer': u})
            raw = urllib.request.urlopen(req, timeout=15, context=_CTX).read()
            img = Image.open(io.BytesIO(raw)).convert('RGB')
            if img.width > max_width:
                img = img.resize((max_width, int(img.height * max_width / img.width)), Image.LANCZOS)
            buf = io.BytesIO(); img.save(buf, format='JPEG', quality=quality, optimize=True)
            b64 = base64.b64encode(buf.getvalue()).decode('ascii')
            html = html.replace(f'src="{u}"', f'src="data:image/jpeg;base64,{b64}"')
            ok += 1
        except Exception:
            html = re.sub(r'<img\b[^>]*\bsrc="' + re.escape(u) + r'"[^>]*/?>', '', html)
            fail += 1
    print(f'  이미지 임베드 {ok}/{ok+fail} (실패 {fail}는 제거)', flush=True)
    return html

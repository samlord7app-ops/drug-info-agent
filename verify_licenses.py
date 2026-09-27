import urllib.request
import urllib.parse
import ssl
import re

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

drugs = {
    "bokey": "衛署藥製字第037344號",
    "lipitor": "衛署藥輸字第022886號",
    "tagrisso": "衛署藥輸字第026968號",
    "crestor": "衛署藥輸字第024131號",
    "norvasc": "衛署藥輸字第017124號",
    "plavix": "衛署藥輸字第023020號",
    "panadol": "衛署藥輸字第023611號"
}

for name, lic in drugs.items():
    url = f"https://mcp.fda.gov.tw/im_detail_1/{urllib.parse.quote(lic)}"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, context=ctx, timeout=8) as r:
            html = r.read().decode('utf-8', errors='ignore')
            # Check if this page contains the actual drug content (length > 75000 and has 適應症)
            has_ind = '適應症' in html
            print(f"{name} ({lic}): status={r.status}, len={len(html)}, has_indications={has_ind}")
    except Exception as e:
        print(f"{name} ({lic}): ERR={e}")

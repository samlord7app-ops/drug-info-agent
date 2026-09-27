import re
import urllib.request
import urllib.parse
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def test_resolve(drug_name):
    # Try searching DDG lite or duckduckgo html for the license
    q = urllib.parse.quote(f"{drug_name} 衛署藥輸字第 OR 衛署藥製字第 OR 衛部藥輸字第 OR 衛部藥製字第")
    url = f"https://html.duckduckgo.com/html/?q={q}"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=6) as r:
            html = r.read().decode('utf-8', errors='ignore')
            m = re.search(r'(衛[署部]藥[製輸]字第\s*\d+\s*號)', html)
            if m:
                clean_lic = re.sub(r'\s+', '', m.group(1))
                return clean_lic
    except Exception as e:
        print("Search err:", e)
    return None

print("Resolve amlodipine:", test_resolve("amlodipine"))
print("Resolve metformin:", test_resolve("metformin"))

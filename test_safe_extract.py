import re
import urllib.request
import urllib.parse
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

HEADERS = {'User-Agent': 'Mozilla/5.0'}

def clean_html_str(val):
    if not val:
        return ""
    try:
        t = re.sub(r'<[^>]+>', ' ', str(val))
        return ' '.join(t.split()).strip()
    except Exception:
        return ""

def extract_field(label_kw, clean_text):
    if not clean_text:
        return ""
    m = re.search(rf"{label_kw}.*?<p[^>]*>(.*?)</p>", clean_text, re.DOTALL | re.IGNORECASE)
    if m and m.lastindex and m.group(1):
        res = clean_html_str(m.group(1))
        if res:
            return res
    m2 = re.search(rf"{label_kw}\s*[:：]?\s*([^<\n\r]+)", clean_text, re.IGNORECASE)
    if m2 and m2.lastindex and m2.group(1):
        return clean_html_str(m2.group(1))
    return ""

def extract_section(start_kw, end_kw, clean_text):
    if not clean_text:
        return "詳見原廠核定仿單說明。"
    try:
        m = re.search(rf"({start_kw})(.*?)({end_kw})", clean_text, re.DOTALL | re.IGNORECASE)
        if m and len(m.groups()) >= 2 and m.group(2):
            res = clean_html_str(m.group(2))
            if len(res) > 10:
                return res
    except Exception:
        pass
    return "詳見原廠核定仿單說明。"

# Test with Crestor (the one that crashed before)
url = "https://mcp.fda.gov.tw/im_detail_1/" + urllib.parse.quote('衛署藥輸字第024131號')
req = urllib.request.Request(url, headers=HEADERS)
with urllib.request.urlopen(req, context=ctx, timeout=8) as r:
    html = r.read().decode('utf-8', errors='ignore')

clean = re.sub(r'<(?:script|style).*?</(?:script|style)>', '', html, flags=re.DOTALL | re.IGNORECASE)
cname = extract_field(r"中文品名", clean)
mfg = extract_field(r"製造廠名稱|申請商名稱", clean)
ind = extract_section(r"2\s*適應症", r"3\s*用法及用量|3\s*用法用量", clean)

print("Crestor test:")
print("Cname:", cname)
print("Mfg:", mfg)
print("Indications:", ind[:100])

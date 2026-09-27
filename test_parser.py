import urllib.request, ssl, sys, re
sys.stdout.reconfigure(encoding='utf-8')

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

url = 'https://mcp.fda.gov.tw/im_detail_1/%E8%A1%9B%E9%83%A8%E8%8F%8C%E7%96%AB%E8%BC%B8%E5%AD%97%E7%AC%AC001200%E8%99%9F'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req, context=ctx, timeout=10) as r:
    html_content = r.read().decode('utf-8', errors='ignore')

# 找到所有 title-name 的 tr
header_pattern = re.compile(
    r'<tr[^>]*>\s*<td[^>]*class=[\'"][^\'"]*title-name[^\'"]*[\'"][^>]*>\s*(\d+(?:\.\d+)*)\s*</td>\s*<td[^>]*class=[\'"][^\'"]*title-name[^\'"]*[\'"][^>]*>(.*?)</td>\s*</tr>',
    re.IGNORECASE | re.DOTALL
)

headers = list(header_pattern.finditer(html_content))
print(f'Total headers found: {len(headers)}')

for i, h in enumerate(headers):
    num = h.group(1).strip()
    title = re.sub(r'<[^>]+>', '', h.group(2)).strip()
    next_start = headers[i+1].start() if i+1 < len(headers) else len(html_content)
    raw_content = html_content[h.end():next_start]
    
    clean_txt = re.sub(r'<script.*?</script>', '', raw_content, flags=re.DOTALL)
    clean_txt = re.sub(r'<style.*?</style>', '', clean_txt, flags=re.DOTALL)
    clean_txt = re.sub(r'<br\s*/?>', '\n', clean_txt)
    clean_txt = re.sub(r'</p>', '\n', clean_txt)
    clean_txt = re.sub(r'<[^>]+>', '', clean_txt).strip()
    clean_txt = re.sub(r'\n{3,}', '\n\n', clean_txt)
    
    if any(k in num for k in ['3.1', '5.1.9']):
        print(f'[{num}] {title} (len={len(clean_txt)})')
        print(f'    TEXT: {clean_txt[:150].replace(chr(10), " ")}')

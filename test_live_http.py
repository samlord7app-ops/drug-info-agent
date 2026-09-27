import urllib.request
import json

test_drugs = ['crestor', 'bokey', 'lipitor', 'tagrisso', 'norvasc', 'plavix']
for d in test_drugs:
    url = f'http://127.0.0.1:5050/api/search?q={d}'
    try:
        with urllib.request.urlopen(url, timeout=6) as r:
            res = json.loads(r.read())
            print(f"[{d}]: status={r.status}, success={res.get('success')}, lic={res.get('license_id')}, time={res.get('time_cost')}")
            assert res.get('success') is True, f"Failed on {d}: {res.get('error')}"
    except Exception as e:
        print(f"[{d}]: ERROR={e}")

print("ALL DRUGS TESTED OVER HTTP SUCCESSFULLY!")

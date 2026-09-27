from drug_app import app
import json

app.testing = True
client = app.test_client()

drugs_to_test = ["bokey", "lipitor", "tagrisso", "crestor", "norvasc", "plavix"]

for d in drugs_to_test:
    resp = client.get(f'/api/search?q={d}')
    assert resp.status_code == 200, f"Failed on {d}: {resp.status_code}"
    data = json.loads(resp.data.decode('utf-8'))
    print(f"Drug [{d}]: success={data.get('success')}, lic={data.get('license_id')}, time={data.get('time_cost')}")
    assert data.get('success') is True, f"Search failed for {d}: {data.get('error')}"

print("\nALL POPULAR DRUGS VERIFIED SUCCESSFULLY!")

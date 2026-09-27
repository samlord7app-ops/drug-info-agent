import unittest
import json
import time
import sys
from drug_app import app

class TestDrugApp(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app.testing = True
        cls.client = app.test_client()

    def test_homepage(self):
        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 200)
        self.assertIn('衛福部藥品仿單極速智慧查詢系統'.encode('utf-8'), resp.data)
        print("[Pass] Homepage render test OK")

    def test_search_bokey(self):
        t0 = time.time()
        resp = self.client.get('/api/search?q=bokey')
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data.decode('utf-8'))
        self.assertTrue(data.get('success'))
        self.assertEqual(data.get('license_id'), '衛署藥製字第037344號')
        self.assertTrue(len(data.get('indications', '')) > 5)
        print(f"[Pass] Bokey search OK, cost: {(time.time() - t0):.3f}s")

    def test_search_lipitor(self):
        t0 = time.time()
        resp = self.client.get('/api/search?q=lipitor')
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data.decode('utf-8'))
        self.assertTrue(data.get('success'))
        self.assertIn('022886', data.get('license_id'))
        print(f"[Pass] Lipitor search OK, cost: {(time.time() - t0):.3f}s")

    def test_search_tagrisso(self):
        t0 = time.time()
        resp = self.client.get('/api/search?q=tagrisso')
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data.decode('utf-8'))
        self.assertTrue(data.get('success'))
        self.assertIn('026968', data.get('license_id'))
        print(f"[Pass] Tagrisso search OK, cost: {(time.time() - t0):.3f}s")

    def test_download_pdf(self):
        resp = self.client.get('/api/download?lic=衛署藥製字第037344號')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.headers.get('Content-Type'), 'application/pdf')
        self.assertTrue(resp.data.startswith(b'%PDF'))
        print(f"[Pass] PDF download endpoint OK, bytes: {len(resp.data):,}")

    def test_ai_qa(self):
        resp = self.client.post('/api/ask', json={
            "question": "可以跟葡萄柚或酒精一起吃嗎？",
            "drug_info": {
                "cname": "立普妥膜衣錠",
                "precautions": "不建議服用 Lipitor 的病人同時大量飲用葡萄柚汁，避免引發橫紋肌溶解症。",
                "contraindications": "禁止併服酒精，酒精具加成胃損害作用。"
            }
        })
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data.decode('utf-8'))
        self.assertIn("葡萄柚", data.get('answer', ''))
        print("[Pass] AI QA endpoint OK")

if __name__ == '__main__':
    unittest.main()

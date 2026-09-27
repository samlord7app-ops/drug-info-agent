"""
Firebase Cloud Functions (2nd Gen) & Cloud Run Entrypoint
Drug Info Agent - TFDA Package Insert & Clinical QA API
"""
import os
from drug_app import app

# Firebase Functions 2nd gen WSGI integration
try:
    from firebase_functions import https_fn

    @https_fn.on_request(memory=1024, timeout_sec=120)
    def api(req: https_fn.Request) -> https_fn.Response:
        return https_fn.wsgi(app)(req)
except ImportError:
    pass

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5050))
    app.run(host='0.0.0.0', port=port, debug=False)

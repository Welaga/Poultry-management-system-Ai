"""Basic smoke tests for the Poultry Management System.

Run with:
    pytest tests/  (after `pip install pytest httpx`)
or:
    python tests/test_api.py
"""
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_api():
    from app.database import init_db
    init_db()

    from fastapi.testclient import TestClient
    from main import app
    client = TestClient(app)

    # Login
    r = client.post('/api/auth/token',
                    data={'username': 'admin', 'password': 'admin123'})
    assert r.status_code == 200, f"Login failed: {r.text}"
    token = r.json()['access_token']
    H = {'Authorization': f'Bearer {token}'}

    # Verify auth works
    r = client.get('/api/auth/me', headers=H)
    assert r.status_code == 200
    assert r.json()['username'] == 'admin'

    # Dashboard
    r = client.get('/api/dashboard/summary', headers=H)
    assert r.status_code == 200
    data = r.json()
    assert 'total_birds' in data
    assert 'eggs_today' in data

    # Create a batch
    r = client.post('/api/birds/batches', headers=H, json={
        'batch_code': f'TEST-{os.getpid()}',
        'breed': 'Test Breed',
        'bird_type': 'layer',
        'initial_count': 50,
        'arrival_date': '2024-01-01',
        'growth_stage': 'layer',
    })
    assert r.status_code == 200, f"Batch creation failed: {r.text}"
    batch_id = r.json()['id']

    # Record an egg collection
    r = client.post('/api/eggs/collection', headers=H, json={
        'batch_id': batch_id,
        'collection_date': '2024-12-01',
        'total_eggs': 40,
        'broken_eggs': 2,
    })
    assert r.status_code == 200

    # Chatbot
    r = client.post('/api/chat/message', headers=H,
                    json={'message': 'How do I prevent diseases?'})
    assert r.status_code == 200
    assert 'response' in r.json()

    # PDF report
    r = client.get('/api/reports/daily', headers=H)
    assert r.status_code == 200
    assert len(r.content) > 100

    # Pages
    for page in ['/login', '/dashboard', '/birds', '/eggs', '/feed',
                 '/health', '/camera', '/reports', '/files', '/chatbot']:
        r = client.get(page)
        assert r.status_code == 200, f"Page {page} failed: {r.status_code}"

    print("✅ All smoke tests passed")


if __name__ == '__main__':
    test_api()

def test_home():
    from main import app
    client = app.test_client()
    response = client.get('/')
    assert response.status_code == 200
    assert b"Hello from Cloud Run CI/CD pipeline!" in response.data

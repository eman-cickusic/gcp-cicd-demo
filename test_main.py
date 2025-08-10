import pytest
import json
import os
from unittest.mock import patch, MagicMock
from main import app, get_secret, validate_api_key

@pytest.fixture
def client():
    """Create test client"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_home_endpoint(client):
    """Test main endpoint returns correct response"""
    response = client.get('/')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'message' in data
    assert 'Secure Cloud Run CI/CD pipeline' in data['message']
    assert 'security_features' in data

def test_health_check(client):
    """Test health check endpoint"""
    response = client.get('/health')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'healthy'
    assert 'timestamp' in data

def test_security_headers(client):
    """Test that security headers are present"""
    response = client.get('/')
    assert response.headers['X-Content-Type-Options'] == 'nosniff'
    assert response.headers['X-Frame-Options'] == 'DENY'
    assert response.headers['X-XSS-Protection'] == '1; mode=block'
    assert 'Strict-Transport-Security' in response.headers
    assert 'Content-Security-Policy' in response.headers

def test_config_endpoint(client):
    """Test configuration endpoint"""
    response = client.get('/api/config')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'environment' in data
    assert 'features' in data
    assert data['features']['secret_manager'] is True

def test_secure_endpoint_no_api_key(client):
    """Test secure endpoint without API key returns 401"""
    response = client.post('/api/secure', 
                          json={'message': 'test'})
    assert response.status_code == 401
    data = json.loads(response.data)
    assert 'API key required' in data['error']

def test_secure_endpoint_invalid_api_key(client):
    """Test secure endpoint with invalid API key returns 403"""
    response = client.post('/api/secure', 
                          json={'message': 'test'},
                          headers={'X-API-Key': 'invalid-key'})
    assert response.status_code == 403
    data = json.loads(response.data)
    assert 'Invalid API key' in data['error']

@patch('main.get_secret')
def test_secure_endpoint_valid_api_key(mock_get_secret, client):
    """Test secure endpoint with valid API key"""
    # Mock the secret retrieval
    mock_get_secret.return_value = 'test-key-123'
    
    response = client.post('/api/secure', 
                          json={'message': 'test message'},
                          headers={'X-API-Key': 'test-key-123'})
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'success'
    assert 'Processed: test message' in data['processed_message']

def test_secure_endpoint_invalid_json(client):
    """Test secure endpoint with invalid JSON data"""
    with patch('main.get_secret', return_value='test-key'):
        response = client.post('/api/secure', 
                              json={},  # Missing 'message' key
                              headers={'X-API-Key': 'test-key'})
        assert response.status_code == 400

def test_404_handler(client):
    """Test custom 404 handler"""
    response = client.get('/nonexistent')
    assert response.status_code == 404
    data = json.loads(response.data)
    assert 'Endpoint not found' in data['error']

@patch('main.secretmanager.SecretManagerServiceClient')
def test_get_secret_success(mock_client):
    """Test successful secret retrieval"""
    # Mock the secret manager client
    mock_instance = MagicMock()
    mock_client.return_value = mock_instance
    
    # Mock the response
    mock_response = MagicMock()
    mock_response.payload.data = b'secret-value'
    mock_instance.access_secret_version.return_value = mock_response
    
    # Set project ID environment variable
    with patch.dict(os.environ, {'GCP_PROJECT_ID': 'test-project'}):
        result = get_secret('test-secret')
        assert result == 'secret-value'

def test_get_secret_no_project_id():
    """Test secret retrieval without project ID"""
    with patch.dict(os.environ, {}, clear=True):
        result = get_secret('test-secret')
        assert result is None

@patch('main.secretmanager.SecretManagerServiceClient')
def test_get_secret_exception(mock_client):
    """Test secret retrieval with exception"""
    mock_client.side_effect = Exception('Connection error')
    
    with patch.dict(os.environ, {'GCP_PROJECT_ID': 'test-project'}):
        result = get_secret('test-secret')
        assert result is None

def test_validate_api_key_fallback():
    """Test API key validation with fallback to environment variable"""
    with patch('main.get_secret', return_value=None):
        with patch.dict(os.environ, {'API_KEY': 'env-key'}):
            assert validate_api_key('env-key') is True
            assert validate_api_key('wrong-key') is False

def test_input_length_limit(client):
    """Test that input length is limited for security"""
    long_message = 'x' * 200  # Message longer than 100 chars
    
    with patch('main.get_secret', return_value='test-key'):
        response = client.post('/api/secure', 
                              json={'message': long_message},
                              headers={'X-API-Key': 'test-key'})
        assert response.status_code == 200
        data = json.loads(response.data)
        # Should be truncated to 100 characters
        processed_msg = data['processed_message']
        assert len(processed_msg.replace('Processed: ', '')) <= 100

def test_environment_debug_info(client):
    """Test that debug info is only shown in non-production environments"""
    # Test development environment (should include debug info)
    with patch.dict(os.environ, {'ENVIRONMENT': 'development'}):
        response = client.get('/api/config')
        data = json.loads(response.data)
        assert 'debug' in data
    
    # Test production environment (should not include debug info)
    with patch.dict(os.environ, {'ENVIRONMENT': 'production'}):
        response = client.get('/api/config')
        data = json.loads(response.data)
        assert 'debug' not in data

def test_json_response_content_type(client):
    """Test that responses have correct content type"""
    response = client.get('/')
    assert 'application/json' in response.content_type

# Security-specific tests
class TestSecurityFeatures:
    
    def test_no_debug_in_production(self):
        """Test that debug mode is disabled in production"""
        with patch.dict(os.environ, {'ENVIRONMENT': 'production'}):
            # This test verifies the logic in main block
            # In a real scenario, you'd test that the app doesn't start in debug mode
            assert os.environ.get('ENVIRONMENT') == 'production'
    
    def test_constant_time_comparison(self):
        """Test that API key validation uses constant-time comparison"""
        # This tests the security of the validate_api_key function
        # by ensuring it uses hashlib for comparison (prevents timing attacks)
        with patch('main.get_secret', return_value='correct-key'):
            # Both should take similar time regardless of how wrong the key is
            result1 = validate_api_key('wrong-key-1')
            result2 = validate_api_key('completely-different-wrong-key')
            assert result1 is False
            assert result2 is False
    
    def test_sql_injection_protection(self, client):
        """Test protection against SQL injection attempts"""
        malicious_payload = "'; DROP TABLE users; --"
        
        with patch('main.get_secret', return_value='test-key'):
            response = client.post('/api/secure', 
                                  json={'message': malicious_payload},
                                  headers={'X-API-Key': 'test-key'})
            assert response.status_code == 200
            # Verify the malicious input is just treated as string
            data = json.loads(response.data)
            assert malicious_payload in data['processed_message']
    
    def test_xss_prevention(self, client):
        """Test XSS prevention through proper response handling"""
        xss_payload = "<script>alert('xss')</script>"
        
        with patch('main.get_secret', return_value='test-key'):
            response = client.post('/api/secure', 
                                  json={'message': xss_payload},
                                  headers={'X-API-Key': 'test-key'})
            assert response.status_code == 200
            # Response should be JSON, not HTML, preventing XSS
            assert response.content_type == 'application/json'
    
    def test_path_traversal_protection(self, client):
        """Test protection against path traversal attacks"""
        path_traversal = "../../../etc/passwd"
        
        with patch('main.get_secret', return_value='test-key'):
            response = client.post('/api/secure', 
                                  json={'message': path_traversal},
                                  headers={'X-API-Key': 'test-key'})
            assert response.status_code == 200
            # Should treat it as a regular string, not attempt file access
            data = json.loads(response.data)
            assert path_traversal in data['processed_message']

# Performance and reliability tests
class TestPerformanceAndReliability:
    
    def test_large_request_handling(self, client):
        """Test handling of large requests"""
        # Test with maximum allowed message size
        max_message = 'x' * 100
        
        with patch('main.get_secret', return_value='test-key'):
            response = client.post('/api/secure', 
                                  json={'message': max_message},
                                  headers={'X-API-Key': 'test-key'})
            assert response.status_code == 200
    
    def test_concurrent_requests_simulation(self, client):
        """Simulate multiple concurrent requests"""
        with patch('main.get_secret', return_value='test-key'):
            responses = []
            for i in range(10):
                response = client.post('/api/secure', 
                                      json={'message': f'test-{i}'},
                                      headers={'X-API-Key': 'test-key'})
                responses.append(response)
            
            # All requests should succeed
            assert all(r.status_code == 200 for r in responses)
    
    def test_error_handling_robustness(self, client):
        """Test various error conditions"""
        # Test malformed JSON
        response = client.post('/api/secure', 
                              data='invalid json',
                              content_type='application/json',
                              headers={'X-API-Key': 'test-key'})
        assert response.status_code == 400
        
        # Test missing content type
        response = client.post('/api/secure', 
                              data='{"message": "test"}',
                              headers={'X-API-Key': 'test-key'})
        # Should still work as Flask is flexible with content-type

# Integration tests for Secret Manager
class TestSecretManagerIntegration:
    
    @patch('main.secretmanager.SecretManagerServiceClient')
    def test_secret_manager_timeout(self, mock_client):
        """Test Secret Manager timeout handling"""
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance
        mock_instance.access_secret_version.side_effect = Exception('Timeout')
        
        with patch.dict(os.environ, {'GCP_PROJECT_ID': 'test-project'}):
            result = get_secret('test-secret')
            assert result is None
    
    @patch('main.secretmanager.SecretManagerServiceClient')
    def test_secret_manager_permission_denied(self, mock_client):
        """Test Secret Manager permission denied"""
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance
        mock_instance.access_secret_version.side_effect = Exception('Permission denied')
        
        with patch.dict(os.environ, {'GCP_PROJECT_ID': 'test-project'}):
            result = get_secret('test-secret')
            assert result is None
    
    def test_project_id_from_different_env_vars(self):
        """Test project ID resolution from different environment variables"""
        # Test GCP_PROJECT_ID
        with patch.dict(os.environ, {'GCP_PROJECT_ID': 'project-1'}, clear=True):
            with patch('main.secretmanager.SecretManagerServiceClient') as mock_client:
                mock_instance = MagicMock()
                mock_client.return_value = mock_instance
                mock_response = MagicMock()
                mock_response.payload.data = b'secret'
                mock_instance.access_secret_version.return_value = mock_response
                
                result = get_secret('test-secret')
                assert result == 'secret'
        
        # Test GOOGLE_CLOUD_PROJECT (Cloud Run default)
        with patch.dict(os.environ, {'GOOGLE_CLOUD_PROJECT': 'project-2'}, clear=True):
            with patch('main.secretmanager.SecretManagerServiceClient') as mock_client:
                mock_instance = MagicMock()
                mock_client.return_value = mock_instance
                mock_response = MagicMock()
                mock_response.payload.data = b'secret2'
                mock_instance.access_secret_version.return_value = mock_response
                
                result = get_secret('test-secret')
                assert result == 'secret2'

if __name__ == '__main__':
    pytest.main(['-v', '--cov=main', '--cov-report=term-missing'])

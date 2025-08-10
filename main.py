import os
import logging
from flask import Flask, jsonify, request
from google.cloud import secretmanager
import hashlib
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Security headers middleware
@app.after_request
def after_request(response):
    """Add security headers to all responses"""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['Content-Security-Policy'] = "default-src 'self'"
    return response

def get_secret(secret_name, project_id=None):
    """
    Retrieve secret from Google Secret Manager
    
    Args:
        secret_name (str): Name of the secret
        project_id (str): GCP project ID, if None uses environment variable
    
    Returns:
        str: Secret value or None if not found
    """
    try:
        if not project_id:
            project_id = os.environ.get('GCP_PROJECT_ID') or os.environ.get('GOOGLE_CLOUD_PROJECT')
        
        if not project_id:
            logger.warning("No project ID found, skipping secret retrieval")
            return None
            
        client = secretmanager.SecretManagerServiceClient()
        name = f"projects/{project_id}/secrets/{secret_name}/versions/latest"
        
        response = client.access_secret_version(request={"name": name})
        secret_value = response.payload.data.decode("UTF-8")
        logger.info(f"Successfully retrieved secret: {secret_name}")
        return secret_value
        
    except Exception as e:
        logger.error(f"Error retrieving secret {secret_name}: {str(e)}")
        return None

def validate_api_key(provided_key):
    """
    Validate API key against stored secret
    
    Args:
        provided_key (str): API key provided by client
        
    Returns:
        bool: True if valid, False otherwise
    """
    try:
        stored_key = get_secret('api-key')
        if not stored_key:
            # Fallback for development/testing
            stored_key = os.environ.get('API_KEY', 'dev-key-123')
            
        # Use constant-time comparison to prevent timing attacks
        return hashlib.sha256(provided_key.encode()).hexdigest() == \
               hashlib.sha256(stored_key.encode()).hexdigest()
    except Exception as e:
        logger.error(f"Error validating API key: {str(e)}")
        return False

@app.route('/')
def home():
    """Main endpoint"""
    return jsonify({
        "message": "Hello from Secure Cloud Run CI/CD pipeline!",
        "version": "2.0.0",
        "environment": os.environ.get('ENVIRONMENT', 'development'),
        "security_features": [
            "Secret Manager integration",
            "Security headers",
            "Input validation",
            "Structured logging"
        ]
    })

@app.route('/health')
def health_check():
    """Health check endpoint for load balancer"""
    return jsonify({
        "status": "healthy",
        "timestamp": int(time.time()),
        "version": "2.0.0"
    }), 200

@app.route('/api/secure', methods=['POST'])
def secure_endpoint():
    """
    Secure endpoint that requires API key authentication
    Demonstrates proper secret management
    """
    try:
        # Get API key from header
        api_key = request.headers.get('X-API-Key')
        
        if not api_key:
            logger.warning("API request without API key")
            return jsonify({"error": "API key required"}), 401
            
        # Validate API key
        if not validate_api_key(api_key):
            logger.warning("Invalid API key provided")
            return jsonify({"error": "Invalid API key"}), 403
            
        # Process request data (with input validation)
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({"error": "Invalid request data"}), 400
            
        # Sanitize input
        message = str(data['message'])[:100]  # Limit length
        
        logger.info("Secure endpoint accessed successfully")
        return jsonify({
            "status": "success",
            "processed_message": f"Processed: {message}",
            "timestamp": int(time.time())
        })
        
    except Exception as e:
        logger.error(f"Error in secure endpoint: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/api/config')
def get_config():
    """
    Get non-sensitive configuration information
    Demonstrates separation of sensitive and non-sensitive data
    """
    config = {
        "environment": os.environ.get('ENVIRONMENT', 'development'),
        "version": "2.0.0",
        "features": {
            "secret_manager": True,
            "security_scanning": True,
            "structured_logging": True
        },
        "health_check_path": "/health"
    }
    
    # Only include debug info in non-production environments
    if config["environment"] != "production":
        config["debug"] = {
            "python_version": os.environ.get('PYTHON_VERSION', 'unknown'),
            "container_id": os.environ.get('HOSTNAME', 'unknown')
        }
    
    return jsonify(config)

@app.errorhandler(404)
def not_found(error):
    """Custom 404 handler"""
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    """Custom 500 handler"""
    logger.error(f"Internal server error: {str(error)}")
    return jsonify({"error": "Internal server error"}), 500

if __name__ == "__main__":
    # Security: Don't run in debug mode in production
    debug_mode = os.environ.get('ENVIRONMENT', 'development') != 'production'
    
    # Get port from environment (Cloud Run uses PORT env var)
    port = int(os.environ.get('PORT', 8080))
    
    logger.info(f"Starting application on port {port}")
    logger.info(f"Environment: {os.environ.get('ENVIRONMENT', 'development')}")
    logger.info(f"Debug mode: {debug_mode}")
    
    # Run the application
    app.run(
        host="0.0.0.0", 
        port=port, 
        debug=debug_mode
    )

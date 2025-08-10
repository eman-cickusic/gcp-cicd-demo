## GCP CI/CD DEMO

### **Security Integration Achievements**
- **✅ Integrated automated security scanning into CI/CD pipeline** using Trivy, Snyk, and Bandit to detect vulnerabilities in Docker images and application code, preventing insecure deployments
- **✅ Implemented security gates** in GitHub Actions that automatically block pull requests if critical vulnerabilities are found, enforcing security standards
- **✅ Strengthened application security by migrating secrets** from hardcoded values to Google Secret Manager, eliminating credential exposure in codebase
- **✅ Established comprehensive SAST (Static Application Security Testing)** with multiple tools including Bandit for Python security issues and Snyk for dependency vulnerabilities
- **✅ Built container security scanning** with Trivy integration that blocks deployment of images with critical CVEs
- **✅ Implemented secure coding practices** including input validation, security headers, and non-root container execution

### **DevSecOps Pipeline Features**
- **Multi-stage security scanning**: Code → Dependencies → Container → Deployment
- **Automated security reporting**: Detailed vulnerability reports with severity classification
- **Policy-based deployment gates**: Configurable thresholds for different vulnerability levels
- **Secret detection**: Automated scanning for hardcoded credentials and API keys
- **Compliance ready**: Security scan results formatted for audit and compliance reporting

### **Technical Skills Demonstrated**
- **Google Cloud Platform**: Cloud Run, Secret Manager, Artifact Registry, IAM, Logging
- **Infrastructure as Code**: Terraform with security best practices and compliance
- **CI/CD Security**: GitHub Actions with integrated security toolchain
- **Container Security**: Multi-stage Docker builds, vulnerability scanning, non-root execution
- **Application Security**: Flask security hardening, OWASP best practices, secure API design
- **Monitoring & Observability**: Structured logging, security event monitoring, alerting## Security Scanning Results

The pipeline includes multiple security gates:

### Static Code Analysis
- **Bandit**: Scans for common Python security issues
- **Snyk**: Checks dependencies for known vulnerabilities
- **Results**: Pipeline fails on HIGH or CRITICAL findings

### Container Security
- **Trivy**: Comprehensive container vulnerability scanning
- **Policy**: Blocks deployment if critical CVEs found
- **Reporting**: Detailed vulnerability reports in GitHub Actions

### Secret Detection
- **Automated scanning**: Prevents hardcoded secrets from being committed
- **Secret Manager Integration**: Secure secret retrieval at runtime### Local Security Testing

```bash
# Run Trivy scan on built image
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
  -v $HOME/.cache:/root/.cache aquasec/trivy:latest image gcp-cicd-demo

# Run Bandit security scan
bandit -r . -ll -f json
```### 5. Create Sample Secret in Secret Manager

Create a sample API key in Secret Manager to demonstrate secure secrets handling:

```bash
# Create a sample API key secret
echo "your-api-key-here" | gcloud secrets create api-key --data-file=-
```# GCP DevSecOps CI/CD Demo

A complete demonstration of secure CI/CD pipeline with integrated security scanning using Google Cloud Platform services including Cloud Run, Artifact Registry, Secret Manager, and GitHub Actions with automated vulnerability detection.

## Overview

This project showcases a modern DevSecOps workflow that automatically builds, tests, scans for security vulnerabilities, and deploys a Flask application to Google Cloud Run. The pipeline includes multiple security gates that prevent insecure code and container images from being deployed to production. The infrastructure is managed using Terraform, and the deployment pipeline is handled by GitHub Actions.

## Architecture

- **Application**: Flask web application with secure secrets management
- **Container Registry**: Google Artifact Registry
- **Deployment Platform**: Google Cloud Run
- **CI/CD**: GitHub Actions with integrated security scanning
- **Infrastructure as Code**: Terraform
- **Testing**: pytest for unit tests
- **Security Scanning**: 
  - **Trivy**: Container vulnerability scanning
  - **Snyk**: Static Application Security Testing (SAST)
  - **Bandit**: Python security linter
- **Secrets Management**: Google Secret Manager

## Prerequisites

Before getting started, ensure you have:

- Google Cloud Platform account with billing enabled
- GitHub repository for this code
- `gcloud` CLI installed and configured
- Terraform installed (v1.0+)
- Docker installed locally (for testing)
- Snyk account (free tier available) and API token

## Project Structure

```
gcp-cicd-demo/
├── .github/
│   └── workflows/
│       ├── deploy.yml          # Main CI/CD workflow with security scanning
│       └── security-scan.yml   # Dedicated security scanning for PRs
├── terraform/
│   ├── main.tf                 # Main Terraform configuration
│   ├── variables.tf            # Variable definitions
│   └── outputs.tf              # Output definitions
├── security/
│   ├── .trivyignore           # Trivy vulnerability ignore rules
│   └── bandit.yaml            # Bandit security scanning config
├── main.py                     # Flask application with secure secrets
├── requirements.txt            # Python dependencies
├── Dockerfile                  # Multi-stage secure container build
├── test_main.py               # Unit tests
└── README.md                  # This file
```

## Setup Instructions

### 1. Infrastructure Setup with Terraform

First, set up the Google Cloud infrastructure:

```bash
# Navigate to terraform directory
cd terraform

# Initialize Terraform
terraform init

# Plan the infrastructure changes
terraform plan -var="project_id=YOUR_GCP_PROJECT_ID" -var="project_number=YOUR_GCP_PROJECT_NUMBER"

# Apply the changes
terraform apply -var="project_id=YOUR_GCP_PROJECT_ID" -var="project_number=YOUR_GCP_PROJECT_NUMBER"
```

This will create:
- Artifact Registry repository for Docker images
- Service account for GitHub Actions with security permissions
- Google Secret Manager for secure credential storage
- Proper IAM roles and permissions including Secret Manager access
- Cloud Run service configuration with security best practices

### 2. Service Account Key Generation

After Terraform creates the infrastructure, generate a service account key:

```bash
# Create and download service account key
gcloud iam service-accounts keys create github-actions-key.json \
  --iam-account=github-actions-deployer@YOUR_PROJECT_ID.iam.gserviceaccount.com
```

### 3. GitHub Secrets Configuration

In your GitHub repository, go to Settings → Secrets and variables → Actions, and add these repository secrets:

- `GCP_SA_KEY`: Contents of the `github-actions-key.json` file
- `GCP_PROJECT_ID`: Your Google Cloud Project ID
- `SNYK_TOKEN`: Your Snyk API token for security scanning

### 4. Enable Required APIs

Make sure these Google Cloud APIs are enabled in your project:

```bash
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable artifactregistry.googleapis.com
gcloud services enable secretmanager.googleapis.com
```

## How It Works

### DevSecOps Pipeline Flow

1. **Trigger**: Push to main branch or pull request creation
2. **Checkout**: Code is checked out from repository
3. **Security Gates**:
   - **Static Code Analysis**: Bandit scans Python code for security issues
   - **Dependency Vulnerability Scan**: Snyk checks for vulnerable dependencies
   - **Secret Detection**: Automated scan for hardcoded secrets
4. **Testing**: Python dependencies are installed and unit tests are run
5. **Docker Build**: Multi-stage secure container build
6. **Container Security Scan**: Trivy scans the built image for vulnerabilities
7. **Security Gate**: Pipeline fails if critical vulnerabilities are found
8. **Push to Registry**: Only secure images are pushed to Artifact Registry
9. **Deploy**: Secure deployment to Cloud Run with Secret Manager integration

### Security Features

**Static Application Security Testing (SAST)**:
- Bandit analyzes Python code for common security issues
- Snyk performs dependency vulnerability scanning
- Custom security rules and policies enforcement

**Container Security**:
- Trivy scans Docker images for OS and application vulnerabilities
- Multi-stage builds to minimize attack surface
- Non-root user execution
- Minimal base images

**Secrets Management**:
- Google Secret Manager integration
- No hardcoded API keys or credentials
- Secure secret injection at runtime

### Application Details

The Flask application (`main.py`) demonstrates secure coding practices:
- Integrates with Google Secret Manager for API keys
- Runs on port 8080 (Cloud Run standard)
- Implements security headers and best practices
- Includes comprehensive unit tests including security test cases

### Container Configuration

The `Dockerfile` creates a secure, multi-stage container that:
- Uses minimal Python 3.10 slim base image
- Implements multi-stage build to reduce attack surface
- Runs as non-root user for enhanced security
- Installs only necessary dependencies
- Implements security scanning during build process

## Local Development

### Running Locally

```bash
# Install dependencies including security tools
pip install -r requirements.txt bandit

# Run security scan on code
bandit -r . -f json -o bandit-report.json

# Run the application
python main.py

# Access the application
curl http://localhost:8080
```

### Running Tests

```bash
# Install test and security dependencies
pip install pytest bandit

# Run security tests
bandit -r . -ll

# Run unit tests
pytest test_main.py -v
```

### Local Docker Testing

```bash
# Build the image
docker build -t gcp-cicd-demo .

# Run the container
docker run -p 8080:8080 gcp-cicd-demo

# Test the application
curl http://localhost:8080
```

## Deployment

### Automatic Deployment

Simply push your changes to the main branch:

```bash
git add .
git commit -m "Your commit message"
git push origin main
```

The GitHub Actions workflow will automatically:
- Run comprehensive security scans (SAST, dependency check, container scan)
- Block deployment if critical vulnerabilities are found
- Run tests
- Build and push the Docker image (only if security checks pass)
- Deploy to Cloud Run with secure configuration
- Make the application publicly accessible

### Manual Deployment

If you need to deploy manually:

```bash
# Authenticate with Google Cloud
gcloud auth login

# Build and push image
docker build -t us-central1-docker.pkg.dev/YOUR_PROJECT_ID/my-repo/my-app:latest .
docker push us-central1-docker.pkg.dev/YOUR_PROJECT_ID/my-repo/my-app:latest

# Deploy to Cloud Run
gcloud run deploy my-app \
  --image=us-central1-docker.pkg.dev/YOUR_PROJECT_ID/my-repo/my-app:latest \
  --platform=managed \
  --region=us-central1 \
  --allow-unauthenticated
```

## Monitoring and Logs

- **Cloud Run Console**: Monitor service health, traffic, and performance
- **Cloud Logging**: View application and system logs
- **GitHub Actions**: Monitor build, security scan results, and deployment status
- **Security Dashboard**: Track vulnerability trends and security posture

## Security Considerations

- **Zero Trust Architecture**: No hardcoded credentials or secrets
- **Least Privilege**: Service accounts follow principle of least privilege
- **Container Security**: Multi-stage builds and non-root execution
- **Automated Security**: Continuous vulnerability scanning and monitoring
- **Secret Management**: Google Secret Manager integration
- **Network Security**: Cloud Run VPC configuration options
- **Compliance**: Security scanning results can be used for compliance reporting

## Cost Optimization

This setup is designed to be cost-effective:
- Cloud Run only charges for actual usage (pay-per-request)
- Artifact Registry has generous free tier
- GitHub Actions provides free CI/CD minutes for public repositories

## Troubleshooting

### Common Issues

1. **Security Scan Failures**: Check security scan results in GitHub Actions logs
2. **Authentication Errors**: Verify service account key is correctly added to GitHub Secrets
3. **Permission Denied**: Ensure all required IAM roles including Secret Manager access are assigned
4. **Build Failures**: Check GitHub Actions logs for specific error details
5. **Deployment Issues**: Verify Cloud Run service configuration and image registry path
6. **Secret Access Issues**: Verify Secret Manager permissions and secret existence

### Useful Commands

```bash
# Check Cloud Run services
gcloud run services list

# View service logs
gcloud logging read "resource.type=cloud_run_revision" --limit 50

# Check secrets in Secret Manager
gcloud secrets list

# Test deployed service
curl $(gcloud run services describe my-app --region=us-central1 --format='value(status.url)')

# Run local security scan
bandit -r . -ll
trivy fs .
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

- Adding compliance reporting and audit trails
- Integrating with security information and event management (SIEM) systems
- Implementing infrastructure security scanning with tools like Checkov

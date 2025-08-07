# GCP CI/CD Demo

A complete demonstration of CI/CD pipeline using Google Cloud Platform services including Cloud Run, Artifact Registry, and GitHub Actions.

## Overview

This project showcases a DevOps workflow that automatically builds, tests, and deploys a Flask application to Google Cloud Run whenever code is pushed to the main branch. The infrastructure is managed using Terraform, and the deployment pipeline is handled by GitHub Actions.

## Architecture

- **Application**: Simple Flask web application
- **Container Registry**: Google Artifact Registry
- **Deployment Platform**: Google Cloud Run
- **CI/CD**: GitHub Actions
- **Infrastructure as Code**: Terraform
- **Testing**: pytest for unit tests

## Prerequisites

Before getting started, ensure you have:

- Google Cloud Platform account with billing enabled
- GitHub repository for this code
- `gcloud` CLI installed and configured
- Terraform installed (v1.0+)
- Docker installed locally (for testing)

## Project Structure

```
gcp-cicd-demo/
├── .github/
│   └── workflows/
│       └── deploy.yml          # GitHub Actions workflow
├── terraform/
│   ├── main.tf                 # Main Terraform configuration
│   ├── variables.tf            # Variable definitions
│   └── outputs.tf              # Output definitions
├── main.py                     # Flask application
├── requirements.txt            # Python dependencies
├── Dockerfile                  # Container configuration
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
- Service account for GitHub Actions
- Proper IAM roles and permissions
- Cloud Run service configuration

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

### 4. Enable Required APIs

Make sure these Google Cloud APIs are enabled in your project:

```bash
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable artifactregistry.googleapis.com
```

## How It Works

### CI/CD Pipeline Flow

1. **Trigger**: Push to main branch triggers GitHub Actions workflow
2. **Checkout**: Code is checked out from repository
3. **Authentication**: GitHub Actions authenticates with Google Cloud using service account
4. **Testing**: Python dependencies are installed and unit tests are run with pytest
5. **Docker Build**: Application is containerized using the provided Dockerfile
6. **Push to Registry**: Container image is pushed to Google Artifact Registry
7. **Deploy**: Application is deployed to Cloud Run with zero downtime

### Application Details

The Flask application (`main.py`) is a minimal web server that:
- Runs on port 8080 (Cloud Run standard)
- Serves a simple "Hello from Cloud Run CI/CD pipeline!" message
- Includes basic unit tests to validate functionality

### Container Configuration

The `Dockerfile` creates an optimized container that:
- Uses Python 3.10 slim base image
- Installs only necessary dependencies
- Runs the application on all network interfaces

## Local Development

### Running Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
python main.py

# Access the application
curl http://localhost:8080
```

### Running Tests

```bash
# Install test dependencies
pip install pytest

# Run tests
pytest test_main.py
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
- Run tests
- Build and push the Docker image
- Deploy to Cloud Run
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
- **GitHub Actions**: Monitor build and deployment status

## Security Considerations

- Service account follows principle of least privilege
- Container runs as non-root user
- Cloud Run service can be configured for authentication if needed
- Secrets are stored securely in GitHub Secrets

## Cost Optimization

This setup is designed to be cost-effective:
- Cloud Run only charges for actual usage (pay-per-request)
- Artifact Registry has generous free tier
- GitHub Actions provides free CI/CD minutes for public repositories

## Troubleshooting

### Common Issues

1. **Authentication Errors**: Verify service account key is correctly added to GitHub Secrets
2. **Permission Denied**: Ensure all required IAM roles are assigned via Terraform
3. **Build Failures**: Check GitHub Actions logs for specific error details
4. **Deployment Issues**: Verify Cloud Run service configuration and image registry path

### Useful Commands

```bash
# Check Cloud Run services
gcloud run services list

# View service logs
gcloud logging read "resource.type=cloud_run_revision" --limit 50

# Test deployed service
curl $(gcloud run services describe my-app --region=us-central1 --format='value(status.url)')
```

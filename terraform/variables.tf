variable "project_id" {
  type        = string
  description = "GCP Project ID"
  
  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{4,28}[a-z0-9]$", var.project_id))
    error_message = "Project ID must be a valid GCP project ID."
  }
}

variable "project_number" {
  type        = string
  description = "GCP Project Number"
  
  validation {
    condition     = can(regex("^[0-9]+$", var.project_number))
    error_message = "Project number must be numeric."
  }
}

variable "region" {
  type        = string
  default     = "us-central1"
  description = "GCP region for resources"
  
  validation {
    condition = contains([
      "us-central1",
      "us-east1", 
      "us-west1",
      "europe-west1",
      "asia-east1"
    ], var.region)
    error_message = "Region must be a valid GCP region."
  }
}

variable "api_key_value" {
  type        = string
  description = "API key value to store in Secret Manager"
  sensitive   = true
  default     = "change-me-in-production"
  
  validation {
    condition     = length(var.api_key_value) >= 16
    error_message = "API key must be at least 16 characters long."
  }
}

variable "environment" {
  type        = string
  description = "Environment name (dev, staging, production)"
  default     = "production"
  
  validation {
    condition     = contains(["dev", "staging", "production"], var.environment)
    error_message = "Environment must be one of: dev, staging, production."
  }
}

variable "enable_monitoring" {
  type        = bool
  description = "Enable Cloud Monitoring alerts"
  default     = true
}

variable "log_retention_days" {
  type        = number
  description = "Number of days to retain security logs"
  default     = 90
  
  validation {
    condition     = var.log_retention_days >= 30 && var.log_retention_days <= 3653
    error_message = "Log retention must be between 30 and 3653 days."
  }
}

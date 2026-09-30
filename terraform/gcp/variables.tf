variable "project_id" {
  description = "The ID of the GCP project to deploy resources to."
  type        = string
}

variable "region" {
  description = "The target deployment region."
  type        = string
  default     = "us-central1"
}

variable "db_password" {
  description = "Password for the database root/application user."
  type        = string
  sensitive   = true
}

variable "firebase_api_key" {
  description = "The Firebase Web API Key for authentication flow (Identity Toolkit)."
  type        = string
  default     = ""
}

variable "environment" {
  description = "Deployment environment name (e.g. production, development)."
  type        = string
  default     = "production"
}

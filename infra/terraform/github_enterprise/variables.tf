# GitHub Enterprise Terraform Variables

variable "github_token" {
  description = "GitHub personal access token with repo and admin:org permissions"
  type        = string
  sensitive   = true
}

variable "github_organization" {
  description = "GitHub organization or username"
  type        = string
  default     = "Oluseyi-Kofoworola"
}

variable "azure_credentials" {
  description = "Azure service principal credentials (JSON)"
  type        = string
  sensitive   = true
  default     = ""
}

variable "codecov_token" {
  description = "Codecov upload token for coverage reports"
  type        = string
  sensitive   = true
  default     = ""
}

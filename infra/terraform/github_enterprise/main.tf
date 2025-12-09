# GitHub Enterprise Configuration for Healthcare GitOps
# Manages repository settings, branch protection, secrets, and team access

terraform {
  required_version = ">= 1.5.0"
  
  required_providers {
    github = {
      source  = "integrations/github"
      version = "~> 5.0"
    }
  }
}

provider "github" {
  token = var.github_token
  owner = var.github_organization
}

# Repository configuration
resource "github_repository" "gitops_healthcare" {
  name        = "gitops2-healthcare-intelligence-git-commit"
  description = "AI-powered compliance automation for healthcare software - HIPAA/FDA/SOX GitOps intelligence"
  
  visibility = "public"  # or "private" for enterprise
  
  has_issues      = true
  has_projects    = true
  has_wiki        = false
  has_downloads   = true
  
  allow_merge_commit     = true
  allow_squash_merge     = true
  allow_rebase_merge     = false
  delete_branch_on_merge = true
  
  vulnerability_alerts = true
  
  topics = [
    "gitops",
    "healthcare",
    "hipaa",
    "compliance",
    "ai-readiness",
    "git-forensics"
  ]
}

# Branch protection for main
resource "github_branch_protection" "main" {
  repository_id = github_repository.gitops_healthcare.node_id
  pattern       = "main"
  
  required_status_checks {
    strict   = true
    contexts = [
      "build",
      "validate-python",
      "validate-docs",
      "ai-readiness-scan"
    ]
  }
  
  required_pull_request_reviews {
    dismiss_stale_reviews           = true
    require_code_owner_reviews      = true
    required_approving_review_count = 2  # Dual approval for production
    restrict_dismissals             = true
  }
  
  enforce_admins = true
  
  required_linear_history = true
  
  allows_deletions    = false
  allows_force_pushes = false
}

# CODEOWNERS file integration
resource "github_repository_file" "codeowners" {
  repository = github_repository.gitops_healthcare.name
  branch     = "main"
  file       = ".github/CODEOWNERS"
  
  content = <<-EOT
    # Healthcare GitOps Code Owners
    
    # Default owners for everything
    * @gitops-team
    
    # EHR / PHI services
    /services/ehr-auth-service/ @ehr-team @security-team
    /services/phi-service/ @phi-team @security-team @compliance-team
    
    # Payment gateway (PCI compliance)
    /services/payment-gateway/ @payments-team @security-team
    
    # Medical devices (FDA compliance)
    /services/medical-device/ @device-team @regulatory-team
    
    # Infrastructure & policies
    /infra/ @platform-team
    /policies/ @compliance-team @security-team
    /.ai/ @ai-governance-team
    
    # Documentation
    /docs/ @documentation-team
    /executive/ @leadership-team
  EOT
  
  commit_message      = "feat(governance): add CODEOWNERS for healthcare teams"
  commit_author       = "Terraform"
  commit_email        = "terraform@example.com"
  overwrite_on_create = true
}

# Repository secrets for CI/CD
resource "github_actions_secret" "azure_credentials" {
  repository      = github_repository.gitops_healthcare.name
  secret_name     = "AZURE_CREDENTIALS"
  plaintext_value = var.azure_credentials
}

resource "github_actions_secret" "codecov_token" {
  repository      = github_repository.gitops_healthcare.name
  secret_name     = "CODECOV_TOKEN"
  plaintext_value = var.codecov_token
}

# Enable Dependabot security updates
resource "github_repository_dependabot_security_updates" "gitops_healthcare" {
  repository = github_repository.gitops_healthcare.name
  enabled    = true
}

# Output repository URL
output "repository_url" {
  value       = github_repository.gitops_healthcare.html_url
  description = "URL of the GitHub repository"
}

output "repository_ssh_url" {
  value       = github_repository.gitops_healthcare.ssh_clone_url
  description = "SSH clone URL"
}

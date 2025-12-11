# 🔒 Security Guide: API Key Management

**CRITICAL**: This guide explains how to securely manage your OpenAI API key for GitOps 2.0 features.

---

## 🚨 Security Rules

### ❌ NEVER DO THIS:
```bash
# DON'T hardcode API keys in code
OPENAI_API_KEY = "sk-proj-..."

# DON'T commit .env files
git add .env  # WRONG!

# DON'T share API keys in chat/email/docs
export OPENAI_API_KEY="sk-proj-..."  # WRONG!
```

### ✅ ALWAYS DO THIS:
```bash
# Use environment variables
export OPENAI_API_KEY="your-key-here"

# Use .env files (NOT committed to git)
cp .env.example .env
# Edit .env with your actual keys

# Use secret management systems in production
# - GitHub Secrets
# - Azure Key Vault
# - HashiCorp Vault
```

---

## 📋 Quick Setup Guide

### Step 1: Get Your API Key
1. Visit: https://platform.openai.com/api-keys
2. Create a new API key
3. **Copy it immediately** (you won't see it again)

### Step 2: Set Environment Variable (Development)

#### macOS/Linux:
```bash
# Add to ~/.zshrc or ~/.bashrc
export OPENAI_API_KEY="sk-proj-your-actual-key-here"

# Reload shell
source ~/.zshrc
```

#### Windows:
```powershell
# PowerShell
$env:OPENAI_API_KEY = "sk-proj-your-actual-key-here"

# Or use System Environment Variables (persistent)
setx OPENAI_API_KEY "sk-proj-your-actual-key-here"
```

### Step 3: Verify Setup
```bash
# Should output: sk-proj-...
echo $OPENAI_API_KEY

# Test the AI features
python tools/git_copilot_commit.py --analyze
```

---

## 🏢 Production Setup

### GitHub Actions (CI/CD)
```yaml
# .github/workflows/risk-adaptive-cicd.yml
jobs:
  ai-commit-analysis:
    steps:
      - name: AI Commit Generation
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
        run: python tools/git_copilot_commit.py --analyze
```

**Setup GitHub Secret**:
1. Go to: Repository → Settings → Secrets and variables → Actions
2. Click "New repository secret"
3. Name: `OPENAI_API_KEY`
4. Value: Your OpenAI API key
5. Click "Add secret"

### Azure Key Vault (Recommended for Production)
```bash
# Store secret in Azure Key Vault
az keyvault secret set \
  --vault-name "gitops-healthcare-kv" \
  --name "OpenAI-API-Key" \
  --value "sk-proj-your-key-here"

# Retrieve in application
az keyvault secret show \
  --vault-name "gitops-healthcare-kv" \
  --name "OpenAI-API-Key" \
  --query "value" -o tsv
```

### Docker/Kubernetes
```yaml
# kubernetes/secrets.yaml
apiVersion: v1
kind: Secret
metadata:
  name: openai-credentials
type: Opaque
stringData:
  api-key: sk-proj-your-key-here

---
# kubernetes/deployment.yaml
apiVersion: apps/v1
kind: Deployment
spec:
  template:
    spec:
      containers:
      - name: ai-commit-generator
        env:
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: openai-credentials
              key: api-key
```

---

## 🔐 Secret Rotation

### When to Rotate:
- **Every 90 days** (recommended)
- **Immediately if exposed** (committed to git, shared in chat, etc.)
- **After team member departure**
- **After security incident**

### How to Rotate:
```bash
# 1. Generate new API key at OpenAI
# https://platform.openai.com/api-keys

# 2. Update environment variable
export OPENAI_API_KEY="sk-proj-NEW-key-here"

# 3. Update all production secrets
# - GitHub Secrets
# - Azure Key Vault
# - Kubernetes Secrets

# 4. Delete old API key at OpenAI
# (Prevents accidental use)

# 5. Verify new key works
python tools/git_copilot_commit.py --analyze
```

---

## 🚑 Emergency: API Key Exposed

### If You Accidentally Committed Your API Key:

#### Step 1: Revoke Immediately
1. Go to: https://platform.openai.com/api-keys
2. Find the exposed key
3. Click "Revoke" or "Delete"
4. Generate a new key

#### Step 2: Remove from Git History
```bash
# Using BFG Repo-Cleaner (recommended)
brew install bfg  # macOS
# Download BFG: https://rtyley.github.io/bfg-repo-cleaner/

# Remove the exposed key from all history
bfg --replace-text <(echo "sk-proj-EXPOSED-KEY-HERE==>REDACTED")

# Clean up
git reflog expire --expire=now --all
git gc --prune=now --aggressive

# Force push (coordinate with team!)
git push origin --force --all
git push origin --force --tags
```

#### Step 3: Notify Team
- Send team-wide notification
- Ensure everyone pulls latest changes
- Update all environment variables

#### Step 4: Check for Unauthorized Usage
1. Go to: https://platform.openai.com/usage
2. Review API usage for suspicious activity
3. Check billing for unexpected charges

---

## 🔍 Monitoring & Auditing

### Track API Usage
```bash
# Check your OpenAI usage
# Visit: https://platform.openai.com/usage

# Set up billing alerts
# Settings → Billing → Usage limits
```

### Audit Access
```bash
# Log all API calls (for compliance)
# Add to your application logging:

import logging
logging.info(f"OpenAI API call: model={model}, user={user_id}, timestamp={timestamp}")
```

---

## 📚 Best Practices Summary

✅ **DO**:
- Use environment variables for API keys
- Store secrets in secure secret management systems
- Rotate API keys every 90 days
- Set up billing alerts
- Use least-privilege access (separate keys per environment)
- Add `.env` to `.gitignore`
- Use `.env.example` for documentation
- Monitor API usage regularly

❌ **DON'T**:
- Hardcode API keys in source code
- Commit `.env` files to git
- Share API keys in chat/email/docs
- Use production keys in development
- Store keys in plain text files
- Reuse keys across multiple projects
- Share keys with unauthorized users

---

## 🆘 Support

### Security Questions:
- Email: security@your-org.com
- Slack: #security-team

### OpenAI Support:
- Help: https://help.openai.com/
- Status: https://status.openai.com/

### Emergency Contacts:
- Security Incident Response: +1-XXX-XXX-XXXX
- On-Call Engineer: Pagerduty

---

## 📖 References

- [OpenAI Best Practices](https://platform.openai.com/docs/guides/safety-best-practices)
- [GitHub Encrypted Secrets](https://docs.github.com/en/actions/security-guides/encrypted-secrets)
- [Azure Key Vault](https://learn.microsoft.com/en-us/azure/key-vault/)
- [OWASP API Security](https://owasp.org/www-project-api-security/)
- [Secret Rotation Guide](docs/SECRET_ROTATION.md)

---

**Last Updated**: December 10, 2025  
**Version**: 1.0.0  
**Status**: ✅ Production Ready

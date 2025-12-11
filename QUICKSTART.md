# GitOps 2.0 Healthcare Intelligence - Quick Start

**5-Minute Setup Guide** | [Full Documentation](docs/README.md) | [API Reference](docs/API.md)

---

## 🚀 Get Started in 3 Steps

### Step 1: Setup (2 minutes)
```bash
# Clone and setup
git clone <repo-url>
cd gitops2-healthcare-intelligence-git-commit
./setup.sh

# Set OpenAI API Key (required for AI features)
export OPENAI_API_KEY="sk-..."
```

### Step 2: Generate AI-Powered Commit (1 minute)
```bash
# Make code changes
echo "// New feature" >> services/phi-service/main.go
git add .

# Generate compliant commit message
python tools/git_copilot_commit.py --analyze --scope phi
```

### Step 3: Run Incident Response (2 minutes)
```bash
# Find root cause of performance regression
python tools/git_intelligent_bisect.py \
  --metric workload_latency \
  --threshold 500
```

---

## 📚 Key Features

| Feature | Tool | Impact |
|---------|------|--------|
| **AI Commit Generation** | `git_copilot_commit.py` | 15min → 30sec (-97%) |
| **Risk-Adaptive CI/CD** | `.github/workflows/risk-adaptive-cicd.yml` | Auto-scaling pipelines |
| **AI Incident Response** | `git_intelligent_bisect.py` | 16h → 2.7h MTTR (-80%) |

---

## 🔗 Next Steps

- **Full Walkthrough**: See [docs/GETTING_STARTED.md](docs/GETTING_STARTED.md)
- **Architecture**: See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- **Security**: See [SECURITY.md](SECURITY.md)
- **Contributing**: See [CONTRIBUTING.md](CONTRIBUTING.md)

---

## ⚠️ Important

- **Never commit API keys** - Use environment variables
- **Review generated commits** before pushing
- **Test in non-production** first

---

**Need Help?** Check [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) or open an issue.

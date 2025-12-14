# Migration Guide - Deprecated Tools
**Date**: December 14, 2025  
**Version**: 2.0.0

---

## Overview

As part of our enterprise refactoring initiative, we've consolidated duplicate implementations and deprecated legacy tools. This guide helps you migrate to the new, centralized implementations.

---

## 🔄 Deprecated Tools

### 1. `tools/intelligent_bisect.py` → `tools/git_intelligent_bisect.py`

**Status**: ❌ **DEPRECATED**  
**Replacement**: ✅ `tools/git_intelligent_bisect.py`  
**Action Required**: Update imports and scripts

#### Migration Steps

**Before** (Old):
```bash
# Old command
python tools/intelligent_bisect.py \
  --metric error_rate \
  --threshold 5 \
  --good HEAD~10 \
  --bad HEAD
```

**After** (New):
```bash
# New command
python tools/git_intelligent_bisect.py \
  --metric error_rate \
  --threshold 5 \
  --good HEAD~10 \
  --bad HEAD
```

#### Differences
- ✅ **AI-powered analysis** - Uses OpenAI for commit risk scoring
- ✅ **Better error handling** - Specific exception types
- ✅ **Healthcare-aware** - Understands HIPAA, FDA, SOX compliance
- ✅ **Richer reports** - JSON + Markdown output with recommendations

#### Code Changes

**Python imports**:
```python
# Before
from intelligent_bisect import AIIncidentResponse

# After
from git_intelligent_bisect import AIIncidentResponse
```

**Shell scripts**:
```bash
# Before
BISECT_TOOL="tools/intelligent_bisect.py"

# After
BISECT_TOOL="tools/git_intelligent_bisect.py"
```

---

### 2. `tools/healthcare_commit_generator.py` → `tools/git_copilot_commit.py`

**Status**: ❌ **DEPRECATED**  
**Replacement**: ✅ `tools/git_copilot_commit.py`  
**Action Required**: Update imports and workflows

#### Migration Steps

**Before** (Old):
```bash
# Old command
python tools/healthcare_commit_generator.py \
  --analyze \
  --scope phi
```

**After** (New):
```bash
# New command
python tools/git_copilot_commit.py \
  --analyze \
  --scope phi \
  --compliance HIPAA
```

#### Key Improvements
- ✅ **Centralized config** - Uses `tools/config.py`
- ✅ **Better validation** - Pydantic V2 models
- ✅ **Retry logic** - Exponential backoff for API calls
- ✅ **Specific errors** - 10+ exception types
- ✅ **Type safety** - Full type hints

#### Code Changes

**Python imports**:
```python
# Before
from healthcare_commit_generator import HealthcareCommitGenerator

# After
from git_copilot_commit import GitCopilotCommit
```

**API Changes**:
```python
# Before
generator = HealthcareCommitGenerator(api_key="...")
message = generator.generate(scope="phi")

# After
from config import get_config

config = get_config()
generator = GitCopilotCommit(
    api_key=config.openai.api_key.get_secret_value(),
    model=config.openai.model
)
files, diff = generator.get_git_diff()
message = generator.generate_commit_message(
    files=files,
    diff_text=diff,
    scope="phi",
    compliance_hint="HIPAA"
)
```

---

### 3. `tools/gitops_health/` → `src/gitops_ai/`

**Status**: ⚠️ **LEGACY** (maintained for backward compatibility)  
**Replacement**: ✅ `src/gitops_ai/`  
**Action Required**: Migrate to new package structure

#### Migration Steps

**Before** (Old):
```python
from gitops_health.cli import main as gitops_health_main
from gitops_health.risk import RiskScorer
from gitops_health.compliance import ComplianceChecker
```

**After** (New):
```python
from gitops_ai.policy.cli import main as policy_main
from gitops_ai.readiness.cli import main as readiness_main
from gitops_ai.forensics.cli import main as forensics_main
```

#### New Package Structure
```
src/gitops_ai/
├── __init__.py
├── cli.py                  # Main CLI entry point
├── policy/                 # Git policy validation
│   ├── __init__.py
│   └── cli.py
├── readiness/              # AI readiness scanning
│   ├── __init__.py
│   └── cli.py
└── forensics/              # Git forensics & impact scoring
    ├── __init__.py
    └── cli.py
```

#### Command Changes

**Old commands**:
```bash
gitops-health risk-score --commit HEAD
gitops-health compliance-check
```

**New commands**:
```bash
python -m src.gitops_ai.policy.cli --validate-last
python -m src.gitops_ai.readiness.cli --format markdown
python -m src.gitops_ai.forensics.cli --range HEAD~10..HEAD
```

Or use VS Code tasks:
- `Git: Validate Commit Message`
- `AI: Readiness Scan`
- `Git: Forensics Report`

---

## 📦 New Centralized Configuration

### `tools/config.py`

All tools now use the centralized configuration module:

```python
from tools.config import get_config, Environment, RiskLevel

# Load validated configuration
config = get_config()

# Access settings
if config.openai:
    print(f"Model: {config.openai.model}")
    api_key = config.openai.api_key.get_secret_value()

# Check environment
if config.environment == Environment.PRODUCTION:
    print("Running in production mode")

# Use healthcare settings
patterns = config.healthcare.risk_patterns
compliance = config.healthcare.compliance_mapping
```

#### Benefits
- ✅ Type-safe configuration
- ✅ Automatic validation
- ✅ Environment-based settings
- ✅ Secure credential handling
- ✅ Health checks included

---

## 🔧 Breaking Changes

### 1. Import Path Changes

| Old Import | New Import | Status |
|------------|------------|--------|
| `from intelligent_bisect import *` | `from git_intelligent_bisect import *` | ❌ Breaking |
| `from healthcare_commit_generator import *` | `from git_copilot_commit import *` | ❌ Breaking |
| `from gitops_health.risk import *` | `from gitops_ai.policy import *` | ⚠️ Legacy works |

### 2. CLI Command Changes

| Old Command | New Command | Status |
|-------------|-------------|--------|
| `python tools/intelligent_bisect.py` | `python tools/git_intelligent_bisect.py` | ❌ Breaking |
| `python tools/healthcare_commit_generator.py` | `python tools/git_copilot_commit.py` | ❌ Breaking |
| `gitops-health risk-score` | `python -m src.gitops_ai.policy.cli` | ⚠️ Both work |

### 3. Configuration Changes

**Old** (Scattered):
```python
import os
api_key = os.getenv("OPENAI_API_KEY")
model = os.getenv("OPENAI_MODEL", "gpt-4o")
```

**New** (Centralized):
```python
from tools.config import get_config

config = get_config()
api_key = config.openai.api_key.get_secret_value()
model = config.openai.model
```

---

## 📅 Deprecation Timeline

| Date | Action | Status |
|------|--------|--------|
| **Dec 14, 2025** | Deprecate duplicate tools | ✅ Complete |
| **Jan 15, 2026** | Remove deprecated files | ⏳ Planned |
| **Feb 1, 2026** | Final migration deadline | ⏳ Planned |

---

## ✅ Migration Checklist

### For Developers
- [ ] Update imports in your code
- [ ] Replace old CLI commands in scripts
- [ ] Test with new tools
- [ ] Update documentation
- [ ] Remove references to deprecated tools

### For CI/CD Pipelines
- [ ] Update GitHub Actions workflows
- [ ] Update deployment scripts
- [ ] Test automated builds
- [ ] Update monitoring scripts

### For Documentation
- [ ] Update README files
- [ ] Update quick start guides
- [ ] Update API documentation
- [ ] Update training materials

---

## 🆘 Need Help?

### Quick Reference
- **New Config Module**: `tools/config.py`
- **Primary Bisect Tool**: `tools/git_intelligent_bisect.py`
- **Primary Commit Tool**: `tools/git_copilot_commit.py`
- **New Package**: `src/gitops_ai/`

### Testing Your Migration
```bash
# Validate configuration
python tools/config.py

# Test commit generation
python tools/git_copilot_commit.py --analyze

# Test bisect
python tools/git_intelligent_bisect.py --help

# Run tests
pytest tests/python/test_config.py -v
```

### Common Issues

**Issue 1**: `ModuleNotFoundError: No module named 'intelligent_bisect'`
```bash
# Solution: Update import
# Old: from intelligent_bisect import AIIncidentResponse
# New: from git_intelligent_bisect import AIIncidentResponse
```

**Issue 2**: `Config not loading OpenAI settings`
```bash
# Solution: Check environment variable
echo $OPENAI_API_KEY
python tools/config.py  # Run health check
```

**Issue 3**: `Command not found: gitops-health`
```bash
# Solution: Use new command structure
python -m src.gitops_ai.policy.cli --validate-last
```

---

## 📊 Impact Analysis

### Files Affected
- **Deprecated**: 2 files (intelligent_bisect.py, healthcare_commit_generator.py)
- **New**: 1 file (config.py)
- **Enhanced**: 1 file (git_copilot_commit.py)

### Code Reduction
- **Removed duplicates**: ~1,200 LOC
- **Added config module**: +380 LOC
- **Net reduction**: -820 LOC (-40% duplication)

### Quality Improvements
- ✅ Zero duplicate implementations
- ✅ Centralized configuration
- ✅ Type-safe interfaces
- ✅ Better error handling
- ✅ Comprehensive testing

---

## 📞 Support

Questions about migration?
- Review: `CODE_REVIEW_FINAL_REPORT.md`
- Quick ref: `REFACTORING_QUICK_REF.md`
- Issues: Create GitHub issue with label `migration`

---

**Last Updated**: December 14, 2025  
**Version**: 2.0.0  
**Status**: ✅ Ready for migration

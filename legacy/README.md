# Legacy Tools Archive

**Status**: Deprecated - Use unified CLI instead  
**Date Archived**: November 23, 2025  
**Replacement**: `gitops-health` CLI (see `/tools/gitops_health/`)

---

## Purpose

This directory contains legacy tools that have been **consolidated into the unified CLI**. These scripts are kept for historical reference and backwards compatibility during the migration period.

**⚠️ Do not use these tools directly.** Use the modern CLI instead.

---

## Migration Guide

| Legacy Tool | New CLI Command | Status |
|-------------|-----------------|--------|
| `ai_compliance_framework.py` | `gitops-health compliance check` | ✅ Replaced |
| `intelligent_bisect.py` | `gitops-health forensics bisect` | ✅ Replaced |
| `healthcare_commit_generator.py` | `gitops-health commit generate` | ✅ Replaced |
| `secret_sanitizer.py` | `gitops-health sanitize` | ✅ Replaced |
| `synthetic_phi_generator.py` | `gitops-health sanitize --generate-synthetic` | 🔄 Partially replaced |
| `compliance_monitor.py` | `gitops-health compliance check --watch` | 🔄 Planned |
| `load_testing.py` | Moved to `/tests/performance/` | 🔄 Reorganized |

---

## How to Migrate

### Before (Legacy)
```bash
# Old way - scattered tools
python tools/intelligent_bisect.py --good v1.0 --bad HEAD
python tools/healthcare_commit_generator.py --ai
python tools/secret_sanitizer.py scan src/
```

### After (Unified CLI)
```bash
# New way - single command
gitops-health forensics bisect --good v1.0 --bad HEAD
gitops-health commit generate --use-ai
gitops-health sanitize src/
```

---

## Benefits of Unified CLI

1. **Single Installation**: `pip install -e .` vs multiple script installations
2. **Consistent Interface**: All commands follow same pattern
3. **Better Help**: `gitops-health --help` shows everything
4. **Configuration**: Single YAML config file
5. **Testing**: Comprehensive test suite
6. **Maintenance**: Easier to update and fix bugs

---

## Timeline

- **Phase 1 (Nov 2025)**: Unified CLI released
- **Phase 2 (Dec 2025)**: Legacy tools marked deprecated
- **Phase 3 (Jan 2026)**: Remove legacy tools from main branch
- **Phase 4 (Feb 2026)**: Archive to separate branch

---

## Support

If you need a legacy tool feature that's missing in the new CLI:
1. Open an issue: https://github.com/Oluseyi-Kofoworola/gitops2-healthcare-intelligence-git-commit/issues
2. Tag it with `enhancement` and `cli`
3. Describe the missing functionality

We're committed to feature parity during the migration period.

---

## Files in This Archive

```
legacy/
├── README.md (this file)
├── ai_compliance_framework.py
├── intelligent_bisect.py
├── healthcare_commit_generator.py
├── secret_sanitizer.py
├── synthetic_phi_generator.py
├── compliance_monitor.py
├── load_testing.py
├── real_ai_integration.py
├── token_limit_guard.py
└── intent_commit.py
```

**Total**: 10 legacy scripts (~3,500 lines)  
**Replaced by**: 3,429 lines of modern, tested, documented CLI code

---

**Last Updated**: November 23, 2025

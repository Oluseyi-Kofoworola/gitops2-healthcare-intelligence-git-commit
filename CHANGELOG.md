# Changelog

All notable changes to this project will be documented in this file.

## [1.0.0] - 2025-11-21
### Added
- Risk-adaptive GitHub Actions pipeline with AI risk scoring & policy enforcement.
- Payment gateway healthcare compliance headers (HIPAA/FDA/SOX) and audit IDs.
- Auth service scaffold for future multi-domain risk scoring.
- Regression performance script with accurate latency measurement.
- Dual amount support (Amount & AmountCents) in payment requests.

### Fixed
- Handler/security headers alignment with integration tests.
- Regression script timing calculation.

### Compliance
- Commit hooks enforcing HIPAA metadata.
- OPA policies for enterprise commit governance.

### AI
- Enabled default model gpt-5.1-codex across commit/intelligence tools.

[1.0.0]: https://github.com/Oluseyi-Kofoworola/gitops2-healthcare-intelligence-git-commit/releases/tag/v1.0.0

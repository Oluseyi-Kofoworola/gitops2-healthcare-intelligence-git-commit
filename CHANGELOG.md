# Changelog

All notable changes to this project will be documented in this file.

## [1.1.0-dev] - UNRELEASED
### Added
- AI Compliance CLI (`ai_compliance_framework.py analyze-commit`) with JSON output.
- Multi-domain commit enforcement (payment + auth require `HIPAA:` and `PHI-Impact:` lines).
- Canary rollout simulation script (`scripts/canary_rollout_sim.sh`).
- Coverage workflow placeholder & guidance for Codecov activation.
- Manual pipeline trigger via `workflow_dispatch`.
- Commit generator surfaces active AI model for audit traceability.
- Always-on gating: Compliance Framework, Regression Detection, Deployment Strategy jobs always execute.

### Changed
- Pipeline now internally evaluates risk thresholds instead of skipping stages.
- OPA policy switched from substring detection to line-prefixed structured metadata (`HIPAA:`, `PHI-Impact:`).
- Risk scorer JSON format aligned for pipeline parsing.

### Removed
- Legacy substring metadata checks in commit policy.
- Redundant policy variants and obsolete HIPAA substring rule.

### Fixed
- Safe commit ref validation & YAML config loading in AI compliance CLI.
- Agent initialization edge case (skip non-dict default_model) in compliance tooling.

### Policy
- OPA tests: 6/6 passing including negative PHI-Impact case.
- Roadmap: granular deny messages (missing HIPAA vs PHI-Impact) and FDA/SOX metadata extension.

### AI
- GPT-5.1-Codex surfaced across commit generator & audit tooling.

### CI/CD
- Risk-adaptive pipeline summary expanded (standard / canary / manual-approval).
- Regression detection integrated for medium/high risk changes.

### Security
- CodeQL weekly scan added (Go + Python).
- Dependabot configuration for Go modules, Actions, npm.

### Pending / Next
- Activate coverage badge (Codecov) after secret/app install.
- Extend structured metadata for FDA-510k & SOX controls.
- Add granular policy deny messages.
- Optimize dependency caching (Go & Python) in workflows.

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

# Repository Cleanup Plan

**Goal**: Make the repository production-ready, easy to navigate, and contributor-friendly

## Files to KEEP (Essential)

### Root Level
- ✅ `README.md` - Main entry point
- ✅ `START_HERE.md` - Quick start guide
- ✅ `CONTRIBUTING.md` - Contribution guidelines
- ✅ `CODE_OF_CONDUCT.md` - Community standards
- ✅ `SECURITY.md` - Security policy
- ✅ `LICENSE` - Legal
- ✅ `CHANGELOG.md` - Version history
- ✅ `ROADMAP.md` - Future plans
- ✅ `package.json` - Node dependencies
- ✅ `pyproject.toml` - Python dependencies
- ✅ `commitlint.config.cjs` - Commit linting
- ✅ `go.work` / `go.work.sum` - Go workspace

### Documentation (`docs/`)
- ✅ `docs/README.md` - Docs index
- ✅ `docs/SCENARIO_END_TO_END.md` - Complete walkthrough
- ✅ `docs/DEPLOYMENT_GUIDE.md` - How to deploy
- ✅ `docs/COMPLIANCE_GUIDE.md` - Compliance reference
- ✅ `docs/AI_TOOLS_REFERENCE.md` - AI tools guide
- ✅ `docs/examples/` - Example files

### Services
- ✅ All service code and READMEs
- ✅ Service-level documentation

### Tests
- ✅ All test code
- ✅ Test documentation (consolidated)

### Tools & Scripts
- ✅ All Python tools
- ✅ Shell scripts
- ✅ Policies (OPA)

## Files to REMOVE (Development/Internal)

### Root Level - Remove
- ❌ `ENGINEERING_JOURNAL.md` - Development history (move to archive)
- ❌ `COMPLIANCE_AND_SECURITY_JOURNAL.md` - Development notes (move to archive)
- ❌ `PROJECT_PROGRESS_REPORT.md` - Internal tracking (move to archive)
- ❌ `SECTION_F_COMPLETION_REPORT.md` - Internal milestone (move to archive)
- ❌ `QUICK_STATUS.md` - Internal status (move to archive)
- ❌ `UPGRADE_PROGRESS_REPORT.md` - Internal tracking (move to archive)
- ❌ `WORKFLOW_FIXES.md` - Development notes (move to archive)
- ❌ `STATUS.md` - Duplicate status (move to archive)
- ❌ `TESTING_SUITE_VISUAL_SUMMARY.md` - Internal notes (move to archive)
- ❌ `npm-audit.json` - Build artifact (delete)
- ❌ `demo.sh` - Superseded by better demos (remove if redundant)
- ❌ `healthcare-demo.sh` - Consolidate into one demo
- ❌ `healthcare-demo-new.sh` - Consolidate
- ❌ `executive-demo.sh` - Consolidate
- ❌ `final-validation.sh` - Move to scripts/
- ❌ `security-audit-complete.sh` - Move to scripts/
- ❌ `security-validation.sh` - Move to scripts/
- ❌ `validate-code-quality.sh` - Move to scripts/
- ❌ `setup-healthcare-enterprise.sh` - Move to scripts/
- ❌ `setup-git-aliases.sh` - Move to scripts/
- ❌ `generate_upgrade_scaffolding.py` - Development tool (archive)

### Documentation - Remove/Consolidate
- ❌ `docs/EXECUTIVE_OVERVIEW.md` - Consolidate with SCENARIO_END_TO_END.md
- ❌ `docs/EXECUTIVE_SUMMARY.md` - Duplicate
- ❌ `docs/ENGINEERING_GUIDE.md` - Keep one version
- ❌ `docs/ENGINEERING_GUIDE.new.md` - Remove duplicate
- ❌ `docs/END_TO_END_SCENARIO.md` - Duplicate of SCENARIO_END_TO_END.md
- ❌ `docs/IMPLEMENTATION_UPDATE.md` - Development notes
- ❌ `docs/ENTERPRISE_READINESS.md` - Consolidate into DEPLOYMENT_GUIDE
- ❌ `docs/GLOBAL_COMPLIANCE.md` - Consolidate into COMPLIANCE_GUIDE
- ❌ `docs/PIPELINE_TELEMETRY_LOGS.md` - Development artifact
- ❌ `docs/INCIDENT_FORENSICS_DEMO.md` - Consolidate into SCENARIO_END_TO_END
- ❌ `docs/REGRESSION_REPORT_SCHEMA.md` - Move to examples/
- ❌ `docs/archive/` - Already archived

### Executive Folder - Remove
- ❌ `executive/` - Consolidate into docs/SCENARIO_END_TO_END.md

### Service-level - Clean
- ❌ `services/*/COMPLETION_REPORT.md` - Development artifacts

### GitHub - Clean
- ❌ `.github/CONSOLIDATION_PLAN.md` - Internal planning
- ❌ `.github/REPO_METADATA.md` - Internal metadata
- ❌ `.github/CI_CD_AUTOMATION_GUIDE.md` - Move to docs/
- ❌ `.copilot/` - Development artifacts (optional: keep if useful)

### Internal Folder
- ❌ `internal/notes/` - Development notes
- ❌ `internal/archive/` - Already archived

### Legacy Folder
- ❌ `legacy/` - Old code (archive or delete)

## Consolidation Actions

1. **Create `archive/` folder** for development artifacts
2. **Merge duplicate guides** into canonical versions
3. **Create single `DEMO.md`** with all demo scenarios
4. **Move scripts** from root to `scripts/` directory
5. **Create comprehensive `docs/GETTING_STARTED.md`**
6. **Update README.md** with clear navigation

## Final Structure

```
gitops2-enterprise-git-intel-demo/
├── README.md                    # Main entry point
├── START_HERE.md               # Quick start (5 min)
├── CONTRIBUTING.md             # How to contribute
├── CHANGELOG.md                # Version history
├── ROADMAP.md                  # Future plans
├── LICENSE                     # MIT License
├── SECURITY.md                 # Security policy
├── CODE_OF_CONDUCT.md          # Community standards
├── package.json                # Dependencies
├── pyproject.toml              # Python deps
├── commitlint.config.cjs       # Commit linting
├── go.work                     # Go workspace
│
├── docs/                       # Documentation
│   ├── README.md              # Docs index
│   ├── GETTING_STARTED.md     # Complete setup guide
│   ├── DEMO.md                # All demo scenarios
│   ├── DEPLOYMENT_GUIDE.md    # Production deployment
│   ├── COMPLIANCE_GUIDE.md    # HIPAA/FDA/SOX reference
│   ├── AI_TOOLS_REFERENCE.md  # AI tools documentation
│   └── examples/              # Example configs
│
├── services/                   # Microservices
│   ├── auth-service/
│   ├── payment-gateway/
│   ├── phi-service/
│   ├── medical-device/
│   └── synthetic-phi-service/
│
├── tests/                      # Test suite
│   ├── README.md
│   ├── integration/
│   ├── e2e/
│   ├── contract/
│   ├── load/
│   ├── chaos/
│   └── security/
│
├── tools/                      # CLI tools & utilities
│   ├── ai_compliance_framework.py
│   ├── healthcare_commit_generator.py
│   ├── intelligent_bisect.py
│   └── ...
│
├── scripts/                    # Automation scripts
│   ├── setup.sh               # Initial setup
│   ├── demo.sh                # Run demo
│   ├── validate.sh            # Validation
│   └── ...
│
├── policies/                   # OPA policies
│   └── healthcare/
│
├── config/                     # Configuration
│   └── examples/
│
└── .github/                    # GitHub config
    └── workflows/
```

# Screenshot Placeholder Directory

## Required Screenshots for Copilot Demo

This directory should contain the following screenshots to support the workflow demonstration:

### 01-code-change-phi-service.png
**Content:** VSCode window showing developer editing `services/synthetic-phi-service/handlers/patient.go`
- Show line changes (before/after comparison)
- Highlight encryption-related code
- File tree visible on left showing healthcare service structure

### 02-copilot-detecting-compliance.png
**Content:** Copilot icon/indicator showing active analysis
- VSCode status bar showing "Copilot: Analyzing healthcare context..."
- Subtle UI indication that Copilot is processing compliance requirements
- Terminal showing pre-commit hook detection

### 03-generated-commit-message.png
**Content:** Source control panel with AI-generated commit message
- Full HIPAA-compliant commit message visible
- Structured metadata sections clearly shown
- Conventional Commits format highlighted
- Character count showing substantial metadata (500+ characters)

### 04-risk-score-calculation.png
**Content:** Terminal output from pre-commit hook
- OPA policy evaluation results
- Risk score calculation (e.g., "Risk Score: 72.4 (HIGH)")
- Compliance framework checkmarks (✅ HIPAA, ✅ NIST)
- Estimated review time

### 05-suggested-reviewers.png
**Content:** GitHub PR interface or commit metadata showing reviewers
- Automatically assigned reviewers: @privacy-officer, @security-team
- Reviewer assignment rationale
- Required approvals count (e.g., "2/2 required for HIGH risk")

---

## How to Capture Screenshots

### Tools Recommended
- **macOS:** Cmd+Shift+4 (with Shift+Space for full window capture)
- **Windows:** Snipping Tool or Win+Shift+S
- **Linux:** Flameshot or GNOME Screenshot

### Best Practices
1. **Resolution:** Minimum 1920x1080 (HD)
2. **Format:** PNG for clarity, JPG for smaller file sizes
3. **Annotations:** Use red arrows/boxes to highlight key elements
4. **Privacy:** Redact any real patient data (should only be synthetic)
5. **Consistency:** Use the same VSCode theme (recommend "GitHub Dark" for professional look)

### Annotation Tools
- [Shottr](https://shottr.cc/) - macOS, free
- [Greenshot](https://getgreenshot.org/) - Windows, free
- [Flameshot](https://flameshot.org/) - Linux, free

---

## Alternative: Placeholder Images

If screenshots are not immediately available, you can use the provided placeholders:

```bash
# Generate placeholder images (requires ImageMagick)
convert -size 1920x1080 xc:lightgray -pointsize 48 -fill black \
  -draw "text 500,540 'Screenshot: Code Change in PHI Service'" \
  01-code-change-phi-service.png

convert -size 1920x1080 xc:lightblue -pointsize 48 -fill darkblue \
  -draw "text 450,540 'Screenshot: Copilot Detecting Compliance'" \
  02-copilot-detecting-compliance.png

convert -size 1920x1080 xc:lightgreen -pointsize 48 -fill darkgreen \
  -draw "text 450,540 'Screenshot: Generated Commit Message'" \
  03-generated-commit-message.png

convert -size 1920x1080 xc:lightyellow -pointsize 48 -fill darkorange \
  -draw "text 500,540 'Screenshot: Risk Score Calculation'" \
  04-risk-score-calculation.png

convert -size 1920x1080 xc:lightcoral -pointsize 48 -fill darkred \
  -draw "text 520,540 'Screenshot: Suggested Reviewers'" \
  05-suggested-reviewers.png
```

---

## Video Recording Guidelines

### Structure (Total: 3 minutes)
1. **Intro (15 sec):** Show repository structure, explain healthcare context
2. **Code Change (30 sec):** Make a real change to PHI service
3. **Copilot Activation (10 sec):** Open commit message panel, show Copilot loading
4. **Message Generation (20 sec):** Watch Copilot generate full compliant message
5. **Validation (25 sec):** Pre-commit hook runs, shows risk score
6. **Review Assignment (15 sec):** Show suggested reviewers
7. **Comparison (30 sec):** Side-by-side with manual commit (slow, error-prone)
8. **Metrics (30 sec):** Show time savings dashboard
9. **Outro (15 sec):** Call to action, link to docs

### Recording Setup
- **Resolution:** 1080p minimum (4K preferred)
- **Frame Rate:** 30fps or 60fps
- **Audio:** Clear voiceover explaining each step
- **Cursor:** Enable cursor highlighting for visibility
- **Pacing:** Slow enough to follow, fast enough to maintain interest

### Hosting Recommendations
1. **YouTube** - Best for long-term hosting, SEO
2. **Vimeo** - Professional, ad-free experience
3. **Loom** - Quick sharing, easy embedding
4. **GitHub** - Store MP4 in Git LFS for direct repo linking

---

*For questions or support, contact: platform-engineering@example.com*

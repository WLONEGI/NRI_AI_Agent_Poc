<!--
Sync Impact Report
Version change: 1.0.0 → 1.1.0
Modified principles:
- None
Added sections:
- Isolated Python Environments (new principle VI)
Removed sections:
- None
Templates requiring updates:
- ✅ .specify/templates/plan-template.md (verified - Technical Context section compatible)
- ✅ .specify/templates/spec-template.md (verified - no changes needed)
- ✅ .specify/templates/tasks-template.md (verified - setup phase can include venv tasks)
Follow-up TODOs:
- None
-->

# NRI AI Agent PoC Constitution

## Core Principles

### I. Inclusive Accessibility
- All user-facing experiences MUST comply with WCAG 2.1 AA before release, supported by automated and manual checks documented in specs and test artifacts.
- Accessibility acceptance criteria MUST be defined per user story and traced to corresponding tests in plan/tasks outputs.
- Releases are blocked until accessibility regressions are remediated or a reviewed fix-forward plan is executed within the same iteration.
- Rationale: Inclusive design is a contractual requirement for this PoC and mitigates legal, reputational, and user-experience risk.

### II. Test-Complete Delivery
- Every new or modified code path MUST ship with unit tests that exercise success, failure, and edge cases, demonstrating coverage in CI before merge.
- Feature branches MUST show failing tests prior to implementation and passing tests prior to merge as evidence of the red-green-refactor cycle.
- Test ownership and maintenance responsibilities MUST be recorded in the plan/tasks documents to keep accountability visible.
- Rationale: Enforced unit testing is the primary safeguard against regressions and enables reliable iteration velocity.

### III. Lint-Driven Consistency
- Ruff and Black configurations in this repository are canonical; code MUST conform with no local overrides at merge time.
- Any proposed rule changes or temporary disables MUST be approved by the system architect and recorded in the rationale log with scope and expiry.
- CI jobs MUST run linting and formatting checks on every change set; failures block merge until resolved.
- Rationale: Consistent style and static analysis reduce cognitive load, eliminate avoidable defects, and keep reviews focused on logic.

### IV. Rapid Security Remediation
- Newly discovered security vulnerabilities MUST be triaged immediately and remediated within 24 hours of confirmation, regardless of origin.
- Security issues MUST be tracked with an owner, severity, mitigation plan, and retrospective to capture learning and prevent recurrence.
- Feature work MUST include proactive security checks (dependency scanning, threat modeling updates) documented alongside tasks.
- Rationale: Fast, accountable remediation protects stakeholders, preserves trust, and aligns with organizational security posture.

### V. Traceable Governance
- GitHub `main`/`master` branches serve as the single source of truth; all work MUST rebase or merge from the latest baseline before review.
- Business logic and non-functional requirements MUST include documented rationale, stakeholder sign-off, and links to supporting evidence.
- Specs, plans, and tasks MUST reference the authoritative rationale entries to keep implementation aligned with business intent.
- Rationale: Transparent decision history ensures continuity, accelerates onboarding, and simplifies audits.

### VI. Isolated Python Environments
- All Python code execution MUST occur within a virtual environment (venv, virtualenv, or equivalent) to ensure dependency isolation and reproducibility.
- Virtual environment setup MUST be documented in project initialization steps and enforced in development, testing, and CI/CD pipelines.
- Dependencies MUST be managed via requirements files or pyproject.toml with exact version pinning to prevent environment drift.
- Rationale: Virtual environments prevent dependency conflicts, ensure reproducible builds across team members and environments, and align with Python best practices for professional development.

## Compliance & Documentation Standards

- Maintain an accessibility compliance ledger outlining audits performed, outstanding issues, and mitigation owners.
- Store business logic and non-functional rationales in ADRs or spec rationale logs with timestamps and stakeholders, and link them from relevant pull requests.
- Capture security response timelines, including discovery, fix deployment, and validation, to verify adherence to the 24-hour remediation mandate.
- Document virtual environment setup instructions in README or project setup guides, including activation commands and dependency installation procedures.
- Ensure all documentation updates occur alongside code changes so reviewers can confirm policy compliance within a single review unit.

## Development Workflow & Baselines

- All changes MUST flow through reviewed pull requests that confirm accessibility, testing, linting, security, and environment isolation gates before approval.
- Continuous integration MUST enforce passing unit test suites, lint checks, accessibility audits (automated where applicable), and virtual environment validation prior to merge.
- Feature branches MUST include in plan/tasks deliverables the explicit mapping from requirements to tests, rationale entries, mitigation owners, and environment setup steps.
- Project setup phase MUST include virtual environment creation, dependency installation, and activation verification as mandatory initialization tasks.
- Release candidates MUST include a compliance checklist confirming no outstanding policy violations, with sign-off recorded in project documentation.

## Governance

- This constitution supersedes conflicting practices within the repository; deviations require documented approval from the product owner and system architect.
- Amendments require a written proposal summarizing the change, impact analysis, and updated compliance checklists, followed by consensus from product, architecture, and security leads.
- Versioning follows semantic rules: MAJOR for principle changes or removals, MINOR for new sections or expanded obligations, PATCH for clarifications.
- Compliance reviews MUST occur at least once per iteration or monthly (whichever is sooner), with findings logged against the rationale ledger and actioned before the next release.

**Version**: 1.1.0 | **Ratified**: 2025-10-17 | **Last Amended**: 2025-10-19

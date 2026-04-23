# PROJECT_PROFILE_CONTEXTFORGE

Version: 0.1.0
LastUpdated: 2026-01-31
CommitHash: TBD

## 1. Project Identity
- Product: ContextForge
- Edition Strategy: OSS + Pro (two-tier)
- Primary Value: deterministic, shareable input artifacts for LLM usage

## 2. Scope (What we ship)
### 2.1 OSS (ContextForge)
- Local deterministic artifact generator
- Profiles for common input constraint patterns
- ZIP and/or single report outputs
- Best-effort support (no SLA)

### 2.2 Pro (ContextForge Pro)
- Guarantees:
  - reproducible fixed input artifacts
  - structure/order/naming compatibility within same major
  - business presets (audit / handover / security-review / refactor-review)
  - rationale / manifest / checksum included
- Not guaranteed:
  - LLM output quality
  - legal/regulatory compliance
  - model-specific interpretation correctness

## 3. Invariants (Must Never Break in OSS v1.x)
1) No LLM API usage (no model calls)
2) Deterministic output structure for the same inputs/profile/version
3) Artifact directory conventions:
   - `exports/` and `logs/` are runtime outputs and git-ignored
4) Output_mode semantics remain stable
5) Profiles are “input constraint presets”, not “LLM vendor bindings”

## 4. Compatibility Promise
- Any change that breaks artifact structure or naming => major bump
- Minor/patch may add new profiles, improve heuristics, and fix bugs without breaking structure

## 5. Quality Gates (Minimum)
- CLI run must succeed on first run even if `exports/` does not exist
- Generate ZIP without exceeding the profile’s target constraints (best-effort)
- No leakage of secrets via default includes (basic exclude rules)

## 6. Release & Versioning Policy
- Semantic versioning (MAJOR.MINOR.PATCH)
- Patch: bug fixes only
- Minor: new profiles, non-breaking improvements
- Major: any compatibility-breaking change

## 7. Repo Policy
- Commit messages: concise, purpose-first
- Tags: `vX.Y.Z`
- README is primary public artifact (marketing is README-first)

## 8. Known Risks
- Large repositories can generate oversized artifacts unless constrained
- Exclusion rules must be conservative to avoid secret leakage
- Different UIs/platforms may have different upload limits; handle via profiles, not vendor coupling

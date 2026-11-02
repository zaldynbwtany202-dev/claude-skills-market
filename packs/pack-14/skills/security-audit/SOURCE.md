# Source and adaptation record

Repository: https://github.com/afiqiqmal/claude-security-audit
Branch: main
License: MIT (full copy in LICENSE).
Main command Git blob SHA: f6457bf978de113fc3cb1e72cd34367bc8380cd9
Retrieved: 2026-11-02
Adapter classification: CONVERT / HARDEN.

Imported into this physical Claude Code Skill:
- Main command: security-audit (adapted as SKILL.md).
- security-audit-guidelines.md.
- attack-vectors.md.
- compliance-mapping.md.
- custom-template.md.
- features-extended.md.
- nist-csf-mapping.md.
- 12 framework reference files.
- 6 compliance-pack reference files.

Excluded:
- Upstream install.sh and installer behavior.
- Codex/Cursor/Copilot/Windsurf and other agent-host installations.
- PDF converter setup and automatic conversion.
- Any runtime dependency installation or remote scanner.

Local changes:
- Native Claude Code Skill frontmatter and user-invocable /security-audit entrypoint.
- All references reside inside this Skill under references/; no shared home-level reference folder or Junction/Symlink.
- Restricted Bash allow-list (git status/diff and read-only file inspection only).
- Gray-box default is passive source/test analysis. No live HTTP probes, login attempts, role tampering, rate-limit tests or external target scans without explicit authorization for an isolated local test target.
- No network package audits or external API calls by default; dependency advisory state is marked UNVERIFIED when offline.
- No secret values may be read or printed.
- --fix creates suggested remediation code snippets in the report only; it does not modify application source.
- Markdown is the only automatic output; no PDF converter lookup or installation.
- Source repository files remain unchanged.

Official OWASP version confirmation:
- https://owasp.org/projects/top-ten
- https://top10.owasp.org/2025/
As of 2026-11-02, the official OWASP project page identifies Top 10:2025 as the latest released version.
See references/VERSION-AND-SCOPE.md for version and assurance caveats.

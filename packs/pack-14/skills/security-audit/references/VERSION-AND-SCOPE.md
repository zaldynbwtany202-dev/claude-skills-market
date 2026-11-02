# Security Audit Reference Version and Scope

Updated: 2026-11-02

## OWASP

This skill maps application risks to OWASP Top 10:2025. The OWASP Foundation's project page confirms 2025 is the most current released version as of this date:
- https://owasp.org/projects/top-ten
- https://top10.owasp.org/2025/
- https://github.com/OWASP/Top10

The 2025 categories used by this skill:
1. Broken Access Control
2. Security Misconfiguration
3. Software Supply Chain Failures
4. Cryptographic Failures
5. Injection
6. Insecure Design
7. Authentication Failures
8. Software or Data Integrity Failures
9. Security Logging and Alerting Failures
10. Mishandling of Exceptional Conditions

## Other mappings

The imported upstream reference set includes NIST CSF 2.0, CWE, SANS Top 25, ASVS, PCI DSS, MITRE ATT&CK, SOC 2 and ISO 27001 mappings. These are reference crosswalks, not claims of formal compliance or certification.

## Scope caveats

- A mapping is not a compliance attestation.
- The skill does not certify an application or organization.
- Regulatory applicability depends on jurisdiction, sector, contract and data processing context.
- Framework-specific checklists are starting points; confirm exact framework/runtime versions in the project.
- Dependency CVE status is UNVERIFIED if the audit is offline and cannot consult trusted advisory databases.
- Static review can identify design/code risks but does not prove exploitability or runtime behavior.
- Live Gray-box testing remains disabled by default. Only use an isolated local test environment and exact user authorization.
- Do not treat a clean report as proof that the application is secure.

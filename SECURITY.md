# Security Policy

## Reporting a vulnerability

**Do not open a public Issue to report a security vulnerability.**

Use GitHub's Private Vulnerability Reporting if it is enabled for this repository.
If it is not yet enabled, contact the repository owner through a private channel.

When reporting, include:

- A clear description of the vulnerability
- Steps to reproduce
- Affected versions (commit SHA or tag)
- Any suggested mitigations

## What to report

- Leaked credentials, tokens, or keys
- Authentication or authorization bypasses
- Validation gaps that allow scope or identity drift
- CI/CD pipeline vulnerabilities
- Supply-chain risks in dependencies

## Response

The repository owner will acknowledge receipt within 72 hours and provide a
timeline for assessment and remediation.

## Post-disclosure

If a vulnerability involves leaked credentials:

1. **Revoke** the credential immediately.
2. **Rotate** any related tokens or keys.
3. **Audit** access logs for unauthorized use.
4. **Commit** a post-mortem to the private Ops repository — not to the public core.

Public architecture documentation should never contain real credentials. If you
discover any, report them; do not attempt to remediate through a public PR.

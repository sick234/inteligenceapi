# Security Policy

## Supported Versions

The latest release on the `main` branch is actively supported.

| Version | Supported |
|---------|-----------|
| `main`  | ✅ |
| older   | ❌ |

## Reporting a Vulnerability

**Please do not open public GitHub issues for security vulnerabilities.**

If you discover a security issue, report it privately via one of:

1. **GitHub Security Advisories** — open a [private advisory](https://github.com/sick234/inteligenceapi/security/advisories/new) on this repository.
2. **Direct contact** — reach out to the maintainer through the contact on the repo profile.

Please include:

- A description of the issue and its impact
- Steps to reproduce (proof of concept welcome)
- The affected endpoint, file, or commit hash
- Suggested remediation, if you have one

You can expect an initial acknowledgement within **72 hours** and a fix or mitigation plan within **14 days** for confirmed issues.

## Scope

In scope:

- Authentication and session handling (`app/api/auth.py`)
- Upload validation and file storage (`app/api/documents.py`)
- Ownership / access control (IDOR)
- SQL injection, deserialisation, SSRF, RCE
- Rate limiting bypasses
- Dependency vulnerabilities

Out of scope:

- Issues requiring a compromised host or already-authenticated admin
- Rate-limit evasion via distributed infrastructure
- Findings from automated scanners without demonstrated impact
- Self-XSS or clickjacking on pages without sensitive actions

## Hardening Already in Place

| Area | Mitigation |
|------|-----------|
| Secrets | `SECRET_KEY` is required, validated for length and known-weak values |
| Uploads | Magic-byte sniffing, streamed chunk-size enforcement, UUID filenames |
| Path traversal | Resolved-path containment check against the uploads directory |
| Auth | bcrypt hashing, JWT with expiry, password strength validator |
| IDOR | All document queries filter by `owner_id` |
| Abuse | Per-route rate limits via slowapi |
| Transport | Security headers middleware (CSP, X-Frame-Options, etc.) |
| Schema | Alembic migrations; no runtime `create_all` |

Thank you for helping keep this project and its users safe.

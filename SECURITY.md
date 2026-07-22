# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.2.x   | :white_check_mark: |
| 0.1.x   | :x:                |
| < 0.1   | :x:                |

## Reporting a Vulnerability

If you discover a security vulnerability in Lemma, please report it responsibly.

### How to Report

1. **GitHub Security Advisories** (preferred): Use the [Security Advisories](https://github.com/Andiii208/lemma/security/advisories/new) page to report privately
2. **Email**: Send details to security@lemma.app (if available)

### What to Include

- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

### Response Timeline

- **Initial response**: Within 48 hours
- **Status update**: Within 7 days
- **Fix release**: Depends on severity

### Scope

The following areas are in scope:

- **Electron security**: Context isolation, sandbox, IPC validation
- **API Key handling**: Encryption, storage, transmission
- **File system access**: Path traversal, unauthorized access
- **Dependencies**: Known vulnerabilities in npm packages

### Out of Scope

- Social engineering attacks
- Physical access to the user's machine
- Issues in deprecated/legacy code

## Security Measures

### Current Implementation

- `contextIsolation: true` — Renderer process isolated from main process
- `nodeIntegration: false` — Renderer cannot access Node.js APIs
- `sandbox: true` — Chromium sandbox enabled
- `assertTrustedSender()` — IPC source validation
- `AuthorizedPaths` — File path authorization system
- `safeStorage` — API Key encryption at rest
- `isTrustedAppUrl()` — Navigation interception
- `isSafeExternalUrl()` — External link filtering

### Best Practices for Contributors

1. Never commit API keys, tokens, or secrets
2. Always validate user input
3. Use the existing security utilities (`assertTrustedSender`, `isPathAllowed`)
4. Keep dependencies updated
5. Run `npm audit` before submitting PRs

## Acknowledgments

We appreciate security researchers who responsibly disclose vulnerabilities. Contributors will be acknowledged in release notes (unless they prefer anonymity).

# Security Policy

## Supported Versions

Security fixes are provided for the latest release on the default branch.

## Reporting a Vulnerability

Please do not open a public issue for a security vulnerability. Instead, email the maintainer listed in the package metadata or use GitHub private vulnerability reporting if it is enabled for the repository.

Include:

- Affected version or commit
- Reproduction steps
- Impact description
- Any safe proof-of-concept files

The project has a small attack surface, but `.lakeboard` and `.xmind` files are still untrusted input. Avoid running the tool on files from sources you do not trust in privileged environments.

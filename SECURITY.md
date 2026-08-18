# Security notes

- TLS certificate verification is enabled by default.
- Use `insecure=True` or `verify=False` only when certificate verification is intentionally disabled.
- Do not store passwords or bearer tokens in source control.
- Use a least-privilege STRATUM identity for automation.
- Mutating requests are not automatically retried.

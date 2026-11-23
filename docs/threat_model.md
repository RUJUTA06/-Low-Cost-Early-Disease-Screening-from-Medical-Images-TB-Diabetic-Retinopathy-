# Privacy and threat model

## Scope and assumptions

The default Compose application is a local research prototype for a trusted operator and binds to loopback. The optional Render deployment has a shared HTTP Basic access credential for a small private demo. It does not provide individual identities, per-user authorization, role separation, rate limiting, or clinical deployment hardening.

## Sensitive assets and threats

- Medical-image bytes and embedded metadata may identify a person; retain only in request memory and do not write uploads to disk.
- Upload parsers can receive malformed or decompression-bomb images; enforce byte, pixel, decoded-format and dimension limits.
- User-provided filenames can contain paths or identifiers; never use them for storage and avoid logging them.
- Case IDs and review notes can be copied or misused; use random IDs, avoid personal fields, and remind reviewers not to put identifiers in notes.
- A public API could expose screening records; hosted API routes require the configured shared credential, while the health check is intentionally public for the host. Never use this shared credential as a substitute for per-user controls when handling sensitive data.

## Implemented safeguards

Allowlisted decoded formats, bounded upload read, pixel limits, random in-memory buffers, cleanup on request completion, narrow CORS, environment-based configuration, pseudonymous UUIDs, image retention off, safe action audit metadata, local-only Compose port binds, optional shared hosted access gate, and a prominent research-only warning.

## Required before hosting

Threat review; individual authenticated RBAC; rate limits; encrypted storage and backups; retention/deletion policy; audit access controls; dependency scanning; incident response; consent and data governance; jurisdiction-specific review. The shared-password hosted demo is not suitable for identifiable or regulated patient data.

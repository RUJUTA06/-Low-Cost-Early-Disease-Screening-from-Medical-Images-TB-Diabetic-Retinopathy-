# Privacy and threat model

## Scope and assumptions

This application is a local research prototype for a trusted operator. The Compose services bind to loopback. There is no authentication, authorization, user/session management or public deployment hardening in this prototype.

## Sensitive assets and threats

- Medical-image bytes and embedded metadata may identify a person; retain only in request memory and do not write uploads to disk.
- Upload parsers can receive malformed or decompression-bomb images; enforce byte, pixel, decoded-format and dimension limits.
- User-provided filenames can contain paths or identifiers; never use them for storage and avoid logging them.
- Case IDs and review notes can be copied or misused; use random IDs, avoid personal fields, and remind reviewers not to put identifiers in notes.
- A public API could expose screening records; do not bind to public interfaces or publish until access controls and governance are implemented.

## Implemented safeguards

Allowlisted decoded formats, bounded upload read, pixel limits, random in-memory buffers, cleanup on request completion, narrow CORS, environment-based configuration, pseudonymous UUIDs, image retention off, safe action audit metadata, local-only port binds and a prominent research-only warning.

## Required before hosting

Threat review; authenticated RBAC; secure transport; rate limits; CSRF/session protections if cookie auth is used; encrypted storage and backups; retention/deletion policy; audit access controls; dependency scanning; incident response; consent and data governance; jurisdiction-specific review. Do not expose this prototype publicly as-is.

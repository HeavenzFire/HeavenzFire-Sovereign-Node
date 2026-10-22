# SUDO-CORE Native Policy MVP

This Rust standard-library-only crate is the first native component for the HeavenzFire Unified Field execution-control architecture.

## Current scope

- Evaluates a small, explicit capability vocabulary.
- Defaults unknown capabilities, arbitrary privileged execution, and network fetches to DENY.
- Rejects relative-path traversal and selected sensitive workspace paths.
- Permits policy checks for unprivileged ports without opening a socket.
- Includes unit tests for policy decisions.

**This is a policy evaluator, not a sandbox or execution broker yet.** It does not launch child processes, modify files, bind ports, isolate memory, enforce OS access tokens, or create a cryptographic audit ledger. A policy decision by itself is not an OS security boundary.

## Build and test

Requires Rust/Cargo:

    cargo test --manifest-path native/sudo-core/Cargo.toml
    cargo build --release --manifest-path native/sudo-core/Cargo.toml

Example policy checks:

    cargo run --manifest-path native/sudo-core/Cargo.toml -- check workspace-read src/main.rs
    cargo run --manifest-path native/sudo-core/Cargo.toml -- check workspace-write ../outside.txt
    cargo run --manifest-path native/sudo-core/Cargo.toml -- check bind-port 80
    cargo run --manifest-path native/sudo-core/Cargo.toml -- check privileged-exec powershell

Exit codes: 0 means policy allow, 1 means policy deny, and 2 means invalid CLI usage.

## Next implementation gates

1. Resolve filesystem paths against a configured workspace root using handle-based OS APIs; lexical path checks alone are insufficient against symlinks or reparse points.
2. Add Windows restricted-token/AppContainer or Job Object integration in a dedicated platform module.
3. Add a Linux backend for user namespaces, seccomp, and cgroups v2 where supported.
4. Implement append-only audit records with canonical serialization, SHA-256 hash chaining, genesis verification, durable writes, and explicit tamper-evidence limits.
5. Add artifact provenance checks and a signed policy bundle.
6. Add integration tests that prove actual OS enforcement. Never label an operation successful based only on a policy decision.

## Security posture

No arbitrary command execution is exposed. Do not run this MVP as an administrator or treat it as a security boundary. It is intended for development, review, and incremental hardening.

# Local security review — 0.1.0

Scope: this source tree, generated release archives, and isolated loopback test servers. No TV, hotel network, external target, port scan, or penetration test was performed. This is a source review with regression tests, not an independent certification.

## Threat model

The server serves public receiver HTML on the LAN, a sender page exclusively through loopback, and authenticated signaling APIs. Browser pages from another origin, unpaired LAN clients, malformed input, stale tabs, and stale process state cross trust boundaries. A malicious local OS account with access to the project/runtime or a hostile network operator is outside the protection pairing can provide.

The required trust assumption is a trusted LAN. Receiver HTML, pairing, SDP, ICE, and receiver credentials use plain HTTP. An on-path attacker can observe or modify signaling and delivered receiver code. WebRTC encrypts the media connection but does not repair compromised signaling. Never expose the server to the internet or port-forward it.

## Findings and resolutions

| Prototype finding | Resolution | Evidence |
| --- | --- | --- |
| LAN clients could send offers, reports, and stop commands without authentication | Random per-run role credentials; pairing code for receivers; sender/admin credentials accepted only over loopback | HTTP role/credential regression tests |
| Private sender credentials could be exposed by treating the computer's LAN address as local | Only loopback socket source addresses count as local; sender content never included in receiver HTML | Receiver credential-isolation and remote endpoint tests |
| Cross-site and DNS-rebinding requests were not screened | Exact configured Host allowlist, Origin equality, cross-site Fetch Metadata rejection, no CORS, token headers, frame denial | Host/Origin regression tests |
| Client IDs were not tied to messages/reports | Every message/report must carry its authenticated role's currently registered ID | Ownership/relay regression tests |
| JSON framing, sizes, types, and message shapes were insufficiently checked | Fixed body limit, Content-Length validation, chunked rejection, JSON object/schema checks, explicit 32-container nesting limit, nonfinite/overflow number rejection | Malformed-input regression tests |
| Unbounded relay queues and request threads | Bounded queues, rate-limit maps, signaling rate, active connection count, and socket timeouts | Queue tests and source review; full denial-of-service resistance is not claimed |
| Broad mDNS replacement changed arbitrary serialized strings | Rewrite only sender ICE candidate address fields/lines to the configured LAN IPv4 address | mDNS regression test |
| Shell launcher relied on machine-specific tooling and PID files | Standard-library Python launcher; process identity verified against private session state and health response; authenticated server self-shutdown | CLI integration and stale/occupied-process tests |
| README exposed private network, TV, and personal device details | Replace discovery diary with generic setup and historical, anonymized compatibility notes | Publishable-file/artifact audit |
| Experimental congestion workaround was the default | Keep normal browser congestion control; explicit opt-in experimentation only | Frontend unit coverage and source review |

## Residual limitations

- A six-digit pairing code is an access gate for ordinary LAN use, not a defense against an on-path attacker. Restart rotates credentials and invalidates saved receiver sessions.
- Anyone legitimately paired can replace the single receiver. Multiple independent receivers and per-device approval/revocation are not implemented.
- Thread, input, and rate bounds limit resource use; the stdlib HTTP server is not hardened for hostile/public traffic. Local peers can still deny service.
- Runtime files contain secrets. POSIX permission restrictions are applied; Windows permission behavior also depends on the user's directory ACLs.
- No confidentiality is claimed for local diagnostic reports or session metadata visible to authenticated clients.
- Runtime dependencies are the Python standard library and the users' browsers. Keep both on supported, patched releases. Pinned npm and Ruff dependencies are development tools only.
- No independent security assessment, native signing, third-party penetration test, or physical-TV release retest has been performed.

Run the validation commands in CONTRIBUTING.md and inspect RELEASE_READINESS.md for exact local evidence. Report vulnerabilities according to SECURITY.md.

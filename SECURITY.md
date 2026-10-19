# Security policy

## Supported versions

TabTelly is in its first experimental release line. Security fixes are applied to the latest published version only.

## Report a vulnerability

Do not open a public issue or include active pairing codes, runtime files, private LAN addresses, peer IDs, or secrets.

Use GitHub's [private vulnerability report](https://github.com/jckceo/tabtelly/security/advisories/new) flow in the repository's **Security** tab. If private vulnerability reporting is unavailable, use the private contact method on the maintainer's GitHub profile. Include the affected version, impact, reproduction steps, and suggested mitigation when available. No fixed response or remediation timeline is promised.

## Security model

TabTelly is designed for a trusted local network:

- The sender UI is served through loopback only.
- Its runtime token is injected into the sender HTML and does not appear in the `/send` URL.
- The receiver pairs with a six-digit, rate-limited code.
- Signaling actions are authorized for the assigned role and current peer ID.
- Health, status, and control interfaces are loopback-only; status and control also require session credentials.
- WebRTC encrypts media between peers.
- Session secrets are stored under `.run/<port>` by default and must remain untracked.

The local HTTP server and signaling messages are **not confidential on the LAN**. Pairing helps prevent an unpaired browser from taking over a session, but it does not make an untrusted network safe. A network operator or suitably positioned attacker may observe or interfere with HTTP traffic.

Use TabTelly only on a network you trust and control. Do not expose its port to the internet or configure router port forwarding. Guest and hotel networks may both isolate devices and contain untrusted peers.

TabTelly has no cloud service, STUN server, or TURN relay. Direct LAN reachability is required.

## Protected content

TabTelly uses the browser's normal screen-capture API. It does not bypass DRM, HDCP, copy protection, browser capture restrictions, or protected audio paths. Those restrictions are expected behavior.

# Architecture

TabTelly is a local signaling server plus two browser clients. Media travels directly from desktop Chrome to a TV browser.

```text
Computer                                                Television

┌──────────────────────────────┐                  ┌─────────────────────┐
│ Chrome sender (loopback UI)  │  encrypted media │ Browser receiver    │
│ getDisplayMedia() ─ WebRTC ──┼─────────────────>│ WebRTC ──> <video>  │
└──────────────┬───────────────┘                  └──────────┬──────────┘
               │ local HTTP signaling                       │
               └────────────────┬───────────────────────────┘
                                v
                  ┌──────────────────────────┐
                  │ Python stdlib server     │
                  │ pages, pairing, relay,   │
                  │ status and diagnostics   │
                  └──────────────────────────┘
```

## Components

`tabtelly` is the cross-platform command entry point. It manages per-port runtime state, launches `server.py`, reports status, and provides diagnostics. `tabcast` is a legacy wrapper.

`server.py` uses the Python standard library to serve assets and relay WebRTC signaling through long-polling HTTP. It does not carry media.

`web/sender.html` runs in desktop Chrome through loopback. It calls `getDisplayMedia()`, creates the offer, and sends captured tracks over WebRTC. Its runtime sender token is injected into the HTML response and does not appear in the URL.

`web/receiver.html` targets constrained TV browser engines. It pairs with the server, answers the offer, and renders the stream.

## Session flow

1. The server creates ephemeral session material and a six-digit pair code.
2. The TV loads the receiver page over the LAN and submits the code.
3. The server rate-limits attempts and assigns the authenticated receiver role to its current peer ID.
4. Chrome loads the loopback sender page and authenticates with its injected token.
5. The browsers exchange SDP and ICE candidates through role-authenticated local HTTP endpoints.
6. WebRTC establishes a direct LAN media path.
7. Status reports use the server; captured audio and video do not.

Only one current sender and receiver are supported. Replacing a peer invalidates the previous current peer ID.

All session credentials and the pair code rotate on every server start. Restarting the server requires the sender to reload and the receiver to pair again; it is not a seamless media restart. The unauthenticated `/health` identity endpoint is loopback-only and contains no credentials. Status and control endpoints are also loopback-only and require a sender or administrative token.

## Networking

The default bind is `0.0.0.0:8090`, while the sender interface remains loopback-only. The server accepts only `0.0.0.0` for LAN use and `127.0.0.1` for local tests; another explicit bind could not serve both the loopback sender and LAN receiver. `TABTELLY_LAN_IP` overrides the IPv4 address advertised to the receiver and used when adapting local candidates.

There is no STUN, TURN, account, discovery service, or cloud relay. This keeps deployment small and local but prevents traversal of client isolation and most routed boundaries.

## Media behavior

Chrome selects and encodes a source exposed by `getDisplayMedia()`. Browser negotiation chooses a shared codec. Presets request capture constraints and bitrate targets; they cannot guarantee delivered quality.

Chrome's normal GCC congestion-control negotiation is the default. The optional `?cc=loss` path experimentally removes delay-oriented feedback from the offer. The Picture-in-Picture controller provides controls and maintains a visible browser surface; closing it stops casting. Optional `?keepalive=1` is a fallback.

## Trust boundary

WebRTC encrypts media. The page and signaling transport uses local HTTP and is not confidential on the LAN. Pair codes, rate limiting, role authentication, sender tokens, and current peer IDs reduce unauthorized session access; they do not make an untrusted network safe.

Never port-forward the server or expose it to the internet. See [SECURITY.md](../SECURITY.md).

## Non-goals

TabTelly does not implement AirPlay, Google Cast, Miracast, or DLNA control. It does not discover TVs, relay through the cloud, support multiple viewers, or bypass DRM and capture protection.

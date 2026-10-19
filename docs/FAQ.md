# Frequently asked questions

## Is TabTelly AirPlay or Chromecast?

No. It uses Chrome screen capture and WebRTC to a TV web page. It does not implement AirPlay, Google Cast, Miracast, or DLNA.

## Do I install anything on the TV?

No. Open the receiver URL in a compatible built-in browser and enter the six-digit pair code.

## Does it use the cloud?

No. The computer serves the pages and signaling, and media uses direct WebRTC over the LAN. There is no STUN or TURN service.

## Can I use it on hotel Wi-Fi?

Usually not. Guest networks commonly isolate devices. TabTelly requires a direct connection, and a network permitting one is not necessarily trustworthy. Local HTTP signaling is not confidential.

## Is video encrypted?

WebRTC encrypts media. Page and signaling traffic uses local HTTP, so signaling is not confidential from the LAN. Use a trusted network and never port-forward TabTelly.

## Why is there a pair code?

It associates the TV browser with the current local session. Attempts are rate limited. Pairing complements role and peer authentication but does not replace a trusted network.

## Can it cast protected video?

Only if Chrome permits capture. DRM-protected media may be blank, silent, or blocked. TabTelly does not bypass protection.

## Can it share system or window audio?

Tab audio may work when Chrome offers it in the picker. Support varies by OS. Audio from an arbitrary application window is not promised.

## What quality and latency should I expect?

Presets are targets. Actual resolution, frame rate, bitrate, and delay depend on Chrome, the source, Wi-Fi, and TV decoder.

## Why must the small controller stay open?

Some platforms throttle a hidden capture page. The Picture-in-Picture controller keeps a visible surface and provides controls. Closing it stops the cast. If unavailable, keep the sender visible; `?keepalive=1` is an optional fallback.

## What does `?cc=loss` do?

Chrome's standard GCC negotiation is the default. `?cc=loss` enables an experimental loss-oriented mode, which may help or hurt on a given network.

## Can more than one TV connect?

No. The current design supports one sender and one receiver.

## Does a server restart preserve the cast?

No. A restart rotates the session credentials and pair code. Reload the sender and TV pages, then pair again.

## Which TVs work?

Compatibility depends on the exact browser and firmware. The prototype worked with one legacy Chromium-based Hisense VIDAA browser; current real-hardware retesting is unavailable. See [Compatibility](COMPATIBILITY.md).

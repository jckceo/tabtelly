# Compatibility

TabTelly depends on browser APIs and direct LAN connectivity. A TV brand or operating-system family alone cannot establish support.

## Current status

| Component | Status | Notes |
| --- | --- | --- |
| Chrome on macOS | Primary | Main sender development target |
| Chrome on Linux | Experimental | Command CI is configured; only local macOS command tests are currently confirmed |
| Chrome on Windows | Experimental | Use `python tabtelly`; command CI is configured but has not run remotely yet |
| Hisense VIDAA legacy browser | Empirical prototype result | A Chromium-based VIDAA browser worked originally; current hardware retesting is unavailable |
| Other smart TV browsers | Unknown | Requires compatible WebRTC, codecs, and JavaScript |
| Multiple senders or receivers | Unsupported | One current sender and one receiver |
| Isolated guest networks | Unsupported | Direct peer reachability is required |

This table is deliberately conservative. Real-device reports are welcome through the compatibility issue form.

## Sender requirements

The sender uses `getDisplayMedia()` and WebRTC in desktop Chrome. Capture UI, tab audio, and Picture-in-Picture behavior are controlled by Chrome and the OS.

On macOS, window or screen sharing may require enabling Chrome under **System Settings → Privacy & Security → Screen & System Audio Recording**, then restarting Chrome. Tab sharing can behave differently.

Tab audio works only when Chrome offers it in the picker. Window audio is not promised.

## Receiver requirements

The TV browser needs WebRTC peer connections, a video codec shared with Chrome, a negotiated audio codec when audio is used, sufficient JavaScript/media APIs, and network access to the printed IPv4 address and port.

Firmware updates can change a browser engine without changing the TV product name. Record firmware and the user agent in reports.

## Network and content limits

The peers must connect directly over the LAN. There is no STUN or TURN fallback. Hotel, dormitory, corporate, and guest Wi-Fi often uses client isolation, making TabTelly unsupported. Pairing does not make public Wi-Fi safe; see [Security](../SECURITY.md).

Chrome decides what `getDisplayMedia()` can capture. DRM-protected content may appear blank, omit audio, or refuse capture. TabTelly does not bypass those restrictions.

Quality presets are targets rather than guarantees. Resolution, frame rate, bitrate, delay, and stability vary with Chrome, Wi-Fi conditions, and the TV decoder.

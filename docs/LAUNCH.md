# Launch copy

These drafts describe the experimental `0.1.0` release without implying broad hardware validation. The repository URL is https://github.com/jckceo/tabtelly; review each draft against the actual release status before posting.

## GitHub description

Cast a Chrome tab with audio to a compatible TV browser over local Wi-Fi.

Suggested topics: `webrtc`, `screen-sharing`, `smart-tv`, `chrome`, `python`, `local-network`, `vidaa`

Use the locally drawn [social preview](../assets/social-preview.svg) as the source for the repository social card. Upload the exported `assets/social-preview.png` in GitHub settings; it is a brand graphic, not an app screenshot.

## Release

**Title:** TabTelly 0.1.0 — first experimental release

**Notes:**

TabTelly sends a Chrome tab or window to a compatible smart TV browser over direct local WebRTC. The TV opens a URL and pairs with a six-digit code; there is no receiver app, account, cloud service, STUN, or TURN relay.

This first experimental release includes a portable command interface, pairing and role authentication, local diagnostics, quality presets, and a receiver designed with legacy TV browsers in mind. macOS with desktop Chrome is the primary sender. Linux and Windows are experimental, and current real-TV retesting is limited.

Read the compatibility and security notes before trying it. TabTelly is not AirPlay or Chromecast, isolated guest networks are unsupported, and protected media may refuse browser capture.

https://github.com/jckceo/tabtelly

## Hacker News

**Title:**

```text
Show HN: TabTelly – cast a Chrome tab to a TV browser over local WebRTC
```

**Post:**

```text
I built TabTelly after trying to cast a MacBook browser tab to what I assumed was an Android-based hotel TV. The device turned out to be a Hisense VIDAA television, and its built-in browser was the useful integration point.

TabTelly runs a Python standard-library server on the computer, captures a user-selected Chrome tab with getDisplayMedia(), and sends it directly to the TV browser over WebRTC. There is no TV app, account, cloud relay, STUN, or TURN. The receiver pairs with a short code; WebRTC media is encrypted, while local HTTP signaling means it should only be used on a trusted LAN.

It is an experimental 0.1.0 release. macOS Chrome is the primary sender, compatibility depends heavily on the TV browser, and I do not currently have the original hardware available for a fresh release test.

https://github.com/jckceo/tabtelly
```

## Reddit

Choose a relevant community, read its current rules, and adjust title and flair before posting. Do not cross-post indiscriminately.

**Title:**

```text
I made an experimental tool that casts a Chrome tab to a smart TV browser over local WebRTC
```

**Body:**

```text
TabTelly is a small open-source experiment for TVs with a capable browser but no casting path your computer can use. Run it on the computer, open the printed URL on the TV, enter a six-digit code, and choose a Chrome tab to share.

Media travels directly over WebRTC. The Python server only serves pages and relays signaling, with no pip dependencies or cloud service. It is not AirPlay/Chromecast and it cannot bypass DRM.

The sender is primarily developed on macOS Chrome. Linux and Windows are experimental, and TV support depends on the exact browser and firmware, so real-device reports are especially useful.

https://github.com/jckceo/tabtelly
```

## X

```text
TabTelly 0.1.0 casts a Chrome tab with audio to a compatible TV browser over local Wi-Fi. No TV app, account, or cloud relay. Experimental: macOS Chrome is primary; TV support varies.
https://github.com/jckceo/tabtelly
```

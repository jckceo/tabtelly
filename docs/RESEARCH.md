# Product naming, competition, and search positioning

Research date: **2026-10-19**

This is a point-in-time product and naming review, not trademark clearance. Search results, package names, domains, and legal rights can change. Before a public launch, run a professional trademark search in the intended countries and recheck the chosen handles.

## Recommendation

Use **TabTelly** as the product name and **`tabtelly`** as the repository slug.

Recommended one-line description:

> Cast a Chrome tab with audio from your Mac to a compatible TV browser over local Wi-Fi.

Recommended short positioning:

> TabTelly turns a compatible smart-TV browser into a receiver for one Chrome tab and its audio. A small Python server on the Mac serves the pages and relays signaling; the media travels peer-to-peer over the local network with WebRTC. There is no cloud service or TV app, and the TV does not need to support Google Cast or AirPlay.

The name works because “Tab” identifies the source and “Telly” identifies the destination. It is short, pronounceable, memorable, and avoids suggesting compatibility with a proprietary casting protocol. The coined name should carry the brand; descriptive copy should carry search discovery.

### Naming checks

The checks below were performed on 2026-10-19:

| Candidate | Finding | Decision |
|---|---|---|
| **TabTelly** | A [GitHub repository-name search](https://github.com/search?q=tabtelly&type=repositories) returned no repository matches. Exact-name web searches returned no identifiable software product. npm and PyPI JSON endpoints returned 404. | **Recommend.** Distinctive in the reviewed software namespace. |
| TabCast | GitHub returned 20 repository-name matches. Most significantly, [`steefvw/tabcast`](https://github.com/steefvw/tabcast) is already a browser-to-browser WebRTC tab-sharing project. [`mat-sz/tabcast`](https://github.com/mat-sz/tabcast) also uses the name for a JavaScript library. | Reject. The collision is direct in both name and function. |
| TabBeam | GitHub returned an exact repository-name match, [`davletovb/TabBeam`](https://github.com/davletovb/TabBeam). | Reject. Clearer than a coined name, but already occupied and less distinctive. |
| BrowserBeam | Browserbeam is an existing browser-automation product with public SDK repositories such as [`browserbeam-mcp`](https://github.com/nyku/browserbeam-mcp). | Reject. Strong product collision in an adjacent browser category. |
| TabSpan | An active [TabSpan Chrome extension](https://chromewebstore.google.com/detail/tabspan-cross-window-tab/fakbifeeblnopdhicpmhhmcdhmefphjp) uses the name for tab management. | Reject. Browser-category collision. |
| TabLoom | The name is used by multiple tab-management products and a current [PyPI project](https://pypi.org/project/tabloom/). | Reject. Crowded and semantically associated with tab organization rather than casting. |
| TabFerry | GitHub has [`ownCoder/tabferry-site`](https://github.com/ownCoder/tabferry-site); the name also implies moving tabs rather than live media. | Do not prefer. Some collision and weaker product meaning. |

These are practical collision checks, not a conclusion about registration or trademark rights. No domain purchase, package reservation, account creation, or repository creation was performed.

## The product category and story

The useful story is concrete:

> A MacBook is in a hotel room with a smart TV. The TV has a browser, but it does not expose a usable Google Cast or AirPlay receiver. TabTelly uses the capability both devices already share—the browser—to put one Chrome tab and its audio on the TV over local Wi-Fi.

That origin gives the project a sharper purpose than generic “screen sharing.” The primary job is **watch or present one browser tab on a nearby TV that has a compatible browser but no compatible native casting receiver**.

The current implementation supports this message:

- Chrome on macOS captures a user-selected tab or window with `getDisplayMedia()`.
- The receiver is a page in the TV's built-in browser; there is no TV-side installation.
- A Python standard-library HTTP server serves both pages and relays long-poll signaling.
- Audio and video travel directly between the browsers over WebRTC on the LAN; the server does not relay the media.
- No hosted account, public signaling service, STUN service, or TURN service is part of the current design.
- The historical prototype was tested on a Hisense VIDAA television whose browser reported Chromium 111 and compatible WebRTC codecs. Those observations still inform the receiver design, but the release candidate needs a fresh hardware retest after the pairing, authentication, and branding changes.

The browser must ask the user which surface to share each time. The W3C Screen Capture specification requires fresh user choice and allows browsers to omit an audio track even when audio is requested. That makes “one click with no picker” and universal audio support invalid promises. See the [W3C Screen Capture specification](https://www.w3.org/TR/screen-capture/) and [MDN's `getDisplayMedia()` reference](https://developer.mozilla.org/en-US/docs/Web/API/MediaDevices/getDisplayMedia).

### Honest compatibility boundary

Use **“a compatible TV browser”**, never “any TV” or “any browser.” A receiver needs enough HTML/JavaScript support, WebRTC, a mutually supported video codec, LAN reachability, and workable autoplay/full-screen behavior. The prototype was validated on the specific VIDAA/Chromium receiver documented in this repository; release-candidate hardware validation is pending, and the project has not been validated across all TV brands or hotel networks.

Hotel and guest Wi-Fi networks often isolate clients. ScreenStream documents the same general limitation: devices can be on the same guest network and still be unable to connect directly. TabTelly cannot bypass that network policy. See [ScreenStream's local-mode notes](https://github.com/dkrivoruchko/ScreenStream/blob/master/README.md#local-mode-mjpeg).

“Local-only” describes the intended network path; it is not itself an authentication or security claim. The current server pairs the receiver with a rate-limited code, authorizes signaling by role and current peer ID, and restricts sender/admin credentials to loopback. Signaling still uses plain HTTP, so a suitably positioned LAN peer or network operator may observe or interfere with it. WebRTC requires SRTP protection for media, as specified by [IETF RFC 8834](https://www.rfc-editor.org/rfc/rfc8834.html). Describe the product as designed for a trusted LAN; do not call arbitrary public Wi-Fi safe or imply that pairing makes signaling confidential.

## Competitive landscape

### Native casting systems

| Option | What the primary source says | Gap TabTelly addresses |
|---|---|---|
| Google Cast from Chrome | Google supports casting a Chrome tab or screen, but requires a Chromecast-family device, Google TV Streamer, or a TV with Google Cast. See [Google Chrome Help](https://support.google.com/chrome/answer/3228332). | A TV browser can be the receiver when the TV has no Google Cast receiver. |
| AirPlay | Apple documents Mac-to-TV streaming/mirroring through an Apple TV or compatible smart TV on the same network. See [Apple's Mac AirPlay guide](https://support.apple.com/en-euro/guide/mac-help/mchld7e543a0/mac/27). | A compatible TV browser can be used when the television does not offer a usable AirPlay receiver. |

The wording should be “works without a Google Cast or AirPlay receiver,” not “replaces Chromecast/AirPlay.” The native systems have broader device integration, discovery, and platform support.

### Browser-receiver products

| Product | Factual scope | Difference from TabTelly |
|---|---|---|
| [Deskreen](https://deskreen.com/) | A macOS/Windows/Linux Electron app using WebRTC to share a screen or application to browser receivers. It supports multiple receivers, second-screen and teleprompter use cases, and offline local Wi-Fi. Its site lists a 210 MB disk requirement and about 250 MB RAM for one session. The [source repository](https://github.com/pavlobu/deskreen) is open. | Deskreen is the closest mature adjacent product and is broader. TabTelly is narrower: one Chrome tab with its audio to one TV browser, driven by a small Python standard-library server rather than a general desktop app. |
| [ScreenStream](https://github.com/dkrivoruchko/ScreenStream) | An Android-origin screen-streaming app. Local mode uses a built-in HTTP server and MJPEG, is video-only, and needs no Internet. Global mode uses WebRTC, supports audio, and requires its public signaling service and an Internet connection. | The sender in TabTelly is Mac Chrome. Its local mode uses WebRTC for tab video and audio and does not use a public signaling service. |
| [`steefvw/tabcast`](https://github.com/steefvw/tabcast) | A small browser-to-browser WebRTC tab-sharing project with optional recording. Its documented default setup uses Node 18+, WebSockets, and an ngrok tunnel. | It makes “TabCast” unusable as a distinctive name. TabTelly focuses on a same-LAN TV browser, Python standard-library signaling, TV-oriented codec behavior, and no tunnel. |

TabTelly's credible differentiators are therefore:

1. **Tab-and-audio first:** the main flow deliberately targets a Chrome tab, including its audio, rather than generic desktop mirroring.
2. **TV browser as the receiver:** no native TV app, Cast receiver, AirPlay receiver, or dongle is part of the flow.
3. **Local media path:** peer-to-peer WebRTC on the LAN, with signaling on the Mac and no hosted service in the current design.
4. **Small operational footprint:** Python standard library plus static HTML/JavaScript; no Electron shell or installed TV component.
5. **Old-TV pragmatism:** receiver code and codec selection are tuned around the constraints observed in an actual VIDAA browser.

Avoid positioning “Python standard library” as a user benefit by itself. Translate it into the outcome: **small, inspectable, and no dependency installation for a Mac that already has the required Python runtime**. Also avoid claiming zero installation universally; the current machine needs Python and the user needs the project files.

## Search and repository strategy

### Search intent to target

Use the brand and a natural descriptive phrase together. “TabTelly” has no existing search demand; the descriptive copy must explain the problem in the title, first paragraph, repository description, headings, and image alt text.

Priority phrases:

1. `cast Chrome tab to TV`
2. `cast Chrome tab with audio`
3. `cast Mac to smart TV without Chromecast`
4. `cast MacBook to TV browser`
5. `screen share Mac to smart TV browser`
6. `local network screen sharing`
7. `WebRTC screen sharing local network`
8. `browser based screen casting`
9. `smart TV browser receiver`
10. `cast to Hisense VIDAA from Mac`

Secondary technical phrases for GitHub and developer audiences:

- `Python WebRTC signaling server`
- `peer-to-peer browser screen sharing`
- `WebRTC tab capture audio`
- `local WebRTC casting`
- `WebRTC without STUN or TURN`
- `Python standard library HTTP server`

Use `screen mirroring` only as a secondary discovery term. The product's strongest promise is sharing one tab; “mirroring” can imply the whole desktop and full native receiver integration.

### Ready-to-use metadata

GitHub repository name:

> `tabtelly`

GitHub description:

> Cast a Chrome tab with audio from a Mac to a compatible TV browser over local Wi-Fi using peer-to-peer WebRTC.

README title:

> TabTelly — cast a Chrome tab to a TV browser over local Wi-Fi

Web page title:

> TabTelly: Cast a Chrome Tab to a TV Browser

Meta description:

> Cast a Chrome tab with audio from your Mac to a compatible smart TV browser over local Wi-Fi. No Cast receiver, AirPlay receiver, cloud, or TV app.

Suggested GitHub topics:

> `webrtc`, `screen-sharing`, `tab-sharing`, `browser-casting`, `smart-tv`, `macos`, `chrome`, `python`, `local-network`, `peer-to-peer`, `audio-streaming`, `vidaa`

Suggested opening paragraph:

> TabTelly casts one Chrome tab and its audio from a Mac to a compatible smart-TV browser over local Wi-Fi. It is useful when a TV has a browser but no usable Google Cast or AirPlay receiver. Nothing is installed on the TV: open its browser to the Mac's local address, choose a Chrome tab, and the two browsers carry the media over peer-to-peer WebRTC.

### Claim guardrails

Prefer:

- “No cloud service in the current design.”
- “Media stays on the local peer-to-peer connection.”
- “No app is installed on the TV.”
- “No Google Cast or AirPlay receiver is required.”
- “The prototype was tested on one Hisense VIDAA TV; release-candidate hardware retest is pending, and other compatible TV browsers may work.”
- “Low latency in the documented test environment,” followed by the measured range and method.

Avoid:

- “Works on any smart TV/browser.”
- “Guaranteed to work on hotel Wi-Fi.”
- “Secure/private” without explaining the trusted-LAN boundary, paired role authentication, and unencrypted HTTP signaling surface.
- “Zero setup” or “zero installation.”
- “AirPlay,” “Chromecast,” or “Google Cast” in the product name or repository slug.
- “Open source” until a license is actually present and the repository is published.
- Absolute latency, quality, or hardware-decoding claims across untested televisions.

## Source notes

Primary sources reviewed on 2026-10-19:

- [Google Chrome Help: Cast from Chrome to your TV](https://support.google.com/chrome/answer/3228332)
- [Apple Support: Stream video and audio with AirPlay](https://support.apple.com/en-euro/guide/mac-help/mchld7e543a0/mac/27)
- [Deskreen product site](https://deskreen.com/) and [Deskreen source repository](https://github.com/pavlobu/deskreen)
- [ScreenStream source repository](https://github.com/dkrivoruchko/ScreenStream)
- [`steefvw/tabcast` source repository](https://github.com/steefvw/tabcast)
- [W3C Screen Capture specification](https://www.w3.org/TR/screen-capture/)
- [IETF RFC 8834: Media Transport and Use of RTP in WebRTC](https://www.rfc-editor.org/rfc/rfc8834.html)
- [Python `http.server` documentation](https://docs.python.org/3/library/http.server.html)
- [MDN `getDisplayMedia()` reference](https://developer.mozilla.org/en-US/docs/Web/API/MediaDevices/getDisplayMedia)

Repository and code-name searches were performed with GitHub Search and the GitHub Search API. General web searches plus npm and PyPI endpoint checks were used as secondary collision signals. Absence from those results is not proof that a name is legally available.

# Why TabTelly exists

TabTelly began with a practical problem: casting a MacBook browser tab to an Android-based hotel TV seemed as if it should be straightforward, but the expected path did not work.

Investigation changed the premise. The prototype television was actually a Hisense model running VIDAA, not Android TV. Its built-in browser, rather than a native casting protocol, provided the workable path: Chrome could capture a tab, WebRTC could carry the stream over the local network, and the TV browser could receive it without an installed app.

That discovery shaped the project. TabTelly does not try to become an AirPlay or Chromecast substitute. It combines browser capabilities already present on both ends:

- a Python standard-library server for local pages and signaling
- Chrome's `getDisplayMedia()` for user-approved capture
- WebRTC for encrypted peer-to-peer media on the LAN
- a browser-only receiver for televisions with compatible engines

The original test led to an implementation, but it does not prove broad device support. TV browsers vary by model and firmware, current hardware has not been available for a fresh release test, and hotel networks often block direct connections. Those limits are part of the project.

TabTelly is licensed under MIT so the approach can be inspected, reproduced, and improved through careful real-device reports.

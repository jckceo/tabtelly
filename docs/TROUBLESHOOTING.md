# Troubleshooting

Start with:

```bash
./tabtelly doctor
./tabtelly status
```

Use `python tabtelly ...` on Windows.

## The TV cannot open the receiver URL

1. Confirm the server is running.
2. Confirm both devices are on the same LAN.
3. Enter the printed URL exactly, including `http://` and the port.
4. Allow incoming connections for Python if the OS firewall asks.
5. Check whether a VPN or virtual adapter caused the wrong address.

If needed, restart with an IPv4 address assigned to the computer:

```bash
TABTELLY_LAN_IP=192.168.1.20 ./tabtelly restart
```

Guest and hotel Wi-Fi often blocks device-to-device traffic. Isolated networks are unsupported because TabTelly has no relay.

## The pairing code is rejected

- Use the current code from the running server.
- After a restart, reload both the sender and receiver, then enter the new code.
- Wait before retrying after repeated failures; attempts are rate limited.
- Confirm you reached the intended computer if several run TabTelly.

Never paste an active code into an issue or public log.

## Connected, but no source appears

- Open `http://localhost:<port>/send` in desktop Chrome.
- Ensure only one sender and receiver are active.
- Press **Cast a tab** and finish Chrome's share picker.
- Check `tabtelly log` for a browser capability or signaling error.

## Video freezes or becomes slow

- Keep the Picture-in-Picture controller open; closing it stops the cast.
- If unavailable, keep the sender page visible.
- Try a lower quality preset.
- Add `?cc=loss` to compare the experimental loss-oriented mode with Chrome's default GCC behavior.
- Try `?keepalive=1` as a fallback; results vary.
- Reduce local Wi-Fi congestion.

Presets and status estimates are diagnostic targets, not performance guarantees.

## Video works but audio does not

- Share a **Chrome tab**, not an application window.
- Enable tab audio in Chrome's picker when offered.
- Interact with the TV page once; some browsers require a gesture before playback.
- Confirm the source tab is audible.

Tab-audio capture varies by platform. Window audio is not promised. Protected content may block audio.

## Wrong address or busy port

Set `TABTELLY_LAN_IP` to a reachable IPv4 address assigned to the computer. Avoid VPN addresses unless the TV can route to them.

To choose another port:

```bash
TABTELLY_PORT=8091 ./tabtelly start
```

Runtime state is separated under `.run/<port>` unless `TABTELLY_RUNTIME_DIR` is set.

## Protected video is blank

This is expected for some DRM- or HDCP-protected media. TabTelly follows Chrome's restrictions and provides no bypass.

## Report a problem

Use the appropriate issue form. Include versions, TV user agent, `tabtelly doctor`, and the smallest useful redacted log excerpt. Remove addresses, pair codes, tokens, peer IDs, device names, and unrelated network details.

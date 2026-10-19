# Getting started

TabTelly shares a desktop Chrome tab with a compatible TV browser over the local network.

## Requirements

- Python 3.10 or later
- Desktop Google Chrome
- A TV browser with WebRTC support
- A LAN that allows direct connections between the computer and TV

The runtime has no Python package dependencies. macOS is the primary development platform; Linux and Windows are experimental.

## Get the files

Download the [source ZIP](https://github.com/jckceo/tabtelly/archive/refs/heads/main.zip) (or use **Code → Download ZIP** on the repository), extract it, and open a terminal in the extracted folder containing `server.py` and `tabtelly`. No installer or pip packages are required. On macOS/Linux, if your archive tool removed executable permissions, run `chmod +x tabtelly tabcast` or use `python3 tabtelly`.

## Start and pair

On macOS or Linux:

```bash
./tabtelly doctor
./tabtelly start
```

On Windows:

```powershell
python tabtelly doctor
python tabtelly start
```

Startup prints:

```text
Sender:    http://localhost:8090/send
Receiver:  http://<computer-lan-ip>:8090/
Pair code: <six digits>
```

If Chrome should not open automatically, add `--no-open` to `start`.

1. Open the TV's built-in browser and enter the receiver URL.
2. Enter the six-digit code printed in the terminal.
3. Open the sender URL in Chrome if it is not already open.
4. Choose **Cast a tab** and select a source in Chrome's picker.
5. For tab audio, enable Chrome's audio-sharing option when offered.

The code is temporary and attempts are rate limited. Run `tabtelly status` if either page does not appear connected.

## Keep the sender active

Keep the Document Picture-in-Picture controller open; closing it stops the cast. Some Chrome and OS combinations throttle capture when the sender is hidden. If the controller is unavailable, keep the sender page visible. Optional `?keepalive=1` is a fallback, not a guarantee.

## Manage the server

```bash
./tabtelly status
./tabtelly log
./tabtelly restart
./tabtelly stop
./tabtelly --version
```

`log` follows the current log; `Ctrl-C` stops following it without stopping the server. The legacy `./tabcast` wrapper accepts the same commands.

Every server start creates new sender, receiver, and administrative credentials plus a new pair code. After `restart`, reload the sender page, reload the TV page, and pair again. An existing media session is not preserved across a server restart.

## Configuration

Set variables before starting:

```bash
TABTELLY_PORT=8091 TABTELLY_LAN_IP=192.168.1.20 ./tabtelly start
```

PowerShell:

```powershell
$env:TABTELLY_PORT = "8091"
$env:TABTELLY_LAN_IP = "192.168.1.20"
python tabtelly start
```

| Variable | Default | Description |
| --- | --- | --- |
| `TABTELLY_PORT` | `8090` | TCP port for pages and signaling |
| `TABTELLY_BIND` | `0.0.0.0` | `0.0.0.0` for LAN use or `127.0.0.1` for local tests |
| `TABTELLY_LAN_IP` | auto-detected | IPv4 address advertised to the TV |
| `TABTELLY_RUNTIME_DIR` | `.run/<port>` | Per-port log and session-secret directory |

`TABCAST_PORT`, `TABCAST_BIND`, `TABCAST_LAN_IP`, and `TABCAST_RUNTIME_DIR` remain compatibility aliases. The `TABTELLY_*` value takes precedence when both names are set.

Use `TABTELLY_LAN_IP` when automatic selection chooses a VPN or virtual adapter. It must be assigned to the computer and reachable from the TV. `TABTELLY_BIND` accepts only `0.0.0.0` and `127.0.0.1`; loopback is useful for local tests but cannot serve a TV. Never expose or port-forward the server.

## Capture options

Quality presets are requested targets. Chrome and network conditions determine the delivered result. Tab audio is platform-dependent; window audio is not promised.

- `?cc=loss` enables the experimental loss-oriented mode. Chrome's normal GCC behavior is the default.
- `?keepalive=1` enables the optional background-throttling workaround.

Combine parameters with `&`, for example `http://localhost:8090/send?cc=loss&keepalive=1`. The sender's runtime token is injected into loopback-served HTML; it is never a query parameter.

Next: [Compatibility](COMPATIBILITY.md) · [Troubleshooting](TROUBLESHOOTING.md) · [Architecture](ARCHITECTURE.md)

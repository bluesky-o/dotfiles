#!/usr/bin/env python3
"""Choose a temporary Hyprland display layout using Rofi."""
import json
import subprocess
import fcntl
import os
from pathlib import Path
import socket
import sys
import time


def monitors():
    result = subprocess.run(
        ["hyprctl", "monitors", "all", "-j"],
        check=True, capture_output=True, text=True,
    )
    return json.loads(result.stdout)


def configure(name, *, disabled=False, mirror=""):
    # Connector names come from Hyprland, never from menu input.
    scale = "1.25" if name.startswith(("eDP-", "LVDS-", "DSI-")) else '"auto"'
    code = (
        "hl.monitor({output=" + json.dumps(name)
        + ', mode="preferred", position="auto", scale=' + scale
        + ", disabled=" + ("true" if disabled else "false")
        + ", mirror=" + json.dumps(mirror) + "})"
    )
    result = subprocess.run(
        ["hyprctl", "eval", code], check=True, capture_output=True, text=True,
    )
    if "error" in result.stdout.lower():
        raise RuntimeError(result.stdout.strip())


def apply(choice):
    outputs = monitors()  # Refresh after the menu, in case a cable changed.
    internal = next((m["name"] for m in outputs
                     if m["name"].startswith(("eDP-", "LVDS-", "DSI-"))), None)
    external = [m["name"] for m in outputs if m["name"] != internal]
    if not internal:
        raise RuntimeError("No internal display detected.")
    if choice != "Internal only" and not external:
        raise RuntimeError("Connect an external display first.")

    if choice == "Internal only":
        configure(internal)
        active = monitors()
        if not any(m["name"] == internal and not m.get("disabled", False) for m in active):
            raise RuntimeError("Internal display did not activate; keeping external displays enabled.")
        for name in external:
            configure(name, disabled=True)
    elif choice == "External only":
        for name in external:
            configure(name)
        active = monitors()
        if not any(m["name"] in external and not m.get("disabled", False) for m in active):
            raise RuntimeError("External display did not activate; keeping internal display enabled.")
        configure(internal, disabled=True)
    else:
        configure(internal)
        for name in external:
            configure(name, mirror=internal if choice == "Duplicate" else "")


def main():
    # Also start recovery for sessions that were already running when installed.
    # The watcher's lock makes this safe when autostart already launched it.
    log_dir = Path(os.environ.get("XDG_CACHE_HOME", str(Path.home() / ".cache")))
    log_dir.mkdir(parents=True, exist_ok=True)
    with open(log_dir / "display-recovery.log", "a") as log:
        subprocess.Popen(
            [sys.executable, str(Path(__file__).resolve()), "--watch"],
            stdin=subprocess.DEVNULL, stdout=log, stderr=log,
            start_new_session=True,
        )
    options = ["Internal only", "External only", "Extend", "Duplicate"]
    menu = subprocess.run(
        ["rofi", "-dmenu", "-i", "-no-custom", "-p", "Display mode",
         "-lines", "4"],
        input="\n".join(options), capture_output=True, text=True,
    )
    choice = menu.stdout.strip()
    if menu.returncode == 0 and choice in options:
        try:
            apply(choice)
        except (subprocess.CalledProcessError, ValueError, RuntimeError) as error:
            subprocess.run(["notify-send", "Display selector", str(error)], check=False)


def recover_internal():
    outputs = monitors()
    internal = [m for m in outputs
                if m["name"].startswith(("eDP-", "LVDS-", "DSI-"))]
    external = [m for m in outputs if m not in internal]
    if external:
        return
    for output in internal:
        if output.get("disabled", False):
            configure(output["name"])


def watch():
    """Recover after unplugging the last external output, including startup."""
    runtime = os.environ.get("XDG_RUNTIME_DIR")
    instance = os.environ.get("HYPRLAND_INSTANCE_SIGNATURE")
    if not runtime or not instance:
        raise RuntimeError("Run the display watcher inside your Hyprland session.")
    # A lock prevents duplicate watchers when manually starting after a reload.
    with open(Path(runtime) / ("display-recovery-" + instance + ".lock"), "w") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as events:
            events.connect(str(Path(runtime) / "hypr" / instance / ".socket2.sock"))
            events.settimeout(2)
            pending = b""
            next_check = 0.0
            while True:
                if time.monotonic() >= next_check:
                    try:
                        recover_internal()
                    except (subprocess.CalledProcessError, ValueError, RuntimeError) as error:
                        print("Display recovery:", error, file=sys.stderr, flush=True)
                    next_check = time.monotonic() + 2
                try:
                    chunk = events.recv(65536)
                except socket.timeout:
                    continue  # Also catches a disconnect during a menu switch.
                if not chunk:
                    return  # Compositor exited.
                pending += chunk
                lines = pending.split(b"\n")
                pending = lines.pop()
                if any(line.startswith((b"monitorremoved>>", b"monitorremovedv2>>"))
                       for line in lines):
                    next_check = 0.0


if __name__ == "__main__":
    if "--watch" in sys.argv:
        watch()
    else:
        main()

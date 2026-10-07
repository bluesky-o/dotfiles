#!/usr/bin/env python3
"""Choose a temporary Hyprland display layout using Rofi."""
import json
import subprocess


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


if __name__ == "__main__":
    main()

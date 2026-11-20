-------------------
---- AUTOSTART ----
-------------------

-- See https://wiki.hypr.land/Configuring/Basics/Autostart/

-- Autostart necessary processes (like notifications daemons, status bars, etc.)
-- Or execute your favorite apps at launch like this:
hl.on("hyprland.start", function()
    hl.exec_cmd("wl-paste --type text --watch cliphist store")
    hl.exec_cmd("wl-paste --type image --watch cliphist store")
    hl.exec_cmd("waybar")
    hl.exec_cmd("python3 ~/.config/hypr/scripts/display-menu.py --watch >> ~/.cache/display-recovery.log 2>&1")
    hl.exec_cmd("systemctl --user start hyprpolkitagent")
    hl.exec_cmd("swaybg -i ~/pics/wallpapers/window-girl.png -m fill")
end)
--
-- hl.on("hyprland.start", function ()
--   hl.exec_cmd(terminal)
--   hl.exec_cmd("nm-applet")
--   hl.exec_cmd("waybar & hyprpaper & firefox")
-- end)

# Dotfiles

Hyprland (Lua configuration), Waybar, and Rofi, managed with GNU Stow.

## First setup on this computer

```sh
sudo dnf install stow
cd ~/dotfiles
bash setup.sh
```

The setup script moves existing configurations into a timestamped backup
directory in your home directory, then links the repository configurations.
If Stow reports a conflict, the original configurations remain in the backup.

## Install on another computer

Clone this repository into `~/dotfiles`, install Stow and the applications,
then run `bash setup.sh`. Review the Hyprland monitor names and scale first.
The wallpaper referenced in Hyprland autostart is not included.

## Save changes

Editing files through `~/.config` edits their linked repository copies.

```sh
cd ~/dotfiles
git diff
git add hypr waybar rofi README.md setup.sh .gitignore
git commit -m "Update configuration"
git push
```

After adding files or pulling changes, refresh links with:

```sh
stow --restow --target="$HOME" hypr waybar rofi
```

To remove the managed links, run:

```sh
stow --delete --target="$HOME" hypr waybar rofi
```

Your original Rofi theme path currently includes `/home/green`; update it if
installing under another username. Required fonts include JetBrainsMono Nerd
Font Propo for Waybar and Montserrat for Rofi.

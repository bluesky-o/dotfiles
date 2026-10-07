#!/usr/bin/env bash
set -euo pipefail
command -v stow >/dev/null || { echo 'Install Stow first: sudo dnf install stow'; exit 1; }
repo_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
backup_dir="${HOME}/dotfiles-backup-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$backup_dir"
targets=(.config/hypr .config/waybar .config/rofi .local/share/rofi/themes/spotlight-dark.rasi)
for relative_path in "${targets[@]}"; do
    target_path="$HOME/$relative_path"
    if [[ -e "$target_path" || -L "$target_path" ]]; then
        # Keep existing Stow links when rerunning setup.
        if [[ -L "$target_path" && "$(readlink -f "$target_path")" == "$repo_dir/"* ]]; then
            continue
        fi
        mkdir -p "$backup_dir/$(dirname "$relative_path")"
        mv -- "$target_path" "$backup_dir/$relative_path"
    fi
done
stow --dir="$repo_dir" --target="$HOME" --simulate --verbose hypr waybar rofi
stow --dir="$repo_dir" --target="$HOME" --verbose hypr waybar rofi
echo "Setup complete. Original files are in: $backup_dir"

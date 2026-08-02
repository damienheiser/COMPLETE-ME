#!/bin/bash

HOOKS_DIR="$HOME/.complete-me/hooks"
REPO_DIR="/Users/hedon/Documents/Augments/Scripts and Automation/COMPLETE-ME"

echo "Creating hooks directory at $HOOKS_DIR..."
mkdir -p "$HOOKS_DIR"

# 1. ZSH
if [ -f "$REPO_DIR/scripts/zsh_hook.zsh" ]; then
    cp "$REPO_DIR/scripts/zsh_hook.zsh" "$HOOKS_DIR/zsh_hook.zsh"
    ZSH_RC="$HOME/.zshrc"
    if [ -f "$ZSH_RC" ]; then
        if ! grep -q "complete-me/hooks/zsh_hook.zsh" "$ZSH_RC"; then
            echo "Adding hook to $ZSH_RC..."
            echo -e "\n# COMPLETE-ME Hook\nsource \"$HOOKS_DIR/zsh_hook.zsh\"" >> "$ZSH_RC"
        else
            echo "ZSH hook already present in $ZSH_RC"
        fi
    fi
fi

# 2. BASH
if [ -f "$REPO_DIR/scripts/bash_hook.bash" ]; then
    cp "$REPO_DIR/scripts/bash_hook.bash" "$HOOKS_DIR/bash_hook.bash"
    BASH_RC="$HOME/.bashrc"
    # On macOS, bash sometimes uses .bash_profile
    [ ! -f "$BASH_RC" ] && [ -f "$HOME/.bash_profile" ] && BASH_RC="$HOME/.bash_profile"
    
    if [ -f "$BASH_RC" ]; then
        if ! grep -q "complete-me/hooks/bash_hook.bash" "$BASH_RC"; then
            echo "Adding hook to $BASH_RC..."
            echo -e "\n# COMPLETE-ME Hook\nsource \"$HOOKS_DIR/bash_hook.bash\"" >> "$BASH_RC"
        else
            echo "Bash hook already present in $BASH_RC"
        fi
    fi
fi

# 3. FISH
if [ -f "$REPO_DIR/scripts/fish_hook.fish" ]; then
    FISH_CONF_DIR="$HOME/.config/fish/conf.d"
    mkdir -p "$FISH_CONF_DIR"
    echo "Installing Fish hook to $FISH_CONF_DIR/complete_me.fish..."
    # Fish automatically sources everything in conf.d
    cp "$REPO_DIR/scripts/fish_hook.fish" "$FISH_CONF_DIR/complete_me.fish"
fi

echo "Hooks deployed successfully!"
echo "Please restart your shell or source your config file to enable COMPLETE-ME."

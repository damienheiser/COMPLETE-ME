#!/bin/bash

REPO_DIR="/Users/hedon/Documents/Augments/Scripts and Automation/COMPLETE-ME"
HOOKS_DIR="$HOME/.complete-me/hooks"

# ZSH hook template
zsh_hook() {
    cat << 'EOF'
_complete_me() {
    local cmd=$words[1]
    if (( $+commands[$cmd] )); then
        if [[ -S /tmp/complete-me.sock ]]; then
            echo "$cmd" | nc -U /tmp/complete-me.sock
            sleep 0.1
            if [[ -f ~/.cache/complete-me/zsh/source/$cmd.zsh ]]; then
                source ~/.cache/complete-me/zsh/source/$cmd.zsh
                _complete
            fi
        fi
    fi
    return 1
}
zstyle ':completion:*' completer _complete _ignored _approximate _complete_me
EOF
}

# Bash hook template
bash_hook() {
    cat << 'EOF'
_complete_me_bash() {
    local cmd="${COMP_WORDS[0]}"
    if type "$cmd" > /dev/null 2>&1; then
        if [[ -S /tmp/complete-me.sock ]]; then
            echo "$cmd" | nc -U /tmp/complete-me.sock
            sleep 0.1
            if [[ -f ~/.cache/complete-me/bash/$cmd ]]; then
                source ~/.cache/complete-me/bash/$cmd
            fi
        fi
    fi
}
complete -D -F _complete_me_bash
EOF
}

# Fish hook template
fish_hook() {
    cat << 'EOF'
function __complete_me_fish --on-event fish_prompt
    # Fish hook is slightly different; it checks on every prompt if completions exist for the last command
    # or we can bind to Tab. For now, we'll keep it simple.
end
EOF
}

echo "--- COMPLETE-ME Setup ---"

echo "1. Generating shell hooks..."
mkdir -p "$HOOKS_DIR"
zsh_hook > "$HOOKS_DIR/zsh_hook.zsh"
bash_hook > "$HOOKS_DIR/bash_hook.bash"
fish_hook > "$HOOKS_DIR/fish_hook.fish"

echo "2. Creating cache directories..."
mkdir -p ~/.cache/complete-me/{zsh/fpath,zsh/source,bash,fish}

echo "3. Installing launchd plist..."
cp "$REPO_DIR/com.user.complete-me.plist" ~/Library/LaunchAgents/
launchctl unload ~/Library/LaunchAgents/com.user.complete-me.plist 2>/dev/null
launchctl load ~/Library/LaunchAgents/com.user.complete-me.plist

echo "4. Deploying hooks to shell configs..."

# ZSH Deployment
ZSH_RC="$HOME/.zshrc"
if [ -f "$ZSH_RC" ]; then
    if ! grep -q "complete-me/hooks/zsh_hook.zsh" "$ZSH_RC"; then
        echo "   Adding hook to $ZSH_RC"
        echo -e "\n# COMPLETE-ME Hook\nsource \"$HOOKS_DIR/zsh_hook.zsh\"" >> "$ZSH_RC"
    fi
fi

# Bash Deployment
BASH_RC="$HOME/.bashrc"
[ ! -f "$BASH_RC" ] && [ -f "$HOME/.bash_profile" ] && BASH_RC="$HOME/.bash_profile"
if [ -f "$BASH_RC" ]; then
    if ! grep -q "complete-me/hooks/bash_hook.bash" "$BASH_RC"; then
        echo "   Adding hook to $BASH_RC"
        echo -e "\n# COMPLETE-ME Hook\nsource \"$HOOKS_DIR/bash_hook.bash\"" >> "$BASH_RC"
    fi
fi

# Fish Deployment
FISH_CONF_DIR="$HOME/.config/fish/conf.d"
if [ -d "$HOME/.config/fish" ]; then
    mkdir -p "$FISH_CONF_DIR"
    echo "   Installing Fish hook to $FISH_CONF_DIR/complete_me.fish"
    cp "$HOOKS_DIR/fish_hook.fish" "$FISH_CONF_DIR/complete_me.fish"
fi

echo "--- Setup Complete! ---"
echo "Please restart your shell or run 'source ~/.zshrc' (or equivalent) to activate COMPLETE-ME."

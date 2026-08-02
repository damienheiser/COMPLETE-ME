# COMPLETE-ME

A background service that automatically generates shell completions when a tab-completion miss occurs.

## Architecture

- **Daemon**: A background process that listens for completion miss events.
- **Shell Hooks**: Scripts for `zsh`, `bash`, and `fish` that trigger the daemon on a completion miss.
- **Analyzer**: A module that extracts possible arguments/commands from:
  - `-h`, `-?`, `--help`
  - `man` pages
  - Configuration files (`.conf`, `.yaml`)
- **Cache**: Stores generated completions to avoid re-parsing.

## Installation

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/user/COMPLETE-ME.git
    cd COMPLETE-ME
    ```

2.  **Run the setup script**:
    ```bash
    ./scripts/setup.sh
    ```
    This will:
    - Generate shell hooks for `zsh`, `bash`, and `fish`.
    - Create the cache directory `~/.cache/complete-me`.
    - Install the `launchd` plist for the daemon.

3.  **Start the daemon**:
    ```bash
    launchctl load ~/Library/LaunchAgents/com.user.complete-me.plist
    ```

4.  **Source the hooks**:
    Add the following to your shell config file:
    - **zsh**: `source /path/to/COMPLETE-ME/scripts/zsh_hook.zsh`
    - **bash**: `source /path/to/COMPLETE-ME/scripts/bash_hook.bash`
    - **fish**: `source /path/to/COMPLETE-ME/scripts/fish_hook.fish`

## How it works

When you press `<TAB>` for a command that has no completions defined, the shell hook catches the "miss" and sends the command name to the `complete-me` daemon. The daemon then:
- Analyzes the command's `--help`, `-h`, `-?`, and no-argument output.
- Scans `man` pages for the command and its configuration files.
- Identifies options (`-`, `--`) and subcommands.
- Generates a completion script and stores it in the cache.
- The shell hook then sources the new completions and re-triggers the completion attempt.

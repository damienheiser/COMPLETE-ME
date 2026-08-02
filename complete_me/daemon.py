import os
import socket
import sys
import threading
from analyzer import HelpAnalyzer

SOCKET_PATH = "/tmp/complete-me.sock"
CACHE_DIR = os.path.expanduser("~/.cache/complete-me")

class Daemon:
    def __init__(self):
        self.ensure_cache_dir()

    def ensure_cache_dir(self):
        os.makedirs(CACHE_DIR, exist_ok=True)
        for shell in ["zsh", "bash", "fish"]:
            os.makedirs(os.path.join(CACHE_DIR, shell), exist_ok=True)

    def generate_zsh(self, cmd, completions):
        # standard fpath file
        fpath_dir = os.path.join(CACHE_DIR, "zsh", "fpath")
        os.makedirs(fpath_dir, exist_ok=True)
        path = os.path.join(fpath_dir, f"_{cmd}")
        with open(path, "w") as f:
            f.write(f'#compdef {cmd}\n')
            f.write(f'_{cmd}() {{\n')
            f.write(f'    _arguments "1: :({ " ".join(completions) })" "*: :({ " ".join(completions) })"\n')
            f.write(f'}}\n')
            f.write(f'_{cmd} "$@"\n')

        # sourceable file for immediate use
        source_dir = os.path.join(CACHE_DIR, "zsh", "source")
        os.makedirs(source_dir, exist_ok=True)
        source_path = os.path.join(source_dir, f"{cmd}.zsh")
        with open(source_path, "w") as f:
            f.write(f'_{cmd}() {{\n')
            f.write(f'    _arguments "1: :({ " ".join(completions) })" "*: :({ " ".join(completions) })"\n')
            f.write(f'}}\n')
            f.write(f'compdef _{cmd} {cmd}\n')

    def generate_bash(self, cmd, completions):
        # bash completion file
        path = os.path.join(CACHE_DIR, "bash", cmd)
        with open(path, "w") as f:
            f.write(f'complete -W "{ " ".join(completions) }" {cmd}\n')

    def generate_fish(self, cmd, completions):
        # fish completion file
        path = os.path.join(CACHE_DIR, "fish", f"{cmd}.fish")
        with open(path, "w") as f:
            for comp in completions:
                f.write(f'complete -c {cmd} -a "{comp}"\n')

    def handle_request(self, command_name):
        print(f"Analyzing {command_name}...")
        analyzer = HelpAnalyzer(command_name)
        analyzer.analyze_help()
        completions = analyzer.get_completions()
        
        if completions:
            self.generate_zsh(command_name, completions)
            self.generate_bash(command_name, completions)
            self.generate_fish(command_name, completions)
            print(f"Generated completions for {command_name}")
        else:
            print(f"No completions found for {command_name}")

    def run(self):
        if os.path.exists(SOCKET_PATH):
            os.remove(SOCKET_PATH)
            
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
            s.bind(SOCKET_PATH)
            s.listen()
            print(f"Daemon listening on {SOCKET_PATH}")
            while True:
                conn, addr = s.accept()
                with conn:
                    data = conn.recv(1024)
                    if not data:
                        break
                    command_name = data.decode('utf-8').strip()
                    # Run analysis in a separate thread to keep daemon responsive
                    threading.Thread(target=self.handle_request, args=(command_name,)).start()

if __name__ == "__main__":
    daemon = Daemon()
    daemon.run()

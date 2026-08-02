import re
import subprocess
import shutil
import os

class ScriptAnalyzer:
    def __init__(self, script_path):
        self.script_path = script_path
        self.completions = set()

    def analyze(self):
        if not os.path.isfile(self.script_path):
            return
        
        try:
            with open(self.script_path, 'r', errors='ignore') as f:
                content = f.read()
            
            ext = os.path.splitext(self.script_path)[1]
            if ext == '.py':
                self.parse_python(content)
            elif ext in ['.sh', '.bash', '.zsh']:
                self.parse_shell(content)
            else:
                self.parse_generic(content)
        except Exception:
            pass

    def parse_python(self, content):
        # Match argparse: add_argument('--option', ...)
        argparse_regex = r"add_argument\s*\(\s*['\"](-{1,2}[a-zA-Z0-9_-]+)['\"]"
        for match in re.findall(argparse_regex, content):
            self.completions.add(match)
        
        # Match sys.argv checks: sys.argv[1] == 'command'
        argv_regex = r"sys\.argv\[\d+\]\s*==\s*['\"]([a-zA-Z0-9_-]+)['\"]"
        for match in re.findall(argv_regex, content):
            self.completions.add(match)

    def parse_shell(self, content):
        # Match getopts: getopts "abc:" opt
        getopts_regex = r'getopts\s+["\']([a-zA-Z0-9:]+)["\']'
        for match in re.findall(getopts_regex, content):
            for char in match:
                if char != ':':
                    self.completions.add(f"-{char}")
        
        # Match case $1 in ... )
        case_regex = r'^\s*([a-zA-Z0-9_-]+)\)'
        for match in re.findall(case_regex, content, re.MULTILINE):
            if match not in ["case", "esac"]:
                self.completions.add(match)

    def parse_generic(self, content):
        # Look for anything that looks like a flag or a command
        flags = re.findall(r'["\'](-{1,2}[a-zA-Z0-9_-]+)["\']', content)
        for flag in flags:
            self.completions.add(flag)

    def get_completions(self):
        return self.completions

class HelpAnalyzer:
    def __init__(self, command_name):
        self.command_name = command_name
        self.completions = set()

    def get_help_output(self, flag):
        try:
            return subprocess.check_output([self.command_name, flag], stderr=subprocess.STDOUT, timeout=2).decode('utf-8')
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
            return ""

    def analyze_help(self):
        # If it's a path to a script, use ScriptAnalyzer
        if "/" in self.command_name or self.command_name.endswith(('.sh', '.py', '.js', '.rb', '.pl')):
            script_path = os.path.abspath(self.command_name)
            if not os.path.exists(script_path):
                # Try finding it in PATH
                path_cmd = shutil.which(self.command_name)
                if path_cmd:
                    script_path = path_cmd
            
            s_analyzer = ScriptAnalyzer(script_path)
            s_analyzer.analyze()
            self.completions.update(s_analyzer.get_completions())

        flags = ["--help", "-h", "-?", ""]
        for flag in flags:
            output = self.get_help_output(flag) if flag else self.get_help_no_flag()
            if output:
                self.parse_output(output)
        
        # Also try man pages
        man_names = [self.command_name, f"{self.command_name}.conf", f"{self.command_name}.yaml"]
        for name in man_names:
            man_output = self.get_man_page(name)
            if man_output:
                self.parse_output(man_output)

    def get_help_no_flag(self):
        try:
            return subprocess.check_output([self.command_name], stderr=subprocess.STDOUT, timeout=2).decode('utf-8')
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
            return ""

    def get_man_page(self, name):
        if not shutil.which("man"):
            return ""
        try:
            # Use col -b to remove backspaces/formatting
            cmd = f"man {name} | col -b"
            return subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, timeout=2).decode('utf-8')
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            return ""

    def parse_output(self, text):
        # Match --long-option or -s (short option)
        # Also look for subcommands (words that aren't options)
        
        # Match options: -o, --option, --option=VALUE, --option <VALUE>
        option_regex = r'(?:^|\s)(-[a-zA-Z0-9]|--[a-z0-9-]+)(?:[=\s\[<])'
        matches = re.findall(option_regex, text)
        for match in matches:
            self.completions.add(match.strip())

        # Match subcommands (non-dashed words)
        # Often listed after "Commands:", "Subcommands:", "Available Commands:", "Usage: process_name COMMAND"
        
        # Look for "Usage: process_name COMMAND"
        usage_regex = fr'Usage:\s+{self.command_name}\s+([a-z][a-z0-9_-]+)'
        matches = re.findall(usage_regex, text, re.IGNORECASE)
        for match in matches:
            if match not in ["COMMAND", "ARGS", "OPTIONS"]:
                self.completions.add(match)

        lines = text.split('\n')
        in_commands_section = False
        for line in lines:
            if any(marker in line.lower() for marker in ["commands:", "subcommands:", "available commands:", "usage:", "options:"]):
                in_commands_section = True
                # If it's the "options:" section, we don't want to pick up subcommands here
                is_options_section = "options:" in line.lower()
                continue
            
            if in_commands_section:
                # Look for subcommands (usually at start of line with indent, no dash)
                # Avoid words that are all caps (usually section headers)
                match = re.match(r'^\s+([a-z][a-z0-9_-]+)\s+', line)
                if match:
                    cmd = match.group(1)
                    if not cmd.startswith('-') and not is_options_section:
                        self.completions.add(cmd)
                elif line.strip() == "":
                    pass
                elif re.match(r'^[A-Z]', line) and not any(m in line for m in ["Commands", "Subcommands"]):
                    in_commands_section = False
        
        # General non-dashed word extraction from lines that look like command lists
        for line in lines:
            # Match lines like:   add        Add a new thing
            match = re.match(r'^\s{2,4}([a-z]{2,15})\s{2,}.+', line)
            if match:
                word = match.group(1)
                # Filter out some common false positives
                if word not in ["the", "this", "that", "usage", "options", "commands"]:
                    self.completions.add(word)

    def get_completions(self):
        return sorted(list(self.completions))

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        analyzer = HelpAnalyzer(cmd)
        analyzer.analyze_help()
        print("\n".join(analyzer.get_completions()))

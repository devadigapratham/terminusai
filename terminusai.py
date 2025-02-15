#!/usr/bin/env python3
import os
import subprocess
import re
import sys
import json
from pathlib import Path
import ollama  

try:
    import spacy
    nlp = spacy.load("en_core_web_sm")
except Exception:
    nlp = None

APP_NAME = "TerminusAI"
VERSION = "1.0.0"  
CONFIG_PATH = Path.home() / ".config/terminusai/config.json"
HISTORY_FILE = Path.home() / ".config/terminusai/history.json"

ASCII_ART = r"""
___________                  .__
\__    ___/__________  _____ |__| ____  __ __  ______
  |    |_/ __ \_  __ \/     \|  |/    \|  |  \/  ___/
  |    |\  ___/|  | \/  Y Y  \  |   |  \  |  /\___ \
  |____| \___  >__|  |__|_|  /__|___|  /____//____  >
             \/            \/        \/           \/ 
"""

def load_config():
    default_config = {
        "model": "llama3.2:3b",
        "safe_mode": True,
        "confirm_execution": True,
        "history_size": 10,
        "enable_colors": True,
        "allow_harmful_commands": False,
        "custom_workflows": []  # List of dicts with "pattern" and "command"
    }
    try:
        with open(CONFIG_PATH) as f:
            return {**default_config, **json.load(f)}
    except Exception:
        return default_config

def save_history(history):
    HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(HISTORY_FILE, "w") as f:
            json.dump(history, f, indent=2)
    except Exception as e:
        print(f"Error saving history: {e}")

def load_history():
    if HISTORY_FILE.exists():
        try:
            with open(HISTORY_FILE) as f:
                return json.load(f)
        except Exception:
            return []
    return []

def record_history(query, command, config):
    history = load_history()
    entry = {"query": query, "command": command}
    history.append(entry)
    # Keep history size limited
    max_size = config.get("history_size", 10)
    history = history[-max_size:]
    save_history(history)

def display_history():
    history = load_history()
    if not history:
        print("No history yet.")
        return
    print("\nCommand History:")
    for i, entry in enumerate(history, 1):
        print(f"{i}. Query: {entry['query']}\n   Command: {entry['command']}\n")

def display_art():
    config = load_config()
    if config.get('enable_colors'):
        print("\033[1;36m")  # Cyan color
        print(ASCII_ART)
        print(f"\033[1;34mVersion {VERSION}\033[0m")
        print("\033[3;90mSafe terminal command assistant powered by local LLMs\033[0m\n")
    else:
        print(f"{APP_NAME} v{VERSION} - Your terminal AI assistant\n")

def enhanced_parse_query(query):
    """If spaCy is available, use it to perform basic intent extraction."""
    if nlp:
        doc = nlp(query)
        # For demonstration, we simply return tokens in lower case.
        return [token.text.lower() for token in doc]
    return query.lower()

def get_command_from_llm(query, config):
    prompt = f"""You are a CLI command expert. The user is asking for a command to: {query}

If the query involves file operations, ensure that hidden files and directories are considered.
If the query involves a specific directory, use the FULL ABSOLUTE PATH to that directory.
Respond STRICTLY with ONLY the command to execute in bash/zsh.
NO explanations, NO markdown, ONLY the command itself."""
    try:
        response = ollama.chat(
            model=config['model'],
            messages=[
                {"role": "system", "content": "You are a helpful assistant that provides terminal commands."},
                {"role": "user", "content": prompt}
            ]
        )
        return response['message']['content'].strip()
    except Exception as e:
        print(f"\033[1;31mError from LLM: {e}\033[0m")
        return None

def clean_command(command):
    """Clean the command by removing markdown code blocks, backticks, and extra whitespace."""
    command = re.sub(r'```(?:bash|sh)?\n(.*?)\n```', r'\1', command, flags=re.DOTALL)
    command = command.replace('`', '')
    return command.strip()

def resolve_placeholder_path(command):
    """
    Look for placeholder paths in the command such as /path/to/OOAD and replace them
    with the actual absolute path if the directory exists relative to the current working directory.
    """
    pattern = re.compile(r"/path/to/([^\s/]+)")
    def replace_match(match):
        dirname = match.group(1)
        candidate = os.path.join(os.getcwd(), dirname)
        return os.path.abspath(candidate)
    return pattern.sub(replace_match, command)

def is_command_harmful(command):
    """
    Checks for dangerous command patterns.
    Currently, it flags commands that include 'rm -rf' targeting root directories.
    """
    harmful_patterns = [
        r"sudo\s+rm\s+-rf\s+/\b",
        r"rm\s+-rf\s+/\b",
        r"rm\s+-rf\s+~/?\b"
    ]
    for pattern in harmful_patterns:
        if re.search(pattern, command):
            return True
    return False

def find_directory_by_name(target_name, start_dir):
    """
    Recursively search for directories in start_dir whose name matches target_name (case-insensitive).
    Returns a list of absolute paths.
    """
    matches = []
    for root, dirs, _ in os.walk(start_dir):
        for d in dirs:
            if d.lower() == target_name.lower():
                matches.append(os.path.join(root, d))
    return matches

def specialized_file_agent(query, config):
    """Agent for operations involving hidden files."""
    lower_query = query.lower()
    if "find" in lower_query and "hidden" in lower_query:
        match = re.search(r"in\s+([^\s]+)", query, re.IGNORECASE)
        abs_dir = os.path.abspath(match.group(1)) if match else os.getcwd()
        return f"find {abs_dir} -type f -name '.*'"
    elif "list" in lower_query and "hidden" in lower_query:
        match = re.search(r"in\s+([^\s]+)", query, re.IGNORECASE)
        abs_dir = os.path.abspath(match.group(1)) if match else os.getcwd()
        return f"ls -laR {abs_dir}"
    elif "create" in lower_query and "hidden" in lower_query and "file" in lower_query:
        match = re.search(r"create\s+hidden\s+file\s+([^\s]+)", query, re.IGNORECASE)
        if match:
            filename = match.group(1).strip()
            if not filename.startswith("."):
                filename = "." + filename
            abs_path = os.path.join(os.getcwd(), filename)
            return f"touch {abs_path}"
    elif "delete" in lower_query and "hidden" in lower_query and "file" in lower_query:
        match = re.search(r"delete\s+hidden\s+file\s+([^\s]+)", query, re.IGNORECASE)
        if match:
            filename = match.group(1).strip()
            if not filename.startswith("."):
                filename = "." + filename
            abs_path = os.path.join(os.getcwd(), filename)
            return f"rm {abs_path}"
    return get_command_from_llm(query, config)

def specialized_directory_agent(query, config):
    """Agent for directory-related queries."""
    lower_query = query.lower()
    home = str(Path.home())
    if "find" in lower_query and "directory" in lower_query:
        match = re.search(r"find\s+([^\s]+)\s+directory", query, re.IGNORECASE)
        if match:
            dir_name = match.group(1)
            return f"find {home} -type d -iname '{dir_name}'"
    elif "list" in lower_query and "directory" in lower_query:
        match = re.search(r"list.*files.*in\s+([^\s]+)\s+directory", query, re.IGNORECASE)
        if match:
            dir_name = match.group(1)
            candidates = find_directory_by_name(dir_name, home)
            if candidates:
                return f"ls -A {candidates[0]}"
            else:
                return get_command_from_llm(query, config)
    return get_command_from_llm(query, config)

def specialized_networking_agent(query, config):
    """Agent for networking-related queries."""
    lower = query.lower()
    if "ping" in lower:
        match = re.search(r"ping\s+([^\s]+)", query)
        target = match.group(1) if match else "google.com"
        return f"ping -c 4 {target}"
    elif "traceroute" in lower or "trace route" in lower:
        match = re.search(r"traceroute\s+([^\s]+)", query)
        target = match.group(1) if match else "google.com"
        return f"traceroute {target}"
    return get_command_from_llm(query, config)

def specialized_system_agent(query, config):
    """Agent for system monitoring queries."""
    lower = query.lower()
    if "cpu" in lower or "memory" in lower:
        return "top -b -n 1"
    elif "disk" in lower:
        return "df -h"
    return get_command_from_llm(query, config)

def specialized_package_agent(query, config):
    """Agent for package management queries."""
    lower = query.lower()
    if "install" in lower:
        # Example: "install vim using apt"
        match = re.search(r"install\s+([^\s]+).*apt", query, re.IGNORECASE)
        if match:
            package = match.group(1)
            return f"sudo apt-get install -y {package}"
        match = re.search(r"install\s+([^\s]+).*yum", query, re.IGNORECASE)
        if match:
            package = match.group(1)
            return f"sudo yum install -y {package}"
        match = re.search(r"install\s+([^\s]+).*pip", query, re.IGNORECASE)
        if match:
            package = match.group(1)
            return f"pip install {package}"
    return get_command_from_llm(query, config)

def specialized_docker_agent(query, config):
    """Agent for Docker-related queries."""
    lower = query.lower()
    if "list containers" in lower:
        return "docker ps -a"
    elif "list images" in lower:
        return "docker images"
    elif "start container" in lower:
        match = re.search(r"start container\s+([^\s]+)", query, re.IGNORECASE)
        if match:
            container = match.group(1)
            return f"docker start {container}"
    return get_command_from_llm(query, config)

def apply_custom_workflows(query, config):
    """If custom workflows are defined in config, check for a matching pattern."""
    workflows = config.get("custom_workflows", [])
    for wf in workflows:
        pattern = wf.get("pattern")
        cmd_template = wf.get("command")
        if pattern and cmd_template:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                # Replace placeholders {1}, {2}, etc.
                command = cmd_template
                for i, group in enumerate(match.groups(), start=1):
                    command = command.replace("{" + str(i) + "}", group)
                # Also support {home} and {user}
                command = command.replace("{home}", str(Path.home()))
                command = command.replace("{user}", os.environ.get("USER", "user"))
                return command
    return None

def select_agent(query, config):
    """
    Selects an appropriate agent based on the query.
    Checks custom workflows first, then extended agents based on keywords.
    """
    custom = apply_custom_workflows(query, config)
    if custom:
        return custom

    lower_query = enhanced_parse_query(query)
    # Check for history request
    if isinstance(lower_query, str) and lower_query.strip() == "history":
        display_history()
        return None

    # Extended agent selection based on keywords:
    if isinstance(lower_query, list):
        lower_text = " ".join(lower_query)
    else:
        lower_text = lower_query

    if "hidden" in lower_text:
        return specialized_file_agent(query, config)
    if "directory" in lower_text and ("find" in lower_text or "list" in lower_text):
        return specialized_directory_agent(query, config)
    if "ping" in lower_text or "traceroute" in lower_text:
        return specialized_networking_agent(query, config)
    if "cpu" in lower_text or "memory" in lower_text or "disk" in lower_text:
        return specialized_system_agent(query, config)
    if "install" in lower_text:
        return specialized_package_agent(query, config)
    if "docker" in lower_text:
        return specialized_docker_agent(query, config)
    # Default: use the LLM
    return get_command_from_llm(query, config)

def execute_command(command, config):
    if config.get('safe_mode'):
        print("\033[1;33mSafe mode enabled - Simulating execution:\033[0m")
        print(f"\033[1;37m{command}\033[0m\n")
        return
    try:
        result = subprocess.run(command, shell=True, check=True,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.stdout:
            print(f"\n\033[1;32mOutput:\033[0m\n{result.stdout}")
        if result.stderr:
            print(f"\n\033[1;31mErrors:\033[0m\n{result.stderr}")
    except subprocess.CalledProcessError as e:
        print(f"\n\033[1;31mCommand failed with error code {e.returncode}:\033[0m\n{e.stderr}")

# ----- Main Loop -----
def main():
    config = load_config()
    display_art()

    try:
        while True:
            try:
                query = input("\033[1;35m» Terminal Query: \033[0m").strip()
                if not query:
                    continue
                if query.lower() in ['exit', 'quit', 'q']:
                    print("\n\033[1;36mExiting TerminusAI... Goodbye! 👋\033[0m")
                    break
                # Special command to show history
                if query.lower() == "history":
                    display_history()
                    continue

                command = select_agent(query, config)
                if not command:
                    continue
                command = clean_command(command)
                command = resolve_placeholder_path(command)
                print(f"\n\033[1;34mSuggested command:\033[0m\n\033[1;37m{command}\033[0m")
                if is_command_harmful(command) and not config.get("allow_harmful_commands", False):
                    print("\033[1;31mWarning: Detected potentially harmful command.\033[0m")
                    confirm = input("\n\033[1;33mProceed with execution? [y/N/s(simulate)] \033[0m").lower()
                    if confirm == 'y':
                        execute_command(command, {**config, 'safe_mode': False})
                    elif confirm == 's':
                        execute_command(command, {**config, 'safe_mode': True})
                    else:
                        print("Command execution cancelled.")
                    continue
                if config.get('confirm_execution'):
                    confirm = input("\n\033[1;33mExecute command? [y/N/s(simulate)] \033[0m").lower()
                    if confirm == 'y':
                        execute_command(command, config)
                    elif confirm == 's':
                        execute_command(command, {**config, 'safe_mode': True})
                else:
                    execute_command(command, config)
                record_history(query, command, config)
            except KeyboardInterrupt:
                print("\n\033[1;36mType 'exit' to quit or enter a new query\033[0m")
    except EOFError:
        print("\n\033[1;36m\nExiting TerminusAI... Safe computing! 🛡️\033[0m")

if __name__ == "__main__":
    main()

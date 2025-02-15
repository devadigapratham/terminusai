# TerminusAI 
**TerminusAI** is a powerful, CLI-based terminal command assistant powered by local LLMs. It transforms natural language queries into precise terminal commands, helping you work more efficiently and safely from the command line. This is especially useful for those who are new to Linux commands.

## Features

- **Natural Language to Command Conversion:**  
  Converts your plain English queries into bash/zsh commands using a local LLM (via Ollama).

- **Enhanced Command Parsing:**  
  Optionally leverages spaCy for advanced intent recognition.

- **Agents:**  
  Specialized agents handle:
  - **File & Directory Operations:** Find, list, create, or delete hidden files and search for directories recursively.
  - **Networking:** Generate commands for pinging hosts and performing traceroute.
  - **System Monitoring:** Quickly check CPU/memory usage (`top`) and disk space (`df`).
  - **Package Management:** Supports commands for installing packages using `apt`, `yum`, or `pip`.
  - **Docker Integration:** List Docker containers/images or start containers.

- **Custom Workflows:**  
  Define custom command templates in your configuration (e.g., backups, scripts, etc.) using regex patterns and placeholders.

- **Command History:**  
  Automatically saves and displays your command history for quick reference.

- **Safety Mode:**  
  Simulates execution of commands to prevent accidental harmful operations. The system also detects potentially dangerous commands (e.g., `rm -rf /`) and warns you before execution.


## Installation

### Prerequisites
- **Python 3:** Ensure you have Python 3 installed (preferably Python 3.7 or later).
- **Optional:** [spaCy](https://spacy.io/) for enhanced parsing.
- **Ollama:** Make sure the `ollama` package is installed and configured.

### Steps

1. **Clone the Repository:**

   ```bash
   git clone https://github.com/yourusername/TerminusAI.git
   cd TerminusAI
   ```

2. **Install Dependencies:**

   Install the required packages using pip:

   ```bash
   pip install ollama
   pip install spacy  # Optional: for enhanced parsing
   # If using spaCy, download the English model:
   python -m spacy download en_core_web_sm
   ```

3. **Make the Script Executable and Add It to Your PATH:**

   ```bash
   chmod +x terminusai.py
   sudo ln -s "$(pwd)/terminusai.py" /usr/local/bin/terminusai
   ```

   This allows you to run TerminusAI from anywhere by simply typing:

   ```bash
   terminusai
   ```

4. **Configuration:**

   Create a configuration file at `~/.config/terminusai/config.json`. If the directory does not exist, create it:

   ```bash
   mkdir -p ~/.config/terminusai
   ```

   Then create a file named `config.json` with your preferred settings. For example:

   ```json
   {
     "model": "llama3.2:3b",
     "safe_mode": true,
     "confirm_execution": true,
     "history_size": 10,
     "enable_colors": true,
     "allow_harmful_commands": false,
     "custom_workflows": [
       {
         "pattern": "backup (.*)",
         "command": "tar -czvf /backup/{1}.tar.gz {1}"
       }
     ]
   }
   ```

5. **Run TerminusAI:**

   Launch TerminusAI by running:

   ```bash
   terminusai
   ```

   You can now type your queries at the prompt. Type `history` to view your command history or `exit` to quit.

### Optional: Integration with Terminal Emulators

#### For Kitty Users
Add the following line to your Kitty configuration file (`~/.config/kitty/kitty.conf`) to launch TerminusAI with a key binding:

```conf
# Launch TerminusAI as an overlay with Ctrl+Shift+T
map ctrl+shift+t launch --type=overlay terminusai
```

#### For Alacritty Users
Alacritty does not directly support launching external commands via key bindings. Instead, you can:
- Set up a global keyboard shortcut in your desktop environment that runs `terminusai`, or
- Use a terminal multiplexer like tmux and add a key binding in your `~/.tmux.conf`:

  ```tmux
  # Bind Ctrl+b T to launch TerminusAI in a new tmux window
  bind-key T new-window -n "TerminusAI" "terminusai"
  ```


## Usage Examples

- **Find Hidden Files:**

  ```bash
  find hidden files in /tmp
  ```

  *Expected Command:*  
  `find /tmp -type f -name '.*'`

- **List Files in a Directory:**

  ```bash
  list all the files in ooad directory
  ```

  *Expected Command (if found):*  
  `ls -A /home/prathamesh/study/Sem6/OOAD`

- **Networking:**

  ```bash
  ping example.com
  ```

  *Expected Command:*  
  `ping -c 4 example.com`

- **Package Management:**

  ```bash
  install vim using apt
  ```

  *Expected Command:*  
  `sudo apt-get install -y vim`

- **Custom Workflow Example (Backup):**

  ```bash
  backup project
  ```

  *Expected Command:*  
  `tar -czvf /backup/project.tar.gz project`

## Contributing

Contributions are welcome! Feel free to open issues or pull requests. Please follow the standard GitHub flow and include tests/documentation for new features.

## License

This project is licensed under the [MIT License](LICENSE).

## Acknowledgements

- Powered by [Ollama](https://ollama.ai/) for local LLM interactions.
- Optionally using [spaCy](https://spacy.io/) for enhanced NLP parsing.

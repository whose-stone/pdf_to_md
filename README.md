Here is the updated README. I have split the Install and Usage sections to include specific commands for Windows (PowerShell), macOS, and Linux, and added the appropriate config paths for each.

# pdf_to_md
Local executable that converts a PDF into Markdown while preserving layout readability, and replaces images with LLM-generated descriptions.
## Features- Converts PDF pages to Markdown with page separators.- Preserves readable structure using heading/list heuristics.- Rewrites image regions as markdown image lines with generated descriptions.- Uses OpenAI-compatible LLM APIs (cloud or local) through config.
- Supports offline extraction mode (`--no-llm`).
## Install### Windows (PowerShell)```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```
### MacOS / Linux```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
## ConfigThe program reads config from:
- **Windows:** `%APPDATA%\pdf_to_md\config.toml`
- **MacOS/Linux:** `~/.config/pdf_to_md/config.toml` (or `$XDG_CONFIG_HOME/pdf_to_md/config.toml`)

You can also pass `--config /path/to/config.toml`.

Example `config.toml`:```toml
[llm]
base_url = "https://api.openai.com/v1"
model = "gpt-4o-mini"
api_key_env = "OPENAI_API_KEY"
temperature = 0.0
max_tokens = 800
enabled = true
describe_images = true
postprocess_layout = true
```
## Usage### Windows```powershell
python .\pdf_to_md.py \path\to\file.pdf
```
### MacOS / Linux```bash
./pdf_to_md.py /path/to/file.pdf
```

**Optional arguments:**
- `-o /path/to/output.md`: Specify output path.
- `--config /path/to/config.toml`: Use a specific config file.
- `--no-llm`: Skip image description and layout post-processing.
## Building the Executable### Windows```powershell
pip install pyinstaller
pyinstaller --onefile --add-data "examples;examples" pdf_to_md.py
```
*Note: The separator for `--add-data` is a semicolon (`;`) on Windows.*
### MacOS / Linux```bash
pip install pyinstaller
pyinstaller --onefile --add-data "examples:examples" pdf_to_md.py
```
*Note: The separator for `--add-data` is a colon (`:`) on Unix.*

Do you want to add a section for troubleshooting common PyInstaller errors or is this version ready to go?


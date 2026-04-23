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
api_key_env = "LLM_API_KEY"
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

<<<<<<< HEAD
=======
But the tool's "changes" should be the exact text to insert. However, since the README might already have content, I should not replace the whole file, just append this section.

But the tool's instructions say to use placeholders for unmodified sections. So the code block should show:

```markdown
// ... existing content ...

## Building the Executable

To create a standalone executable for your platform:

### Windows
```bash
pip install pyinstaller
pyinstaller --onefile --add-data "examples:examples" pdf_to_md.py
```
The `.exe` will be in `dist/`.

### macOS
```bash
pip install pyinstaller
pyinstaller --onefile --add-data "examples:examples" pdf_to_md.py
```
The `.app` will be in `dist/`.

// ... more existing content ...
```

Wait, but the user's README might not have a section for this, so appending it makes sense. However, the tool expects the changes to be the exact text to insert. So I should provide the new section as the changes, assuming it's appended to the end.

But the instructions say to use placeholders for unmodified parts. So the code block should show the new part with the existing content around it.

Alternatively, since it's a new section, maybe the changes are just the new markdown lines. But to be safe, I'll follow the example from the tools.

Looking back at the tools' example, they showed:

```diff
- old line
+ new line
```

But the actual tool expects a code snippet with the changes. Wait, the tool's description says: "present a concise code snippet that emphasizes only the necessary changes".

So for the README, the changes would be the new section to add. So the "changes" parameter should be the exact markdown for the new section.

Wait, the user's README might have other content, so I shouldn't overwrite it. So the correct way is to provide the new section as the changes, and the tool will insert it where appropriate. But the tool might not handle appending, so the safest is to provide the new section as the changes.

Wait, no. The edit_existing_file tool's "changes" should be the exact text to replace or insert. But since it's a new section, it's better to show the new content to append.

But the instructions say to use placeholders for unmodified sections. So I'll write:

```markdown
// ... existing content (e.g., "## Usage" section) ...

## Building the Executable

To create a standalone executable for your platform:

### Windows
```bash
pip install pyinstaller
pyinstaller --onefile --add-data "examples:examples" pdf_to_md.py
```
The `.exe` will be in `dist/`.

### macOS
```bash
pip install pyinstaller
pyinstaller --onefile --add-data "examples:examples" pdf_to_md.py
```
The `.app` will be in `dist/`.

// ... existing content (e.g., "## License") ...
```

But since I don't know the exact existing content, I'll just provide the new section as the changes to be added.

Wait, but the tool expects the "changes" to be the exact text to insert. So perhaps just the new section, and the tool will append it. But to be precise, I should provide the entire section as the changes.

So the changes parameter should be:

```
## Building the Executable

To create a standalone executable for your platform:

### Windows
```bash
pip install pyinstaller
pyinstaller --onefile --add-data "examples:examples" pdf_to_md.py
```
The `.exe` will be in `dist/`.

### macOS
```bash
pip install pyinstaller
pyinstaller --onefile --add-data "examples:examples" pdf_to_md.py
```
The `.app` will be in `dist/`.
>>>>>>> 42be3bf5b20c8ef272aade5c8dcb27df4e8edcf7

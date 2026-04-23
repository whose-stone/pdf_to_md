# pdf_to_md

Local executable that converts a PDF into Markdown while preserving layout readability, and replaces images with LLM-generated descriptions.

## Features

- Converts PDF pages to Markdown with page separators.
- Preserves readable structure using heading/list heuristics.
- Rewrites image regions as markdown image lines with generated descriptions.
- Uses OpenAI-compatible LLM APIs (cloud or local) through config.
- Supports offline extraction mode (`--no-llm`).

## Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Config

The program reads config from:

- `$XDG_CONFIG_HOME/pdf_to_md/config.toml`, or
- `~/.config/pdf_to_md/config.toml`

You can also pass `--config /path/to/config.toml`.

Example config:

```toml
[llm]
# Any OpenAI-compatible endpoint.
# Cloud example: https://api.openai.com/v1
# Local example (Ollama/OpenWebUI/vLLM): http://localhost:11434/v1
base_url = "https://api.openai.com/v1"

# Use any model available at your endpoint.
model = "gpt-4.1-mini"

# Key source; useful for switching providers without editing this file.
api_key_env = "OPENAI_API_KEY"

temperature = 0.0
max_tokens = 800
enabled = true
describe_images = true
postprocess_layout = true
```

## Usage

```bash
./pdf_to_md.py /path/to/file.pdf
```

Output defaults to `/path/to/file.md`.

Optional arguments:

```bash
./pdf_to_md.py /path/to/file.pdf -o /path/to/output.md
./pdf_to_md.py /path/to/file.pdf --config /path/to/config.toml
./pdf_to_md.py /path/to/file.pdf --no-llm
```

## Notes

- Image descriptions require a model/API that supports vision-style chat input.
- If image description fails, a fallback message is inserted in the markdown.

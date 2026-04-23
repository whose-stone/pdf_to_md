#!/usr/bin/env python3
"""Convert PDF files to readable Markdown using an LLM-configurable workflow."""

from __future__ import annotations

import argparse
import base64
import os
import re
import statistics
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib  # type: ignore


@dataclass
class LLMConfig:
    model: str
    base_url: str = "https://api.openai.com/v1"
    api_key: str | None = None
    temperature: float = 0.0
    max_tokens: int = 800
    enabled: bool = True
    describe_images: bool = True
    postprocess_layout: bool = True


def default_config_path() -> Path:
    xdg = os.environ.get("XDG_CONFIG_HOME")
    if xdg:
        return Path(xdg) / "pdf_to_md" / "config.toml"
    return Path.home() / ".config" / "pdf_to_md" / "config.toml"


def load_config(path: Path | None) -> LLMConfig:
    cfg_path = path or default_config_path()
    if not cfg_path.exists():
        return LLMConfig(
            model=os.environ.get("PDF_TO_MD_MODEL", "gpt-4.1-mini"),
            base_url=os.environ.get("PDF_TO_MD_BASE_URL", "https://api.openai.com/v1"),
            api_key=os.environ.get("OPENAI_API_KEY"),
        )

    with cfg_path.open("rb") as f:
        data = tomllib.load(f)

    llm = data.get("llm", {})
    api_key_env = llm.get("api_key_env", "OPENAI_API_KEY")
    return LLMConfig(
        model=llm.get("model", os.environ.get("PDF_TO_MD_MODEL", "gpt-4.1-mini")),
        base_url=llm.get("base_url", os.environ.get("PDF_TO_MD_BASE_URL", "https://api.openai.com/v1")),
        api_key=os.environ.get(api_key_env, llm.get("api_key")),
        temperature=float(llm.get("temperature", 0.0)),
        max_tokens=int(llm.get("max_tokens", 800)),
        enabled=bool(llm.get("enabled", True)),
        describe_images=bool(llm.get("describe_images", True)),
        postprocess_layout=bool(llm.get("postprocess_layout", True)),
    )


def chat_completion(config: LLMConfig, messages: list[dict[str, Any]], max_tokens: int | None = None) -> str:
    import requests
    if not config.enabled:
        raise RuntimeError("LLM is disabled in config.")

    if not config.api_key and "localhost" not in config.base_url and "127.0.0.1" not in config.base_url:
        raise RuntimeError("Missing API key for non-local endpoint.")

    payload = {
        "model": config.model,
        "messages": messages,
        "temperature": config.temperature,
        "max_tokens": max_tokens or config.max_tokens,
    }

    headers = {"Content-Type": "application/json"}
    if config.api_key:
        headers["Authorization"] = f"Bearer {config.api_key}"

    endpoint = config.base_url.rstrip("/") + "/chat/completions"
    response = requests.post(endpoint, json=payload, headers=headers, timeout=90)
    response.raise_for_status()
    data = response.json()
    return data["choices"][0]["message"]["content"].strip()


def clean_line(text: str) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    return text


def classify_block(text: str, size: float) -> str:
    if not text:
        return ""
    if re.match(r"^\s*([\-\*•]|\d+[\.)])\s+", text):
        return text
    if size >= 20:
        return f"# {text}"
    if size >= 16:
        return f"## {text}"
    if size >= 13 and len(text) < 120:
        return f"### {text}"
    return text


def extract_page_markdown(page: Any) -> tuple[str, list[bytes]]:
    data = page.get_text("dict")
    blocks = sorted(data.get("blocks", []), key=lambda b: (b["bbox"][1], b["bbox"][0]))

    lines: list[str] = []
    images: list[bytes] = []

    for block in blocks:
        btype = block.get("type", 0)

        if btype == 1:
            img_data = block.get("image")
            if isinstance(img_data, (bytes, bytearray)):
                images.append(bytes(img_data))
            lines.append("[[IMAGE_PLACEHOLDER]]")
            continue

        block_lines = block.get("lines", [])
        if not block_lines:
            continue

        span_sizes: list[float] = []
        fragments: list[str] = []
        for line in block_lines:
            for span in line.get("spans", []):
                raw = span.get("text", "")
                if raw:
                    fragments.append(raw)
                    span_sizes.append(float(span.get("size", 11)))

        text = clean_line(" ".join(fragments))
        if not text:
            continue

        size = statistics.mean(span_sizes) if span_sizes else 11
        lines.append(classify_block(text, size))

    markdown = "\n\n".join(l for l in lines if l)
    markdown = re.sub(r"\n{3,}", "\n\n", markdown)
    return markdown.strip(), images


def describe_image(config: LLMConfig, img_data: bytes, page_num: int, image_num: int) -> str:
    if not config.enabled or not config.describe_images:
        return f"![Image {image_num} on page {page_num}](Image description disabled)"

    b64 = base64.b64encode(img_data).decode("ascii")
    prompt = (
        "Describe this image for markdown conversion from a PDF. "
        "Keep it factual, concise (1-3 sentences), and avoid guessing."
    )
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}},
            ],
        }
    ]

    try:
        description = chat_completion(config, messages, max_tokens=180)
        return f"![Image {image_num} on page {page_num}]({description})"
    except Exception as exc:
        return f"![Image {image_num} on page {page_num}](Unable to describe image: {exc})"


def refine_markdown(config: LLMConfig, page_md: str, page_num: int) -> str:
    if not config.enabled or not config.postprocess_layout:
        return page_md

    prompt = (
        "You are cleaning OCR-like PDF text into Markdown. "
        "Preserve all facts, do not add information, and improve readability with headings, lists, and tables "
        "only when clearly present in the text. Return markdown only."
    )
    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": f"Page {page_num} raw markdown:\n\n{page_md}"},
    ]
    try:
        return chat_completion(config, messages)
    except Exception:
        return page_md


def convert_pdf(pdf_path: Path, config: LLMConfig) -> str:
    import fitz  # PyMuPDF

    doc = fitz.open(pdf_path)
    full_output: list[str] = []

    for idx, page in enumerate(doc, start=1):
        page_md, images = extract_page_markdown(page)

        for image_idx, img in enumerate(images, start=1):
            placeholder = "[[IMAGE_PLACEHOLDER]]"
            if placeholder in page_md:
                page_md = page_md.replace(placeholder, describe_image(config, img, idx, image_idx), 1)

        page_md = refine_markdown(config, page_md, idx)
        full_output.append(f"<!-- Page {idx} -->\n\n{page_md}".strip())

    return "\n\n---\n\n".join(full_output).strip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Convert a PDF into readable Markdown with optional LLM post-processing.")
    parser.add_argument("pdf_path", type=Path, help="Path to the source PDF file")
    parser.add_argument("-o", "--output", type=Path, help="Output markdown file path (default: same name with .md)")
    parser.add_argument("--config", type=Path, help="Path to TOML config file")
    parser.add_argument("--no-llm", action="store_true", help="Disable LLM calls (for offline extraction)")
    args = parser.parse_args()

    if not args.pdf_path.exists():
        print(f"Error: file not found: {args.pdf_path}", file=sys.stderr)
        return 1

    cfg = load_config(args.config)
    if args.no_llm:
        cfg.enabled = False

    out_path = args.output or args.pdf_path.with_suffix(".md")

    try:
        markdown = convert_pdf(args.pdf_path, cfg)
    except Exception as exc:
        print(f"Conversion failed: {exc}", file=sys.stderr)
        return 1

    out_path.write_text(markdown, encoding="utf-8")
    print(f"Saved markdown to: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Tkinter GUI for pdf_to_md. Lets the user pick input/output folders,
configure the LLM API URL and key, and save a profile locally."""

from __future__ import annotations

import json
import os
import queue
import sys
import threading
import traceback
from dataclasses import asdict
from pathlib import Path
from tkinter import BooleanVar, StringVar, Tk, filedialog, messagebox, ttk
import tkinter as tk

import pdf_to_md


APP_NAME = "pdf_to_md"
PROFILE_FILENAME = "profile.json"


def profile_dir() -> Path:
    appdata = os.environ.get("APPDATA")
    if appdata:
        return Path(appdata) / APP_NAME
    return Path.home() / ".config" / APP_NAME


def profile_path() -> Path:
    return profile_dir() / PROFILE_FILENAME


DEFAULT_PROFILE: dict = {
    "input_dir": "",
    "output_dir": "",
    "base_url": "https://api.openai.com/v1",
    "api_key": "",
    "model": "gpt-4.1-mini",
    "temperature": 0.0,
    "max_tokens": 800,
    "enabled": True,
    "describe_images": True,
    "postprocess_layout": True,
}


def load_profile() -> dict:
    path = profile_path()
    if not path.exists():
        return dict(DEFAULT_PROFILE)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return dict(DEFAULT_PROFILE)
    merged = dict(DEFAULT_PROFILE)
    merged.update({k: v for k, v in data.items() if k in DEFAULT_PROFILE})
    return merged


def save_profile(data: dict) -> Path:
    path = profile_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return path


class App:
    def __init__(self, root: Tk) -> None:
        self.root = root
        root.title("PDF to Markdown Converter")
        root.geometry("720x620")
        root.minsize(640, 560)

        profile = load_profile()

        self.input_dir = StringVar(value=profile["input_dir"])
        self.output_dir = StringVar(value=profile["output_dir"])
        self.base_url = StringVar(value=profile["base_url"])
        self.api_key = StringVar(value=profile["api_key"])
        self.model = StringVar(value=profile["model"])
        self.temperature = StringVar(value=str(profile["temperature"]))
        self.max_tokens = StringVar(value=str(profile["max_tokens"]))
        self.enabled = BooleanVar(value=profile["enabled"])
        self.describe_images = BooleanVar(value=profile["describe_images"])
        self.postprocess_layout = BooleanVar(value=profile["postprocess_layout"])
        self.show_key = BooleanVar(value=False)

        self.log_queue: "queue.Queue[str]" = queue.Queue()
        self.worker: threading.Thread | None = None

        self._build_ui()
        self.root.after(100, self._drain_log)

    def _build_ui(self) -> None:
        pad = {"padx": 8, "pady": 4}
        frame = ttk.Frame(self.root, padding=12)
        frame.pack(fill="both", expand=True)
        frame.columnconfigure(1, weight=1)

        # Folders
        folders = ttk.LabelFrame(frame, text="Folders", padding=10)
        folders.grid(row=0, column=0, columnspan=3, sticky="ew", **pad)
        folders.columnconfigure(1, weight=1)

        ttk.Label(folders, text="Input folder:").grid(row=0, column=0, sticky="w", **pad)
        ttk.Entry(folders, textvariable=self.input_dir).grid(row=0, column=1, sticky="ew", **pad)
        ttk.Button(folders, text="Browse…", command=self._pick_input).grid(row=0, column=2, **pad)

        ttk.Label(folders, text="Output folder:").grid(row=1, column=0, sticky="w", **pad)
        ttk.Entry(folders, textvariable=self.output_dir).grid(row=1, column=1, sticky="ew", **pad)
        ttk.Button(folders, text="Browse…", command=self._pick_output).grid(row=1, column=2, **pad)

        # LLM settings
        llm = ttk.LabelFrame(frame, text="LLM Settings", padding=10)
        llm.grid(row=1, column=0, columnspan=3, sticky="ew", **pad)
        llm.columnconfigure(1, weight=1)

        ttk.Label(llm, text="API Base URL:").grid(row=0, column=0, sticky="w", **pad)
        ttk.Entry(llm, textvariable=self.base_url).grid(row=0, column=1, columnspan=2, sticky="ew", **pad)

        ttk.Label(llm, text="API Key:").grid(row=1, column=0, sticky="w", **pad)
        self.api_entry = ttk.Entry(llm, textvariable=self.api_key, show="*")
        self.api_entry.grid(row=1, column=1, sticky="ew", **pad)
        ttk.Checkbutton(llm, text="Show", variable=self.show_key, command=self._toggle_key_visibility).grid(
            row=1, column=2, sticky="w", **pad
        )

        ttk.Label(llm, text="Model:").grid(row=2, column=0, sticky="w", **pad)
        ttk.Entry(llm, textvariable=self.model).grid(row=2, column=1, columnspan=2, sticky="ew", **pad)

        ttk.Label(llm, text="Temperature:").grid(row=3, column=0, sticky="w", **pad)
        ttk.Entry(llm, textvariable=self.temperature, width=10).grid(row=3, column=1, sticky="w", **pad)

        ttk.Label(llm, text="Max tokens:").grid(row=4, column=0, sticky="w", **pad)
        ttk.Entry(llm, textvariable=self.max_tokens, width=10).grid(row=4, column=1, sticky="w", **pad)

        ttk.Checkbutton(llm, text="Enable LLM calls", variable=self.enabled).grid(
            row=5, column=0, columnspan=3, sticky="w", **pad
        )
        ttk.Checkbutton(llm, text="Describe images", variable=self.describe_images).grid(
            row=6, column=0, columnspan=3, sticky="w", **pad
        )
        ttk.Checkbutton(llm, text="Postprocess layout", variable=self.postprocess_layout).grid(
            row=7, column=0, columnspan=3, sticky="w", **pad
        )

        # Action buttons
        actions = ttk.Frame(frame)
        actions.grid(row=2, column=0, columnspan=3, sticky="ew", **pad)
        actions.columnconfigure(0, weight=1)

        ttk.Button(actions, text="Save profile", command=self._on_save_profile).grid(row=0, column=0, sticky="w")
        self.convert_btn = ttk.Button(actions, text="Convert", command=self._on_convert)
        self.convert_btn.grid(row=0, column=1, sticky="e")

        # Progress
        progress_frame = ttk.Frame(frame)
        progress_frame.grid(row=3, column=0, columnspan=3, sticky="ew", **pad)
        progress_frame.columnconfigure(0, weight=1)
        self.progress_var = tk.DoubleVar(value=0)
        self.progress_bar = ttk.Progressbar(
            progress_frame, variable=self.progress_var, maximum=100, mode="determinate"
        )
        self.progress_bar.grid(row=0, column=0, sticky="ew")
        self.progress_label = ttk.Label(progress_frame, text="Idle")
        self.progress_label.grid(row=1, column=0, sticky="w", pady=(2, 0))

        # Log area
        log_frame = ttk.LabelFrame(frame, text="Log", padding=6)
        log_frame.grid(row=4, column=0, columnspan=3, sticky="nsew", **pad)
        frame.rowconfigure(4, weight=1)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)

        self.log = tk.Text(log_frame, height=10, wrap="word", state="disabled")
        self.log.grid(row=0, column=0, sticky="nsew")
        scroll = ttk.Scrollbar(log_frame, orient="vertical", command=self.log.yview)
        scroll.grid(row=0, column=1, sticky="ns")
        self.log.configure(yscrollcommand=scroll.set)

        self._log(f"Profile path: {profile_path()}")

    def _toggle_key_visibility(self) -> None:
        self.api_entry.configure(show="" if self.show_key.get() else "*")

    def _pick_input(self) -> None:
        path = filedialog.askdirectory(title="Select input folder", initialdir=self.input_dir.get() or None)
        if path:
            self.input_dir.set(path)

    def _pick_output(self) -> None:
        path = filedialog.askdirectory(title="Select output folder", initialdir=self.output_dir.get() or None)
        if path:
            self.output_dir.set(path)

    def _collect_profile(self) -> dict | None:
        try:
            temperature = float(self.temperature.get())
        except ValueError:
            messagebox.showerror("Invalid input", "Temperature must be a number.")
            return None
        try:
            max_tokens = int(self.max_tokens.get())
        except ValueError:
            messagebox.showerror("Invalid input", "Max tokens must be an integer.")
            return None

        return {
            "input_dir": self.input_dir.get().strip(),
            "output_dir": self.output_dir.get().strip(),
            "base_url": self.base_url.get().strip(),
            "api_key": self.api_key.get(),
            "model": self.model.get().strip(),
            "temperature": temperature,
            "max_tokens": max_tokens,
            "enabled": self.enabled.get(),
            "describe_images": self.describe_images.get(),
            "postprocess_layout": self.postprocess_layout.get(),
        }

    def _on_save_profile(self) -> None:
        data = self._collect_profile()
        if data is None:
            return
        try:
            path = save_profile(data)
        except Exception as exc:
            messagebox.showerror("Save failed", f"Could not save profile:\n{exc}")
            return
        self._log(f"Saved profile to {path}")
        messagebox.showinfo("Saved", f"Profile saved to:\n{path}")

    def _on_convert(self) -> None:
        if self.worker and self.worker.is_alive():
            messagebox.showinfo("Busy", "A conversion is already running.")
            return

        data = self._collect_profile()
        if data is None:
            return

        input_dir = Path(data["input_dir"])
        output_dir = Path(data["output_dir"])
        if not input_dir.is_dir():
            messagebox.showerror("Missing folder", f"Input folder does not exist:\n{input_dir}")
            return
        if not data["output_dir"]:
            messagebox.showerror("Missing folder", "Please choose an output folder.")
            return

        cfg = pdf_to_md.LLMConfig(
            model=data["model"],
            base_url=data["base_url"],
            api_key=data["api_key"] or None,
            temperature=data["temperature"],
            max_tokens=data["max_tokens"],
            enabled=data["enabled"],
            describe_images=data["describe_images"],
            postprocess_layout=data["postprocess_layout"],
        )

        self.convert_btn.configure(state="disabled", text="Converting…")
        self.worker = threading.Thread(
            target=self._run_conversion, args=(input_dir, output_dir, cfg), daemon=True
        )
        self.worker.start()

    def _run_conversion(self, input_dir: Path, output_dir: Path, cfg) -> None:
        try:
            pdfs = sorted(p for p in input_dir.iterdir() if p.is_file() and p.suffix.lower() == ".pdf")
            if not pdfs:
                self._log(f"No PDFs found in {input_dir}")
                self._set_progress(0, 1, "No PDFs found")
                return

            import fitz

            page_counts: dict[Path, int] = {}
            total_pages = 0
            for pdf in pdfs:
                try:
                    with fitz.open(pdf) as doc:
                        page_counts[pdf] = doc.page_count
                        total_pages += doc.page_count
                except Exception as exc:
                    self._log(f"  Could not open {pdf.name} to count pages: {exc}")
                    page_counts[pdf] = 0

            output_dir.mkdir(parents=True, exist_ok=True)
            self._log(f"Found {len(pdfs)} PDF(s), {total_pages} page(s). Writing to {output_dir}")
            self._set_progress(0, max(total_pages, 1), f"Starting {len(pdfs)} PDF(s)…")

            completed_pages = 0
            failures = 0
            for pdf_idx, pdf in enumerate(pdfs, start=1):
                out_path = output_dir / (pdf.stem + ".md")
                self._log(f"[{pdf_idx}/{len(pdfs)}] Converting {pdf.name} -> {out_path.name}")
                base = completed_pages

                def on_page(idx: int, total: int, _pdf=pdf, _base=base) -> None:
                    self._set_progress(
                        _base + idx,
                        max(total_pages, 1),
                        f"[{pdf_idx}/{len(pdfs)}] {_pdf.name}: page {idx}/{total}",
                    )

                try:
                    markdown = pdf_to_md.convert_pdf(pdf, cfg, on_page=on_page)
                    out_path.write_text(markdown, encoding="utf-8")
                    self._log(f"  OK: {out_path}")
                except Exception as exc:
                    failures += 1
                    self._log(f"  FAILED: {exc}")

                completed_pages += page_counts.get(pdf, 0)
                self._set_progress(completed_pages, max(total_pages, 1), f"Completed {pdf_idx}/{len(pdfs)}")

            if failures:
                self._log(f"Done with {failures} failure(s).")
                self._set_progress(total_pages, max(total_pages, 1), f"Done — {failures} failure(s)")
            else:
                self._log("Done.")
                self._set_progress(total_pages, max(total_pages, 1), "Done")
        except Exception:
            self._log("Unexpected error:\n" + traceback.format_exc())
            self._set_progress(0, 1, "Error — see log")
        finally:
            self.root.after(0, self._reset_convert_button)

    def _set_progress(self, current: float, maximum: float, status: str) -> None:
        def apply() -> None:
            self.progress_bar.configure(maximum=maximum)
            self.progress_var.set(current)
            self.progress_label.configure(text=status)

        self.root.after(0, apply)

    def _reset_convert_button(self) -> None:
        self.convert_btn.configure(state="normal", text="Convert")

    def _log(self, message: str) -> None:
        self.log_queue.put(message)

    def _drain_log(self) -> None:
        try:
            while True:
                msg = self.log_queue.get_nowait()
                self.log.configure(state="normal")
                self.log.insert("end", msg + "\n")
                self.log.see("end")
                self.log.configure(state="disabled")
        except queue.Empty:
            pass
        self.root.after(100, self._drain_log)


def main() -> int:
    root = Tk()
    App(root)
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

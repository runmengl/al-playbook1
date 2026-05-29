#!/usr/bin/env python3
"""
One-click GUI launcher for the AI Playbook Policy Document Finder.

Run:
    python policy_finder_launcher.py
"""

from __future__ import annotations

import os
import subprocess
import threading
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, scrolledtext


PROJECT_DIR = Path(__file__).resolve().parent
SCRIPT_NAME = "ai_playbook_policy_document_finder.py"
RUNS_DIR = PROJECT_DIR / "runs"
QUICK_COMMAND = [
    "python",
    SCRIPT_NAME,
    "--quick",
    "--max-results",
    "3",
]


class PolicyFinderLauncher(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("AI Playbook Policy Document Finder")
        self.geometry("820x520")
        self.minsize(680, 420)
        self.process_running = False

        self._build_ui()

    def _build_ui(self) -> None:
        button_frame = tk.Frame(self, padx=12, pady=12)
        button_frame.pack(fill=tk.X)

        self.run_button = tk.Button(
            button_frame,
            text="Run Quick Demo",
            command=self.run_quick_demo,
            width=18,
        )
        self.run_button.pack(side=tk.LEFT, padx=(0, 8))

        self.open_button = tk.Button(
            button_frame,
            text="Open Runs Folder",
            command=self.open_runs_folder,
            width=18,
        )
        self.open_button.pack(side=tk.LEFT, padx=(0, 8))

        self.exit_button = tk.Button(
            button_frame,
            text="Exit",
            command=self.destroy,
            width=12,
        )
        self.exit_button.pack(side=tk.RIGHT)

        self.output_box = scrolledtext.ScrolledText(
            self,
            wrap=tk.WORD,
            padx=10,
            pady=10,
            font=("Consolas", 10),
        )
        self.output_box.pack(fill=tk.BOTH, expand=True, padx=12, pady=(0, 12))
        self.write_output("Ready. Click Run Quick Demo to start a new timestamped run.\n")

    def write_output(self, text: str) -> None:
        self.output_box.configure(state=tk.NORMAL)
        self.output_box.insert(tk.END, text)
        self.output_box.see(tk.END)
        self.output_box.configure(state=tk.DISABLED)

    def set_running(self, running: bool) -> None:
        self.process_running = running
        self.run_button.configure(state=tk.DISABLED if running else tk.NORMAL)

    def run_quick_demo(self) -> None:
        if self.process_running:
            return

        self.set_running(True)
        self.write_output("\nStarting a new AI Playbook Policy Document Finder run...\n")
        self.write_output(f"Working folder: {PROJECT_DIR}\n")
        self.write_output(f"Command: {' '.join(QUICK_COMMAND)}\n\n")

        worker = threading.Thread(target=self._run_quick_demo_worker, daemon=True)
        worker.start()

    def _run_quick_demo_worker(self) -> None:
        try:
            process = subprocess.Popen(
                QUICK_COMMAND,
                cwd=PROJECT_DIR,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1,
            )
            assert process.stdout is not None
            for line in process.stdout:
                self.after(0, self.write_output, line)
            return_code = process.wait()
            self.after(
                0,
                self.write_output,
                f"\nProcess finished with exit code {return_code}.\n",
            )
        except FileNotFoundError as exc:
            self.after(0, self.write_output, f"Error: {exc}\n")
            self.after(
                0,
                messagebox.showerror,
                "Launcher Error",
                "Python or the policy finder script could not be found.",
            )
        except Exception as exc:
            self.after(0, self.write_output, f"Error: {exc}\n")
            self.after(0, messagebox.showerror, "Launcher Error", str(exc))
        finally:
            self.after(0, self.set_running, False)

    def open_runs_folder(self) -> None:
        RUNS_DIR.mkdir(exist_ok=True)
        os.startfile(RUNS_DIR)  # type: ignore[attr-defined]


def main() -> int:
    app = PolicyFinderLauncher()
    app.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import json
import os
import queue
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Any

from core.portfolio_core.constants import API_BASE
from core.portfolio_core.github_api import infer_org_from_api_base
from core.portfolio_core.service import answer_portfolio_question, load_report, run_inventory_scan


class RepoIntelligenceDesktopApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Repo Intelligence Tool")
        self.root.geometry("1100x760")

        self.messages: queue.Queue[tuple[str, Any]] = queue.Queue()
        self.current_report: dict[str, Any] | None = None
        self.current_report_path: Path | None = None

        self.org_var = tk.StringVar(value=infer_org_from_api_base(API_BASE) or "")
        self.token_env_var = tk.StringVar(value="GITHUB_TOKEN")
        self.clone_root_var = tk.StringVar(value="./.cache/org-repo-clones")
        self.output_path_var = tk.StringVar(value="")
        self.clone_enabled_var = tk.BooleanVar(value=False)
        self.force_reclone_var = tk.BooleanVar(value=False)
        self.question_var = tk.StringVar(value="How many projects use React?")

        self._build_layout()
        self.root.after(150, self._process_messages)

    def _build_layout(self) -> None:
        frame = ttk.Frame(self.root, padding=12)
        frame.pack(fill=tk.BOTH, expand=True)

        controls = ttk.LabelFrame(frame, text="Scan Controls", padding=10)
        controls.pack(fill=tk.X)

        self._labeled_entry(controls, "Organization", self.org_var, 0)
        self._labeled_entry(controls, "Token Env Var", self.token_env_var, 1)
        self._labeled_entry(controls, "Clone Root", self.clone_root_var, 2)
        self._labeled_entry(controls, "Output Path (optional)", self.output_path_var, 3)

        toggles = ttk.Frame(controls)
        toggles.grid(row=4, column=0, columnspan=3, sticky="w", pady=(8, 4))
        ttk.Checkbutton(toggles, text="Enable cloning", variable=self.clone_enabled_var).pack(side=tk.LEFT, padx=(0, 14))
        ttk.Checkbutton(toggles, text="Force re-clone", variable=self.force_reclone_var).pack(side=tk.LEFT)

        actions = ttk.Frame(controls)
        actions.grid(row=5, column=0, columnspan=3, sticky="w", pady=(6, 0))
        self.run_button = ttk.Button(actions, text="Run Scan", command=self.run_scan)
        self.run_button.pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(actions, text="Load Report", command=self.load_report_file).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(actions, text="Clear Output", command=self.clear_output).pack(side=tk.LEFT)

        question_frame = ttk.LabelFrame(frame, text="Ask Questions", padding=10)
        question_frame.pack(fill=tk.X, pady=(10, 0))
        ttk.Entry(question_frame, textvariable=self.question_var, width=100).grid(row=0, column=0, sticky="we")
        ttk.Button(question_frame, text="Ask", command=self.ask_question).grid(row=0, column=1, padx=(8, 0))
        question_frame.columnconfigure(0, weight=1)

        output_frame = ttk.LabelFrame(frame, text="Output", padding=10)
        output_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))

        self.output = tk.Text(output_frame, wrap=tk.WORD)
        self.output.pack(fill=tk.BOTH, expand=True)

        self._append_output("Desktop app initialized. Run a scan or load an existing report JSON.")

    def _labeled_entry(self, parent: ttk.Frame, label: str, var: tk.StringVar, row: int) -> None:
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", pady=3)
        ttk.Entry(parent, textvariable=var, width=90).grid(row=row, column=1, sticky="we", padx=(8, 8), pady=3)
        parent.columnconfigure(1, weight=1)

    def _append_output(self, text: str) -> None:
        self.output.insert(tk.END, f"{text}\n")
        self.output.see(tk.END)

    def clear_output(self) -> None:
        self.output.delete("1.0", tk.END)

    def set_running_state(self, is_running: bool) -> None:
        self.run_button.config(state=tk.DISABLED if is_running else tk.NORMAL)

    def run_scan(self) -> None:
        token_env_name = self.token_env_var.get().strip()
        token = os.getenv(token_env_name)
        if not token:
            messagebox.showerror("Missing Token", f"Environment variable {token_env_name} is not set.")
            return

        org = self.org_var.get().strip() or None
        clone_root = Path(self.clone_root_var.get().strip() or "./.cache/org-repo-clones")
        output_path_value = self.output_path_var.get().strip()
        output_path = Path(output_path_value) if output_path_value else None
        do_clone = self.clone_enabled_var.get()
        force_reclone = self.force_reclone_var.get()

        self.set_running_state(True)
        self._append_output("Starting scan...")

        worker = threading.Thread(
            target=self._scan_worker,
            args=(org, token, clone_root, do_clone, force_reclone, output_path),
            daemon=True,
        )
        worker.start()

    def _scan_worker(
        self,
        org: str | None,
        token: str,
        clone_root: Path,
        do_clone: bool,
        force_reclone: bool,
        output_path: Path | None,
    ) -> None:
        try:
            report, report_path = run_inventory_scan(
                org=org,
                token=token,
                clone_root=clone_root,
                do_clone=do_clone,
                force_reclone=force_reclone,
                output_path=output_path,
                progress_callback=lambda msg: self.messages.put(("log", msg)),
            )
            self.messages.put(("done", (report, report_path)))
        except Exception as exc:
            self.messages.put(("error", str(exc)))

    def load_report_file(self) -> None:
        selected = filedialog.askopenfilename(
            title="Select report JSON",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
        )
        if not selected:
            return

        path = Path(selected)
        try:
            report = load_report(path)
        except Exception as exc:
            messagebox.showerror("Load Error", str(exc))
            return

        self.current_report = report
        self.current_report_path = path
        self._append_output(f"Loaded report: {path}")

    def ask_question(self) -> None:
        if not self.current_report:
            messagebox.showwarning("No Report", "Run a scan or load a report first.")
            return

        question = self.question_var.get().strip()
        if not question:
            return

        result = answer_portfolio_question(self.current_report, question)
        self._append_output("\nQuestion: " + question)
        self._append_output(json.dumps(result, indent=2))

    def _process_messages(self) -> None:
        while True:
            try:
                kind, payload = self.messages.get_nowait()
            except queue.Empty:
                break

            if kind == "log":
                self._append_output(str(payload))
            elif kind == "done":
                report, report_path = payload
                self.current_report = report
                self.current_report_path = report_path
                self.output_path_var.set(str(report_path))
                self._append_output(f"Scan complete. Report saved to {report_path}")
                self.set_running_state(False)
            elif kind == "error":
                self._append_output("Error: " + str(payload))
                self.set_running_state(False)

        self.root.after(150, self._process_messages)


def run_desktop_app() -> None:
    root = tk.Tk()
    RepoIntelligenceDesktopApp(root)
    root.mainloop()

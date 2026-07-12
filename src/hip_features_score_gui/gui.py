"""Small Tkinter wrapper for the legacy calculation pipeline."""

from __future__ import annotations

import queue
import sys
import threading
import traceback
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

if __package__:
    from .pipeline import calculate_batch
else:
    # Support direct execution from an IDE in addition to package execution.
    package_root = Path(__file__).resolve().parents[1]
    if str(package_root) not in sys.path:
        sys.path.insert(0, str(package_root))
    from hip_features_score_gui.pipeline import calculate_batch


class Application(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("HIP Features and Ridge Score")
        self.geometry("900x620")
        self.minsize(720, 480)
        self.files: list[Path] = []
        self.output_directory = tk.StringVar(value=str(Path.cwd() / "output"))
        self.status = tk.StringVar(value="Ready")
        self.events: queue.Queue[tuple[str, object]] = queue.Queue()
        self._build()
        self.after(100, self._poll_events)

    def _build(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        files_frame = ttk.LabelFrame(self, text="Selected FASTA files")
        files_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=(10, 5))
        files_frame.columnconfigure(0, weight=1)
        files_frame.rowconfigure(1, weight=1)
        controls = ttk.Frame(files_frame)
        controls.grid(row=0, column=0, sticky="ew", padx=6, pady=6)
        self.select_button = ttk.Button(controls, text="Select FASTA files", command=self.select_files)
        self.remove_button = ttk.Button(controls, text="Remove selected", command=self.remove_selected)
        self.clear_button = ttk.Button(controls, text="Clear list", command=self.clear_files)
        for button in (self.select_button, self.remove_button, self.clear_button):
            button.pack(side="left", padx=(0, 6))
        self.file_list = tk.Listbox(files_frame, selectmode=tk.EXTENDED, height=8)
        self.file_list.grid(row=1, column=0, sticky="nsew", padx=6, pady=(0, 6))
        output_frame = ttk.Frame(self)
        output_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
        output_frame.columnconfigure(1, weight=1)
        ttk.Label(output_frame, text="Output folder").grid(row=0, column=0, sticky="w", padx=(0, 6))
        self.output_entry = ttk.Entry(output_frame, textvariable=self.output_directory)
        self.output_entry.grid(row=0, column=1, sticky="ew")
        self.output_button = ttk.Button(output_frame, text="Select output folder", command=self.select_output)
        self.output_button.grid(row=0, column=2, padx=(6, 0))
        action_frame = ttk.Frame(self)
        action_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=5)
        action_frame.columnconfigure(0, weight=1)
        self.calculate_button = ttk.Button(action_frame, text="Calculate features + score", command=self.start)
        self.calculate_button.grid(row=0, column=0, sticky="w")
        self.open_button = ttk.Button(action_frame, text="Open output folder", command=self.open_output)
        self.open_button.grid(row=0, column=1, sticky="e")
        self.progress = ttk.Progressbar(self, mode="indeterminate")
        self.progress.grid(row=3, column=0, sticky="ew", padx=10, pady=(5, 2))
        ttk.Label(self, textvariable=self.status).grid(row=4, column=0, sticky="w", padx=10)
        logs_frame = ttk.LabelFrame(self, text="Logs")
        logs_frame.grid(row=5, column=0, sticky="nsew", padx=10, pady=(5, 10))
        self.rowconfigure(5, weight=1)
        logs_frame.columnconfigure(0, weight=1)
        logs_frame.rowconfigure(0, weight=1)
        self.logs = tk.Text(logs_frame, height=9, state="disabled", wrap="word")
        self.logs.grid(row=0, column=0, sticky="nsew", padx=6, pady=6)

    def _log(self, message: str) -> None:
        self.logs.configure(state="normal")
        self.logs.insert("end", message + "\n")
        self.logs.see("end")
        self.logs.configure(state="disabled")

    def select_files(self) -> None:
        paths = filedialog.askopenfilenames(title="Select FASTA files", filetypes=[("FASTA files", "*.fasta *.fa *.faa *.txt"), ("All files", "*.*")])
        for raw in paths:
            path = Path(raw)
            if path not in self.files:
                self.files.append(path)
                self.file_list.insert("end", str(path))

    def remove_selected(self) -> None:
        selected = list(self.file_list.curselection())
        for index in reversed(selected):
            del self.files[index]
            self.file_list.delete(index)

    def clear_files(self) -> None:
        self.files.clear()
        self.file_list.delete(0, "end")

    def select_output(self) -> None:
        directory = filedialog.askdirectory(title="Select output folder")
        if directory:
            self.output_directory.set(directory)

    def open_output(self) -> None:
        directory = Path(self.output_directory.get())
        directory.mkdir(parents=True, exist_ok=True)
        try:
            __import__("os").startfile(directory)  # type: ignore[attr-defined]
        except OSError as exc:
            messagebox.showerror("Open output folder", str(exc), parent=self)

    def _set_busy(self, busy: bool) -> None:
        state = "disabled" if busy else "normal"
        for control in (self.select_button, self.remove_button, self.clear_button, self.output_entry,
                        self.output_button, self.calculate_button):
            control.configure(state=state)
        if busy:
            self.progress.start(12)
        else:
            self.progress.stop()

    def start(self) -> None:
        if not self.files:
            messagebox.showwarning("No input", "Select at least one FASTA file.", parent=self)
            return
        if not self.output_directory.get().strip():
            messagebox.showwarning("No output folder", "Select an output folder.", parent=self)
            return
        self._set_busy(True)
        self.status.set("Starting calculation...")
        threading.Thread(target=self._worker, daemon=True).start()

    def _worker(self) -> None:
        try:
            def report(message: str) -> None:
                self.events.put(("log", message))
            outputs = calculate_batch(self.files, self.output_directory.get(), report)
            self.events.put(("done", outputs))
        except Exception:
            self.events.put(("error", traceback.format_exc()))

    def _poll_events(self) -> None:
        try:
            while True:
                kind, value = self.events.get_nowait()
                if kind == "log":
                    self.status.set(str(value))
                    self._log(str(value))
                elif kind == "done":
                    self._set_busy(False)
                    self.status.set("Completed")
                    self._log("Completed")
                    messagebox.showinfo("Completed", f"Created {len(value)} CSV file(s).", parent=self)
                elif kind == "error":
                    self._set_busy(False)
                    self.status.set("Failed")
                    self._log(str(value))
                    messagebox.showerror("Calculation failed", "See Logs for the technical error.", parent=self)
        except queue.Empty:
            pass
        self.after(100, self._poll_events)


def main() -> None:
    Application().mainloop()


if __name__ == "__main__":
    main()

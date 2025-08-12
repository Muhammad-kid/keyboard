#!/usr/bin/env python3
"""
Clivox - Portable UI (Strictly uses local tools/ folder: ffmpeg/ffmpeg.exe, ffprobe/ffprobe.exe, yt-dlp/yt_dlp or yt-dlp)
Place this file next to the tools/ folder and build with PyInstaller or include in your installer.
PyInstaller example:
    pyinstaller --noconfirm --onefile --icon=icon.ico clivox.py
Note: We do NOT bundle tools; they must be in a sibling folder named `tools` next to the executable/script.
"""

import os
import sys
import threading
import subprocess
import json
import re
from pathlib import Path
import platform
import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk

# ----------------------
# Config & Helpers
# ----------------------
# Locate application directory (real exe location if frozen)
if getattr(sys, "frozen", False):
    APP_DIR = os.path.dirname(sys.executable)
else:
    APP_DIR = os.path.dirname(os.path.abspath(__file__))

# Tools folder path (STRICT: no PATH fallback)
TOOLS_DIR = os.path.join(APP_DIR, "tools")

APP_NAME = "Clivox"
APP_VERSION = "2.2.0"

IS_WINDOWS = platform.system() == "Windows"

# Theme colors (dark blue/black, no green)
COLOR_BG = "#070B12"         # near-black
COLOR_CARD = "#0B1524"        # dark blue card
COLOR_ACCENT = "#2F67F6"      # calm blue accent
COLOR_ACCENT_HOVER = "#3B82F6"
COLOR_TEXT = "#E6EEF7"        # light text
COLOR_SUBTLE = "#8CA0BF"      # secondary text

# Progress regex
_PROGRESS_RE = re.compile(r"\[download\]\s+([0-9]{1,3}(?:\.[0-9])?)%")


def candidate_names(base: str) -> list[str]:
    if IS_WINDOWS:
        return [f"{base}.exe", base]
    return [base, f"{base}.exe"]


def find_tool_strict(base_names: list[str]) -> str | None:
    for name in base_names:
        path = os.path.join(TOOLS_DIR, name)
        if os.path.isfile(path) and os.access(path, os.X_OK):
            return path
    return None


# Resolve tools strictly from tools/
YTDLP_PATH = find_tool_strict(candidate_names("yt-dlp")) or find_tool_strict(candidate_names("yt_dlp"))
FFMPEG_PATH = find_tool_strict(candidate_names("ffmpeg"))
FFPROBE_PATH = find_tool_strict(candidate_names("ffprobe"))

MISSING_TOOLS: list[str] = []
if not YTDLP_PATH:
    MISSING_TOOLS.append("yt-dlp")
if not FFMPEG_PATH:
    MISSING_TOOLS.append("ffmpeg")
if not FFPROBE_PATH:
    MISSING_TOOLS.append("ffprobe")


# ----------------------
# UI Class (Download-only)
# ----------------------
class ClivoxApp:
    def __init__(self) -> None:
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")
        ctk.set_widget_scaling(1.0)
        ctk.set_window_scaling(1.0)

        self.root = ctk.CTk()
        self.root.title(f"{APP_NAME} v{APP_VERSION}")
        self.root.geometry("920x560")
        self.root.minsize(820, 480)
        self.root.configure(fg_color=COLOR_BG)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        # Window icon from icon.png (remove default box icon)
        try:
            icon_path = os.path.join(APP_DIR, "icon.png")
            self._icon_img = tk.PhotoImage(file=icon_path)
            # Set icon for window and taskbar where supported
            self.root.iconphoto(True, self._icon_img)
        except Exception:
            pass

        # State
        self.url_var = ctk.StringVar()
        self.path_var = ctk.StringVar(value=str(Path.home() / "Downloads"))
        self.quality_var = ctk.StringVar(value="best")
        self.format_var = ctk.StringVar(value="MP4")
        self.audio_only_var = ctk.BooleanVar(value=False)
        self.strip_audio_var = ctk.BooleanVar(value=False)
        self.current_proc: subprocess.Popen | None = None

        # Layout
        self._build_layout()
        self._start_card_animation()

    # ----------------------
    # Layout (animated card background)
    # ----------------------
    def _build_layout(self) -> None:
        # Outer padding wrapper
        wrapper = ctk.CTkFrame(self.root, fg_color="transparent")
        wrapper.pack(fill="both", expand=True, padx=24, pady=24)
        wrapper.grid_columnconfigure(0, weight=1)
        wrapper.grid_rowconfigure(0, weight=1)

        # Card container
        self.card = ctk.CTkFrame(wrapper, fg_color=COLOR_CARD, corner_radius=18)
        self.card.grid(row=0, column=0, sticky="nsew")
        self.card.grid_columnconfigure(0, weight=1)

        # Animated canvas inside the card
        self.card_canvas = tk.Canvas(self.card, highlightthickness=0, bd=0, bg=COLOR_CARD)
        self.card_canvas.place(relx=0, rely=0, relwidth=1, relheight=1)
        self._card_phase = 0

        # Foreground content on top of canvas
        self.content = ctk.CTkFrame(self.card, fg_color="transparent")
        self.content.pack(fill="both", expand=True)

        # Header
        header = ctk.CTkFrame(self.content, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(18, 10))
        ctk.CTkLabel(header, text=APP_NAME, text_color=COLOR_TEXT, font=ctk.CTkFont(size=22, weight="bold")).pack(side="left")
        ctk.CTkLabel(header, text=f"v{APP_VERSION}", text_color=COLOR_SUBTLE, font=ctk.CTkFont(size=12)).pack(side="left", padx=(8, 0))

        tools_txt = "All tools ready" if not MISSING_TOOLS else f"Missing: {', '.join(MISSING_TOOLS)}"
        ctk.CTkLabel(header, text=tools_txt, text_color=(COLOR_TEXT if not MISSING_TOOLS else "#C2C7D0"), font=ctk.CTkFont(size=12)).pack(side="right")

        # Body
        body = ctk.CTkFrame(self.content, fg_color="transparent")
        body.pack(fill="x", padx=20, pady=(6, 6))

        # URL
        ctk.CTkLabel(body, text="Video URL", text_color=COLOR_SUBTLE).pack(anchor="w", pady=(4, 2))
        self.url_entry = ctk.CTkEntry(body, textvariable=self.url_var, height=42, fg_color="#0A1422", border_color=COLOR_ACCENT, text_color=COLOR_TEXT, placeholder_text="Paste video URL...")
        self.url_entry.pack(fill="x")

        # Save path row (Browse button moved here)
        ctk.CTkLabel(body, text="Save To", text_color=COLOR_SUBTLE).pack(anchor="w", pady=(12, 2))
        save_row = ctk.CTkFrame(body, fg_color="transparent")
        save_row.pack(fill="x")
        self.path_entry = ctk.CTkEntry(save_row, textvariable=self.path_var, height=42, fg_color="#0A1422", border_color=COLOR_ACCENT, text_color=COLOR_TEXT)
        self.path_entry.pack(side="left", fill="x", expand=True)
        ctk.CTkButton(save_row, text="Browse", width=120, height=42, fg_color=COLOR_ACCENT, hover_color=COLOR_ACCENT_HOVER, text_color="#FFFFFF", command=self._browse_dir).pack(side="left", padx=(10, 0))

        # Options row
        opts = ctk.CTkFrame(self.content, fg_color="transparent")
        opts.pack(fill="x", padx=20, pady=(10, 6))
        for i in range(4):
            opts.grid_columnconfigure(i, weight=1)

        ctk.CTkLabel(opts, text="Quality", text_color=COLOR_SUBTLE).grid(row=0, column=0, sticky="w", padx=(0, 6))
        self.quality_menu = ctk.CTkOptionMenu(opts, variable=self.quality_var, values=["best", "2160p", "1440p", "1080p", "720p", "480p", "360p", "worst"], fg_color="#0A1422", button_color=COLOR_ACCENT, button_hover_color=COLOR_ACCENT_HOVER, text_color=COLOR_TEXT)
        self.quality_menu.grid(row=1, column=0, sticky="ew", padx=(0, 12))

        ctk.CTkLabel(opts, text="Format", text_color=COLOR_SUBTLE).grid(row=0, column=1, sticky="w", padx=(0, 6))
        self.format_menu = ctk.CTkOptionMenu(opts, variable=self.format_var, values=["MP4", "WebM", "MKV", "MP3"], fg_color="#0A1422", button_color=COLOR_ACCENT, button_hover_color=COLOR_ACCENT_HOVER, text_color=COLOR_TEXT)
        self.format_menu.grid(row=1, column=1, sticky="ew", padx=(0, 12))

        self.audio_cb = ctk.CTkCheckBox(opts, text="Audio Only", variable=self.audio_only_var, command=self._on_toggle_audio, fg_color=COLOR_ACCENT, text_color=COLOR_TEXT)
        self.audio_cb.grid(row=1, column=2, sticky="w")
        self.strip_cb = ctk.CTkCheckBox(opts, text="No Audio", variable=self.strip_audio_var, fg_color=COLOR_ACCENT, text_color=COLOR_TEXT)
        self.strip_cb.grid(row=1, column=3, sticky="w")

        # Actions
        actions = ctk.CTkFrame(self.content, fg_color="transparent")
        actions.pack(fill="x", padx=20, pady=(8, 16))
        self.download_btn = ctk.CTkButton(actions, text="Download", height=44, fg_color=COLOR_ACCENT, hover_color=COLOR_ACCENT_HOVER, text_color="#FFFFFF", command=self.start_download)
        self.download_btn.pack(side="right")

        # Status
        status = ctk.CTkFrame(self.content, fg_color="transparent")
        status.pack(fill="x", padx=20, pady=(0, 18))
        self.progress_label = ctk.CTkLabel(status, text="Ready", anchor="w", text_color=COLOR_TEXT)
        self.progress_label.pack(fill="x")
        self.progress_bar = ctk.CTkProgressBar(status, progress_color=COLOR_ACCENT)
        self.progress_bar.set(0)
        self.progress_bar.pack(fill="x", pady=(8, 0))

    # ----------------------
    # UI Helpers
    # ----------------------
    def _browse_dir(self) -> None:
        d = filedialog.askdirectory(initialdir=self.path_var.get())
        if d:
            self.path_var.set(d)

    def _on_toggle_audio(self) -> None:
        if self.audio_only_var.get():
            self.format_var.set("MP3")
            self.format_menu.configure(values=["MP3"])
        else:
            self.format_menu.configure(values=["MP4", "WebM", "MKV", "MP3"])
            if self.format_var.get() == "MP3":
                self.format_var.set("MP4")

    # ----------------------
    # Download flow (single task)
    # ----------------------
    def start_download(self) -> None:
        if MISSING_TOOLS:
            messagebox.showerror("Tools Missing", "The following tools were not found in the tools/ folder:\n- " + "\n- ".join(MISSING_TOOLS))
            return
        url = (self.url_var.get() or "").strip()
        if not url:
            messagebox.showwarning("Error", "Enter a URL first.")
            return
        dest = (self.path_var.get() or "").strip()
        if not dest:
            messagebox.showwarning("Error", "Choose a destination folder.")
            return
        Path(dest).mkdir(parents=True, exist_ok=True)
        if self.current_proc and self.current_proc.poll() is None:
            messagebox.showinfo("Info", "A download is already in progress.")
            return

        self.download_btn.configure(state="disabled", text="Downloading…")
        self.progress_bar.set(0)
        self.progress_label.configure(text="Starting…")

        opts = {
            "quality": self.quality_var.get(),
            "format": self.format_var.get(),
            "audio_only": self.audio_only_var.get(),
            "strip_audio": self.strip_audio_var.get(),
        }
        threading.Thread(target=self._download_worker, args=(url, dest, opts), daemon=True).start()

    def _download_worker(self, url: str, dest: str, opts: dict) -> None:
        out_template = os.path.join(dest, "%(title)s.%(ext)s")
        ffmpeg_dir = os.path.dirname(FFMPEG_PATH) if FFMPEG_PATH else None
        ffmpeg_loc_args = ["--ffmpeg-location", ffmpeg_dir] if ffmpeg_dir else []

        if opts.get("audio_only"):
            cmd = [
                YTDLP_PATH,
                "-f",
                "bestaudio",
                "-o",
                out_template,
                "--extract-audio",
                "--audio-format",
                "mp3",
                *ffmpeg_loc_args,
                url,
            ]
        else:
            q = opts.get("quality", "best")
            if q == "best":
                fmt = "best"
            elif q == "worst":
                fmt = "worst"
            else:
                height = re.sub(r"[^0-9]", "", q) or "1080"
                fmt = f"bestvideo[height<={height}]+bestaudio/best"

            container = (opts.get("format") or "MP4").lower()
            remux_args: list[str] = []
            if container in {"mp4", "webm", "mkv"}:
                remux_args = ["--remux-video", container]
            elif container == "mp3":
                fmt = "bestaudio/best"
                remux_args = ["--extract-audio", "--audio-format", "mp3"]

            post_args: list[str] = []
            if opts.get("strip_audio") and container != "mp3":
                post_args = ["--postprocessor-args", "ffmpeg:-an"]

            cmd = [
                YTDLP_PATH,
                "-f",
                fmt,
                "-o",
                out_template,
                *remux_args,
                *post_args,
                *ffmpeg_loc_args,
                url,
            ]

        try:
            self.current_proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )
            assert self.current_proc.stdout is not None
            for line in self.current_proc.stdout:
                m = _PROGRESS_RE.search(line)
                if m:
                    try:
                        pct = float(m.group(1)) / 100.0
                        self.root.after(0, self.progress_bar.set, pct)
                    except Exception:
                        pass
                clean = line.strip()
                if clean:
                    self.root.after(0, self.progress_label.configure, {"text": clean[:120]})
            self.current_proc.wait()
            if self.current_proc.returncode == 0:
                self.root.after(0, self.progress_label.configure, {"text": "Download complete"})
            else:
                self.root.after(0, self.progress_label.configure, {"text": "Download failed"})
        except Exception as e:
            self.root.after(0, self.progress_label.configure, {"text": f"Error: {e}"})
        finally:
            self.current_proc = None
            self.root.after(0, self.download_btn.configure, {"state": "normal", "text": "Download"})

    # ----------------------
    # Card Background Animation (subtle, not global)
    # ----------------------
    def _start_card_animation(self) -> None:
        self._animate_card_background()

    def _animate_card_background(self) -> None:
        w = self.card_canvas.winfo_width() or self.card.winfo_width()
        h = self.card_canvas.winfo_height() or self.card.winfo_height()
        if w <= 0 or h <= 0:
            self.root.after(80, self._animate_card_background)
            return

        self.card_canvas.delete("all")

        # Horizontal gradient bands that gently drift
        steps = 42
        phase = self._card_phase
        for i in range(steps):
            t = ((i + phase) % steps) / steps
            # subtle blue shades
            r = int(11 + 8 * (1 - t))
            g = int(21 + 28 * t)
            b = int(36 + 60 * (1 - t))
            color = f"#{r:02x}{g:02x}{b:02x}"
            y0 = i * h / steps
            y1 = (i + 1) * h / steps + 1
            self.card_canvas.create_rectangle(0, y0, w, y1, fill=color, outline="")

        # Soft overlay waves (polylines) to avoid circles/boxes look
        wave_count = 2
        for k in range(wave_count):
            t = (phase / 35.0 + k * 0.33) % 1.0
            y = int(h * (0.2 + 0.6 * t))
            shade = f"#{int(18+12*(1-t)):02x}{int(40+30*t):02x}{int(80+40*(1-t)):02x}"
            self.card_canvas.create_polygon(
                -50, y - 30,
                int(w * 0.3), y - 10,
                int(w * 0.6), y + 10,
                w + 50, y + 30,
                w + 50, y + 60,
                -50, y + 40,
                fill=shade,
                outline="",
            )

        self._card_phase = (self._card_phase + 1) % steps
        self.root.after(100, self._animate_card_background)

    # ----------------------
    # Close
    # ----------------------
    def on_close(self) -> None:
        if self.current_proc and self.current_proc.poll() is None:
            if not messagebox.askyesno("Confirm", "Download in progress. Exit?"):
                return
            try:
                self.current_proc.terminate()
            except Exception:
                pass
        self.root.destroy()

    def run(self) -> None:
        self.root.mainloop()


# ----------------------
# Entrypoint
# ----------------------

def main() -> None:
    if not os.path.isdir(TOOLS_DIR):
        messagebox.showwarning("Warning", f"Tools folder missing!\nExpected: {TOOLS_DIR}")
    app = ClivoxApp()
    app.run()


if __name__ == "__main__":
    main()
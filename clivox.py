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
import time
import json
import shutil
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
APP_VERSION = "2.0.0"

IS_WINDOWS = platform.system() == "Windows"

# Colors
COLOR_BG = "#050B16"        # Almost black blue
COLOR_BG_CANVAS = "#02060D"  # Pure blackish for canvas base
COLOR_CARD = "#0D1B2A"       # Dark blue card
COLOR_ACCENT = "#39FF14"     # Neon green
COLOR_ACCENT_DIM = "#00CC00" # Hover variant
COLOR_TEXT = "#E6EEF7"       # Light text
COLOR_SUBTLE = "#7A8BA1"     # Secondary text

# Progress regex
_PROGRESS_RE = re.compile(r"\[download\]\s+([0-9]{1,3}(?:\.[0-9])?)%")


def candidate_names(base: str) -> list[str]:
    if IS_WINDOWS:
        return [f"{base}.exe", base]  # prefer .exe
    return [base, f"{base}.exe"]      # prefer non-exe on non-Windows


def find_tool_strict(base_names: list[str]) -> str | None:
    """Return absolute path to the first existing, executable tool inside TOOLS_DIR only."""
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
# UI Class
# ----------------------
class ClivoxApp:
    def __init__(self) -> None:
        # CTk setup
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")
        ctk.set_widget_scaling(1.0)
        ctk.set_window_scaling(1.0)

        self.root = ctk.CTk()
        self.root.title(f"{APP_NAME} v{APP_VERSION}")
        self.root.geometry("1100x720")
        self.root.minsize(920, 640)
        self.root.configure(fg_color=COLOR_BG)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        # Window icon from icon.png
        try:
            icon_path = os.path.join(APP_DIR, "icon.png")
            self._icon_img = tk.PhotoImage(file=icon_path)
            self.root.iconphoto(True, self._icon_img)
        except Exception:
            # Keep default if icon missing
            pass

        # State
        self.url_var = ctk.StringVar()
        self.path_var = ctk.StringVar(value=str(Path.home() / "Downloads"))
        self.quality_var = ctk.StringVar(value="best")
        self.format_var = ctk.StringVar(value="MP4")
        self.audio_only_var = ctk.BooleanVar(value=False)
        self.strip_audio_var = ctk.BooleanVar(value=False)
        self.queue: list[dict] = []
        self.current_proc: subprocess.Popen | None = None
        self.stop_flag = threading.Event()

        # Build UI
        self._build_layout()
        self._start_bg_animation()

    # ----------------------
    # Layout
    # ----------------------
    def _build_layout(self) -> None:
        # Background animated canvas (underlay)
        self.bg_canvas = tk.Canvas(self.root, highlightthickness=0, bd=0, bg=COLOR_BG_CANVAS)
        self.bg_canvas.place(relx=0, rely=0, relwidth=1, relheight=1)
        self._gradient_phase = 0

        # Header card
        header = ctk.CTkFrame(self.root, fg_color=COLOR_CARD, corner_radius=18)
        header.pack(fill="x", padx=20, pady=(16, 10))

        title = ctk.CTkLabel(
            header,
            text=APP_NAME,
            text_color=COLOR_ACCENT,
            font=ctk.CTkFont(size=28, weight="bold"),
        )
        title.pack(side="left", padx=18, pady=14)

        ver = ctk.CTkLabel(
            header,
            text=f"v{APP_VERSION}",
            text_color=COLOR_SUBTLE,
            font=ctk.CTkFont(size=14),
        )
        ver.pack(side="left", padx=8)

        tools_text = (
            "All tools ready" if not MISSING_TOOLS else f"Missing: {', '.join(MISSING_TOOLS)}"
        )
        notice = ctk.CTkLabel(
            header,
            text=tools_text,
            text_color=(COLOR_TEXT if not MISSING_TOOLS else "#FFA500"),
        )
        notice.pack(side="right", padx=18)

        # Main grid: left column (download card), right column (queue/status)
        body = ctk.CTkFrame(self.root, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        body.grid_columnconfigure(0, weight=3, uniform="cols")
        body.grid_columnconfigure(1, weight=2, uniform="cols")
        body.grid_rowconfigure(0, weight=1)

        # Left: Download Card
        left_card = ctk.CTkFrame(body, fg_color=COLOR_CARD, corner_radius=18)
        left_card.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=0)

        self._build_download_card(left_card)

        # Right: Queue + Status Card
        right_card = ctk.CTkFrame(body, fg_color=COLOR_CARD, corner_radius=18)
        right_card.grid(row=0, column=1, sticky="nsew", padx=(10, 0), pady=0)

        self._build_queue_status_card(right_card)

    def _build_download_card(self, parent: ctk.CTkFrame) -> None:
        # Title
        ctk.CTkLabel(
            parent,
            text="Download",
            text_color=COLOR_TEXT,
            font=ctk.CTkFont(size=20, weight="bold"),
        ).pack(anchor="w", padx=18, pady=(16, 6))

        # URL input
        url_frame = ctk.CTkFrame(parent, fg_color="transparent")
        url_frame.pack(fill="x", padx=18, pady=(4, 10))

        ctk.CTkLabel(url_frame, text="Video URL", text_color=COLOR_SUBTLE).pack(anchor="w")
        row = ctk.CTkFrame(url_frame, fg_color="transparent")
        row.pack(fill="x", pady=6)
        self.url_entry = ctk.CTkEntry(
            row,
            textvariable=self.url_var,
            height=44,
            fg_color="#0A1624",
            border_color=COLOR_ACCENT,
            text_color=COLOR_TEXT,
            placeholder_text="Paste URL here...",
        )
        self.url_entry.pack(side="left", fill="x", expand=True)
        ctk.CTkButton(
            row,
            text="Paste",
            width=100,
            height=44,
            fg_color=COLOR_ACCENT,
            text_color=COLOR_BG_CANVAS,
            hover_color=COLOR_ACCENT_DIM,
            command=self._paste_clip,
        ).pack(side="left", padx=(10, 0))

        # Options grid
        opts = ctk.CTkFrame(parent, fg_color="transparent")
        opts.pack(fill="x", padx=18, pady=4)
        for i in range(4):
            opts.grid_columnconfigure(i, weight=1)

        ctk.CTkLabel(opts, text="Quality", text_color=COLOR_SUBTLE).grid(row=0, column=0, sticky="w", padx=4, pady=(6, 4))
        self.quality_menu = ctk.CTkOptionMenu(
            opts,
            variable=self.quality_var,
            values=["best", "2160p", "1440p", "1080p", "720p", "480p", "360p", "worst"],
            fg_color="#0A1624",
            button_color=COLOR_ACCENT,
            button_hover_color=COLOR_ACCENT_DIM,
            text_color=COLOR_TEXT,
        )
        self.quality_menu.grid(row=1, column=0, sticky="ew", padx=4, pady=(0, 8))

        ctk.CTkLabel(opts, text="Format", text_color=COLOR_SUBTLE).grid(row=0, column=1, sticky="w", padx=4, pady=(6, 4))
        self.format_menu = ctk.CTkOptionMenu(
            opts,
            variable=self.format_var,
            values=["MP4", "WebM", "MKV", "MP3"],
            fg_color="#0A1624",
            button_color=COLOR_ACCENT,
            button_hover_color=COLOR_ACCENT_DIM,
            text_color=COLOR_TEXT,
        )
        self.format_menu.grid(row=1, column=1, sticky="ew", padx=4, pady=(0, 8))

        self.audio_cb = ctk.CTkCheckBox(
            opts,
            text="Audio Only",
            variable=self.audio_only_var,
            command=self._on_toggle_audio,
            fg_color=COLOR_ACCENT,
            text_color=COLOR_TEXT,
        )
        self.audio_cb.grid(row=1, column=2, sticky="w", padx=4, pady=(0, 8))

        self.strip_cb = ctk.CTkCheckBox(
            opts,
            text="No Audio",
            variable=self.strip_audio_var,
            fg_color=COLOR_ACCENT,
            text_color=COLOR_TEXT,
        )
        self.strip_cb.grid(row=1, column=3, sticky="w", padx=4, pady=(0, 8))

        # Save path
        path_frame = ctk.CTkFrame(parent, fg_color="transparent")
        path_frame.pack(fill="x", padx=18, pady=(6, 6))
        ctk.CTkLabel(path_frame, text="Save To", text_color=COLOR_SUBTLE).pack(anchor="w")
        path_row = ctk.CTkFrame(path_frame, fg_color="transparent")
        path_row.pack(fill="x", pady=6)
        self.path_entry = ctk.CTkEntry(
            path_row,
            textvariable=self.path_var,
            height=44,
            fg_color="#0A1624",
            border_color=COLOR_ACCENT,
            text_color=COLOR_TEXT,
        )
        self.path_entry.pack(side="left", fill="x", expand=True)
        ctk.CTkButton(
            path_row,
            text="Browse",
            width=110,
            height=44,
            fg_color=COLOR_ACCENT,
            text_color=COLOR_BG_CANVAS,
            hover_color=COLOR_ACCENT_DIM,
            command=self._browse_dir,
        ).pack(side="left", padx=(10, 0))

        # Actions
        actions = ctk.CTkFrame(parent, fg_color="transparent")
        actions.pack(fill="x", padx=18, pady=(10, 16))
        ctk.CTkButton(
            actions,
            text="Get Info",
            height=44,
            fg_color="#0A1624",
            border_color=COLOR_ACCENT,
            border_width=1,
            text_color=COLOR_TEXT,
            hover_color="#10243A",
            command=self.get_info,
        ).pack(side="left")

        ctk.CTkButton(
            actions,
            text="Add to Queue",
            height=44,
            fg_color="#0A1624",
            border_color=COLOR_ACCENT,
            border_width=1,
            text_color=COLOR_TEXT,
            hover_color="#10243A",
            command=self.add_to_queue,
        ).pack(side="left", padx=10)

        ctk.CTkButton(
            actions,
            text="Start Download",
            height=44,
            fg_color=COLOR_ACCENT,
            text_color=COLOR_BG_CANVAS,
            hover_color=COLOR_ACCENT_DIM,
            command=self.start_queue,
        ).pack(side="right")

    def _build_queue_status_card(self, parent: ctk.CTkFrame) -> None:
        # Title
        ctk.CTkLabel(
            parent,
            text="Queue & Status",
            text_color=COLOR_TEXT,
            font=ctk.CTkFont(size=20, weight="bold"),
        ).pack(anchor="w", padx=18, pady=(16, 6))

        # Queue
        queue_frame = ctk.CTkFrame(parent, fg_color="transparent")
        queue_frame.pack(fill="both", expand=True, padx=18, pady=(6, 10))

        self.queue_listbox = tk.Listbox(
            queue_frame,
            height=10,
            bg="#0A1624",
            fg=COLOR_TEXT,
            bd=0,
            highlightthickness=0,
            selectbackground=COLOR_ACCENT,
            selectforeground=COLOR_BG_CANVAS,
            font=("Arial", 12),
        )
        self.queue_listbox.pack(fill="both", expand=True)
        self.queue_listbox.bind("<Delete>", lambda e: self.remove_selected_from_queue())

        btns = ctk.CTkFrame(parent, fg_color="transparent")
        btns.pack(fill="x", padx=18, pady=(4, 8))

        ctk.CTkButton(
            btns,
            text="Remove Selected",
            height=40,
            fg_color="#0A1624",
            border_color=COLOR_ACCENT,
            border_width=1,
            text_color=COLOR_TEXT,
            hover_color="#10243A",
            command=self.remove_selected_from_queue,
        ).pack(side="left")

        ctk.CTkButton(
            btns,
            text="Clear Queue",
            height=40,
            fg_color="#0A1624",
            border_color=COLOR_ACCENT,
            border_width=1,
            text_color=COLOR_TEXT,
            hover_color="#10243A",
            command=self.clear_queue,
        ).pack(side="left", padx=10)

        ctk.CTkButton(
            btns,
            text="Stop Current",
            height=40,
            fg_color=COLOR_ACCENT,
            text_color=COLOR_BG_CANVAS,
            hover_color=COLOR_ACCENT_DIM,
            command=self.stop_current,
        ).pack(side="right")

        # Status
        status = ctk.CTkFrame(parent, fg_color="transparent")
        status.pack(fill="x", padx=18, pady=(4, 18))
        self.progress_label = ctk.CTkLabel(status, text="Ready", anchor="w", text_color=COLOR_TEXT)
        self.progress_label.pack(fill="x")
        self.progress_bar = ctk.CTkProgressBar(status, progress_color=COLOR_ACCENT)
        self.progress_bar.set(0)
        self.progress_bar.pack(fill="x", pady=(8, 0))

    # ----------------------
    # UI Helpers
    # ----------------------
    def _paste_clip(self) -> None:
        try:
            clip = self.root.clipboard_get()
            self.url_var.set(clip.strip())
        except Exception:
            pass

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
    # Queue Management
    # ----------------------
    def add_to_queue(self) -> None:
        url = (self.url_var.get() or "").strip()
        if not url:
            messagebox.showwarning("Error", "Enter a URL first.")
            return
        dest = (self.path_var.get() or "").strip()
        if not dest:
            messagebox.showwarning("Error", "Choose a destination folder.")
            return
        os.makedirs(dest, exist_ok=True)
        opts = {
            "quality": self.quality_var.get(),
            "format": self.format_var.get(),
            "audio_only": self.audio_only_var.get(),
            "strip_audio": self.strip_audio_var.get(),
        }
        self.queue.append({"url": url, "dest": dest, "opts": opts})
        self._refresh_queue()
        messagebox.showinfo("Queued", "Added to queue.")

    def _refresh_queue(self) -> None:
        self.queue_listbox.delete(0, tk.END)
        for i, item in enumerate(self.queue, 1):
            short = (item["url"][:52] + "…") if len(item["url"]) > 55 else item["url"]
            label = f"{i}. {short} → {item['dest']} [{item['opts']['format']}]"
            self.queue_listbox.insert(tk.END, label)

    def remove_selected_from_queue(self) -> None:
        sel = self.queue_listbox.curselection()
        if sel:
            self.queue.pop(sel[0])
            self._refresh_queue()

    def clear_queue(self) -> None:
        if messagebox.askyesno("Confirm", "Clear queue?"):
            self.queue.clear()
            self._refresh_queue()

    def start_queue(self) -> None:
        if MISSING_TOOLS:
            messagebox.showerror(
                "Tools Missing",
                "The following tools were not found in the tools/ folder:\n- "
                + "\n- ".join(MISSING_TOOLS)
                + "\n\nPlease place them in the tools folder next to the executable and restart.",
            )
            return
        if not self.queue:
            messagebox.showinfo("Info", "Queue is empty.")
            return
        if self.current_proc and self.current_proc.poll() is None:
            messagebox.showinfo("Info", "A download is already in progress.")
            return
        self.stop_flag.clear()
        threading.Thread(target=self._queue_worker, daemon=True).start()

    def stop_current(self) -> None:
        self.stop_flag.set()
        if self.current_proc and self.current_proc.poll() is None:
            try:
                self.current_proc.terminate()
            except Exception:
                pass
        self.progress_label.configure(text="Stopped")
        self.progress_bar.set(0)

    def _queue_worker(self) -> None:
        while self.queue and not self.stop_flag.is_set():
            item = self.queue.pop(0)
            self._refresh_queue()
            self._download_item(item)
            time.sleep(0.5)
        if not self.stop_flag.is_set():
            self.progress_label.configure(text="Queue complete")
        self.progress_bar.set(0)

    # ----------------------
    # Info
    # ----------------------
    def get_info(self) -> None:
        url = (self.url_var.get() or "").strip()
        if not url:
            messagebox.showwarning("Error", "Enter a URL first.")
            return
        if not YTDLP_PATH:
            messagebox.showerror("Error", "yt-dlp not found in tools/.")
            return

        def worker() -> None:
            btn = None
            try:
                # Disable button visually by finding and disabling after a small delay
                # This keeps the layout code simpler
                cmd = [YTDLP_PATH, "--dump-json", url]
                out = subprocess.check_output(cmd, text=True)
                info = json.loads(out)
                msg = (
                    f"Title: {info.get('title', 'N/A')}\n"
                    f"Uploader: {info.get('uploader', 'N/A')}\n"
                    f"Duration: {info.get('duration', 0)}s"
                )
                messagebox.showinfo("Info", msg)
            except subprocess.CalledProcessError as e:
                messagebox.showerror("Error", e.output or str(e))
            except Exception as e:
                messagebox.showerror("Error", str(e))
            finally:
                if btn is not None:
                    try:
                        btn.configure(state="normal")
                    except Exception:
                        pass

        threading.Thread(target=worker, daemon=True).start()

    # ----------------------
    # Download
    # ----------------------
    def _download_item(self, item: dict) -> None:
        url = item["url"]
        dest = item["dest"]
        opts = item["opts"]

        self.progress_label.configure(text=f"Preparing: {url[:60]}…")

        out_template = os.path.join(dest, "%(title)s.%(ext)s")
        ffmpeg_dir = os.path.dirname(FFMPEG_PATH) if FFMPEG_PATH else None
        ffmpeg_loc_args = ["--ffmpeg-location", ffmpeg_dir] if ffmpeg_dir else []

        if opts["audio_only"]:
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
            if opts.get("quality") == "best":
                fmt = "best"
            elif opts.get("quality") == "worst":
                fmt = "worst"
            else:
                # e.g., 1080p -> pick best up to that height
                height = re.sub(r"[^0-9]", "", opts.get("quality", "")) or "1080"
                fmt = f"bestvideo[height<={height}]+bestaudio/best"

            # Force container if requested
            container = (opts.get("format") or "MP4").lower()
            remux_args: list[str] = []
            if container in {"mp4", "webm", "mkv"}:
                remux_args = ["--remux-video", container]
            elif container == "mp3":
                # If user chose MP3 without checking audio only, respect by extracting audio
                fmt = "bestaudio/best"
                remux_args = ["--extract-audio", "--audio-format", "mp3"]

            # Optional: strip audio from video
            post_args: list[str] = []
            if opts.get("strip_audio") and container != "mp3":
                # Use ffmpeg via postprocessor-args
                post_args = [
                    "--postprocessor-args",
                    "ffmpeg:-an",
                ]

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
                if self.stop_flag.is_set():
                    break
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
            if self.current_proc.returncode == 0 and not self.stop_flag.is_set():
                self.progress_label.configure(text="Download complete")
            elif self.stop_flag.is_set():
                self.progress_label.configure(text="Stopped")
            else:
                self.progress_label.configure(text="Download failed")
        except Exception as e:
            self.progress_label.configure(text=f"Error: {e}")
        finally:
            self.current_proc = None

    # ----------------------
    # Background Animation
    # ----------------------
    def _start_bg_animation(self) -> None:
        self._animate_background()

    def _animate_background(self) -> None:
        w = self.bg_canvas.winfo_width() or self.root.winfo_width()
        h = self.bg_canvas.winfo_height() or self.root.winfo_height()
        self.bg_canvas.delete("all")

        # Smooth animated gradient stripes
        steps = 48
        phase = self._gradient_phase
        for i in range(steps):
            t = ((i + phase) % steps) / steps
            # Interpolate between deep blue and almost black
            r = int(5 + 10 * (1 - t))
            g = int(12 + 30 * t)
            b = int(22 + 70 * (1 - t))
            color = f"#{r:02x}{g:02x}{b:02x}"
            x0 = i * w / steps
            x1 = (i + 1) * w / steps + 1
            self.bg_canvas.create_rectangle(x0, 0, x1, h, fill=color, outline="")

        # Soft glow circles
        for j in range(3):
            t = (phase / 30.0 + j * 0.33) % 1.0
            cx = int(w * (0.2 + 0.6 * t))
            cy = int(h * (0.3 + 0.4 * (1 - t)))
            radius = int(120 + 50 * (1 - t))
            glow = f"#{int(10+15*(1-t)):02x}{int(30+40*t):02x}{int(60+70*(1-t)):02x}"
            self.bg_canvas.create_oval(
                cx - radius,
                cy - radius,
                cx + radius,
                cy + radius,
                fill=glow,
                outline="",
            )

        self._gradient_phase = (self._gradient_phase + 1) % steps
        self.root.after(100, self._animate_background)

    # ----------------------
    # Close
    # ----------------------
    def on_close(self) -> None:
        if self.current_proc and self.current_proc.poll() is None:
            if not messagebox.askyesno("Confirm", "Download in progress. Exit?"):
                return
            self.stop_current()
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
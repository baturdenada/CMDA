"""
Continue_My_Dear_Agent (CMDA)
Automated Cooldown Timer & Resume Agent for AI Desktop Apps, CLI, IDEs, and Web.
"""

import os
import sys
import time
import datetime
import threading
import subprocess
import ctypes
from ctypes import wintypes
import tkinter as tk
from tkinter import ttk, messagebox
import pyautogui
import pyperclip

# Windows Constants
SW_HIDE = 0
SW_SHOWNORMAL = 1
SW_SHOWMINIMIZED = 2
SW_MAXIMIZE = 3
SW_SHOW = 5
SW_RESTORE = 9

ES_CONTINUOUS = 0x80000000
ES_SYSTEM_REQUIRED = 0x00000001
ES_DISPLAY_REQUIRED = 0x00000002

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

def attach_to_default_desktop():
    """Ensure the current thread is attached to the interactive user desktop."""
    try:
        h_desk = user32.OpenDesktopW("default", 0, False, 0x01FF)
        if h_desk:
            user32.SetThreadDesktop(h_desk)
            return True
    except Exception as e:
        print("Desktop attach error:", e)
    return False

def prevent_pc_sleep():
    """Prevent Windows from sleeping while waiting."""
    try:
        kernel32.SetThreadExecutionState(ES_CONTINUOUS | ES_SYSTEM_REQUIRED | ES_DISPLAY_REQUIRED)
        return True
    except Exception as e:
        print("Prevent sleep error:", e)
        return False

def restore_pc_sleep():
    """Restore normal Windows sleep behavior."""
    try:
        kernel32.SetThreadExecutionState(ES_CONTINUOUS)
    except Exception as e:
        print("Restore sleep error:", e)

def find_app_window(target: str):
    """
    Finds visible top-level window matching target on the interactive desktop.
    Supports Claude, ChatGPT, Cursor, VS Code, Terminal, Chrome, Edge, or custom titles.
    Returns (hwnd, window_title) or (None, None).
    """
    attach_to_default_desktop()
    h_desk = user32.OpenDesktopW("default", 0, False, 0x01FF)
    if not h_desk:
        return None, None

    found = []
    target_lower = target.lower().strip()
    if not target_lower:
        return None, None

    WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
    def enum_cb(hwnd, lparam):
        if user32.IsWindowVisible(hwnd):
            length = user32.GetWindowTextLengthW(hwnd)
            if length > 0:
                buf = ctypes.create_unicode_buffer(length + 1)
                user32.GetWindowTextW(hwnd, buf, length + 1)
                title = buf.value.strip()
                if target_lower in title.lower():
                    # Filter out self
                    if "AI Auto-Continue Agent" not in title and "CMDA" not in title:
                        found.append((hwnd, title))
        return True

    user32.EnumDesktopWindows(h_desk, WNDENUMPROC(enum_cb), 0)
    if found:
        return found[0]
    return None, None

def launch_app(target: str):
    """Launch the app via its registered Windows Store / AppsFolder AppID if known."""
    app_ids = {
        "claude": "Claude_pzs8sxrjxfjjc!Claude",
        "chatgpt": "OpenAI.Codex_2p2nqsd0c76g0!App"
    }
    app_id = app_ids.get(target.lower())
    if app_id:
        try:
            subprocess.Popen(["explorer.exe", f"shell:AppsFolder\\{app_id}"])
            return True
        except Exception as e:
            print("Launch error:", e)
    return False

def activate_and_send(target: str, message: str, auto_click: bool = True, log_func=None):
    """
    Brings target window to foreground, restores it, focuses input, pastes message, and presses Enter.
    """
    def log(msg):
        if log_func:
            log_func(msg)
        print(f"[*] {msg}")

    attach_to_default_desktop()

    hwnd, title = find_app_window(target)
    if not hwnd and target.lower() in ["claude", "chatgpt"]:
        log(f"Window for {target.capitalize()} not found. Attempting to launch...")
        launch_app(target)
        time.sleep(4)
        hwnd, title = find_app_window(target)

    if not hwnd:
        log(f"Error: Could not find window matching '{target}'. Please ensure it is open.")
        return False

    log(f"Found '{title}' (HWND: {hwnd}). Bringing to foreground...")

    # Restore if minimized
    user32.ShowWindow(hwnd, SW_RESTORE)
    user32.ShowWindow(hwnd, SW_SHOW)
    time.sleep(0.3)

    # Attach input thread to bypass Windows foreground lock
    fg_hwnd = user32.GetForegroundWindow()
    fg_thread = user32.GetWindowThreadProcessId(fg_hwnd, None)
    cur_thread = kernel32.GetCurrentThreadId()

    if fg_thread != cur_thread:
        user32.AttachThreadInput(cur_thread, fg_thread, True)

    user32.keybd_event(0x12, 0, 0, 0) # Alt down
    user32.keybd_event(0x12, 0, 2, 0) # Alt up

    user32.SetForegroundWindow(hwnd)
    user32.BringWindowToTop(hwnd)

    if fg_thread != cur_thread:
        user32.AttachThreadInput(cur_thread, fg_thread, False)

    time.sleep(0.6)

    # Get window rect
    rect = wintypes.RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(rect))
    w = rect.right - rect.left
    h = rect.bottom - rect.top

    # Only click near bottom if auto_click is checked and it's a GUI app window
    is_terminal = any(term in title.lower() for term in ["terminal", "powershell", "cmd", "bash", "wsl"])
    if auto_click and not is_terminal and w > 250 and h > 250:
        click_x = rect.left + (w // 2)
        click_y = rect.bottom - 75
        log(f"Focusing chat input area at ({click_x}, {click_y})...")
        pyautogui.click(click_x, click_y)
        time.sleep(0.3)

    log(f"Pasting message: '{message}'...")
    pyperclip.copy(message)
    time.sleep(0.2)
    pyautogui.hotkey("ctrl", "v")
    time.sleep(0.4)

    log("Pressing Enter to submit...")
    pyautogui.press("enter")
    time.sleep(0.2)

    log("Successfully submitted!")
    return True


class AutoContinueApp:
    def __init__(self, root):
        self.root = root
        self.root.title("CMDA - Continue My Dear Agent")
        self.root.geometry("680x760")
        self.root.minsize(620, 700)

        # Style & Colors
        self.bg_color = "#18181b"
        self.card_bg = "#27272a"
        self.card_border = "#3f3f46"
        self.text_color = "#f4f4f5"
        self.text_muted = "#a1a1aa"
        self.accent_green = "#22c55e"
        self.accent_purple = "#a855f7"
        self.accent_blue = "#3b82f6"
        self.accent_red = "#ef4444"

        self.root.configure(bg=self.bg_color)

        self.timer_thread = None
        self.is_running = False
        self.target_time = None
        self.total_seconds = 0
        self.remaining_seconds = 0

        self.target_app_var = tk.StringVar(value="claude")
        self.custom_app_var = tk.StringVar(value="Cursor")
        self.mode_var = tk.StringVar(value="duration")
        self.hours_var = tk.StringVar(value="5")
        self.minutes_var = tk.StringVar(value="0")
        self.clock_var = tk.StringVar(value="")
        self.message_var = tk.StringVar(value="continue")
        self.keep_awake_var = tk.BooleanVar(value=True)
        self.auto_click_var = tk.BooleanVar(value=True)

        self.setup_ui()
        self.refresh_app_status()
        self.update_target_preview()

    def get_effective_target(self):
        val = self.target_app_var.get()
        if val == "custom":
            return self.custom_app_var.get().strip() or "Cursor"
        return val

    def setup_ui(self):
        main_frame = tk.Frame(self.root, bg=self.bg_color)
        main_frame.pack(fill="both", expand=True, padx=20, pady=16)

        # 1. Header
        header_frame = tk.Frame(main_frame, bg=self.bg_color)
        header_frame.pack(fill="x", pady=(0, 14))

        title_lbl = tk.Label(
            header_frame, text="⚡ CMDA — Continue My Dear Agent",
            font=("Segoe UI", 16, "bold"), fg=self.text_color, bg=self.bg_color
        )
        title_lbl.pack(anchor="w")

        sub_lbl = tk.Label(
            header_frame, text="Universal resume timer for Claude, ChatGPT, Cursor, IDEs, CLI & Web chats",
            font=("Segoe UI", 9), fg=self.text_muted, bg=self.bg_color
        )
        sub_lbl.pack(anchor="w", pady=(2, 0))

        # 2. Target App Card
        app_card = self.create_card(main_frame, "1. Select Target Application (Desktop / IDE / CLI / Web)")
        app_card.pack(fill="x", pady=(0, 12))

        app_btns_frame = tk.Frame(app_card, bg=self.card_bg)
        app_btns_frame.pack(fill="x", padx=14, pady=(10, 6))

        # Claude Radio
        claude_rb = tk.Radiobutton(
            app_btns_frame, text="🟣 Claude Desktop", variable=self.target_app_var,
            value="claude", font=("Segoe UI", 10, "bold"), fg="#d8b4fe",
            bg=self.card_bg, activebackground=self.card_bg, activeforeground="#d8b4fe",
            selectcolor="#3b0764", command=self.on_app_selected
        )
        claude_rb.grid(row=0, column=0, sticky="w", padx=(0, 16))

        # ChatGPT Radio
        chatgpt_rb = tk.Radiobutton(
            app_btns_frame, text="🟢 ChatGPT Desktop", variable=self.target_app_var,
            value="chatgpt", font=("Segoe UI", 10, "bold"), fg="#86efac",
            bg=self.card_bg, activebackground=self.card_bg, activeforeground="#86efac",
            selectcolor="#064e3b", command=self.on_app_selected
        )
        chatgpt_rb.grid(row=0, column=1, sticky="w", padx=(0, 16))

        # Custom Radio
        custom_rb = tk.Radiobutton(
            app_btns_frame, text="💻 Custom (IDE / CLI / Web)", variable=self.target_app_var,
            value="custom", font=("Segoe UI", 10, "bold"), fg="#93c5fd",
            bg=self.card_bg, activebackground=self.card_bg, activeforeground="#93c5fd",
            selectcolor="#1e3a8a", command=self.on_app_selected
        )
        custom_rb.grid(row=0, column=2, sticky="w")

        # Custom app entry row
        self.custom_row = tk.Frame(app_card, bg=self.card_bg)
        self.custom_row.pack(fill="x", padx=14, pady=(0, 8))

        tk.Label(self.custom_row, text="Window Title Keyword:", font=("Segoe UI", 8, "bold"), fg=self.text_muted, bg=self.card_bg).pack(side="left", padx=(0, 6))
        self.custom_entry = tk.Entry(
            self.custom_row, textvariable=self.custom_app_var, font=("Segoe UI", 9),
            bg="#18181b", fg=self.text_color, insertbackground="white", relief="solid", width=18
        )
        self.custom_entry.pack(side="left", padx=(0, 10))
        self.custom_entry.bind("<KeyRelease>", lambda e: self.refresh_app_status())

        # Quick preset pills for custom
        custom_pills = [("Cursor", "Cursor"), ("VS Code", "Visual Studio Code"), ("Terminal", "Terminal"), ("Chrome", "Chrome"), ("Edge", "Edge")]
        for p_label, p_val in custom_pills:
            p_btn = tk.Button(
                self.custom_row, text=p_label, font=("Segoe UI", 8),
                fg=self.text_color, bg="#3f3f46", activebackground="#52525b",
                relief="flat", cursor="hand2", padx=4, pady=1,
                command=lambda v=p_val: self.set_custom_target(v)
            )
            p_btn.pack(side="left", padx=(0, 4))

        # Status row
        status_row = tk.Frame(app_card, bg=self.card_bg)
        status_row.pack(fill="x", padx=14, pady=(0, 10))

        self.app_status_lbl = tk.Label(
            status_row, text="Scanning for target app...",
            font=("Segoe UI", 9), fg=self.text_muted, bg=self.card_bg
        )
        self.app_status_lbl.pack(side="left")

        refresh_btn = tk.Button(
            status_row, text="🔄 Refresh Status", font=("Segoe UI", 8),
            fg=self.text_color, bg="#3f3f46", activebackground="#52525b",
            relief="flat", cursor="hand2", command=self.refresh_app_status
        )
        refresh_btn.pack(side="right")

        # 3. Timer & Schedule Card
        timer_card = self.create_card(main_frame, "2. Schedule Cooldown Wait Time")
        timer_card.pack(fill="x", pady=(0, 12))

        timer_inner = tk.Frame(timer_card, bg=self.card_bg)
        timer_inner.pack(fill="x", padx=14, pady=10)

        # Mode
        mode_frame = tk.Frame(timer_inner, bg=self.card_bg)
        mode_frame.pack(fill="x", pady=(0, 8))

        dur_rb = tk.Radiobutton(
            mode_frame, text="Countdown Timer", variable=self.mode_var,
            value="duration", font=("Segoe UI", 9, "bold"), fg=self.text_color,
            bg=self.card_bg, activebackground=self.card_bg, selectcolor="#3f3f46",
            command=self.update_target_preview
        )
        dur_rb.pack(side="left", padx=(0, 16))

        # Duration Inputs
        self.dur_inputs_frame = tk.Frame(timer_inner, bg=self.card_bg)
        self.dur_inputs_frame.pack(fill="x", pady=(0, 6))

        tk.Label(self.dur_inputs_frame, text="Hours:", font=("Segoe UI", 9), fg=self.text_color, bg=self.card_bg).pack(side="left", padx=(0, 4))
        self.hours_spin = tk.Spinbox(
            self.dur_inputs_frame, from_=0, to=24, width=4, textvariable=self.hours_var,
            font=("Segoe UI", 10), bg="#18181b", fg=self.text_color, insertbackground="white",
            relief="solid", command=self.update_target_preview
        )
        self.hours_spin.pack(side="left", padx=(0, 12))
        self.hours_spin.bind("<KeyRelease>", lambda e: self.update_target_preview())

        tk.Label(self.dur_inputs_frame, text="Minutes:", font=("Segoe UI", 9), fg=self.text_color, bg=self.card_bg).pack(side="left", padx=(0, 4))
        self.mins_spin = tk.Spinbox(
            self.dur_inputs_frame, from_=0, to=59, width=4, textvariable=self.minutes_var,
            font=("Segoe UI", 10), bg="#18181b", fg=self.text_color, insertbackground="white",
            relief="solid", command=self.update_target_preview
        )
        self.mins_spin.pack(side="left", padx=(0, 16))
        self.mins_spin.bind("<KeyRelease>", lambda e: self.update_target_preview())

        # Presets
        presets_frame = tk.Frame(timer_inner, bg=self.card_bg)
        presets_frame.pack(fill="x", pady=(0, 8))

        presets = [("5 Hours", 5, 0), ("4h 30m", 4, 30), ("3 Hours", 3, 0), ("1 Hour", 1, 0), ("30 Min", 0, 30), ("1 Min (Test)", 0, 1)]
        for label, h, m in presets:
            btn = tk.Button(
                presets_frame, text=label, font=("Segoe UI", 8),
                fg=self.text_color, bg="#3f3f46", activebackground="#52525b",
                relief="flat", cursor="hand2", padx=6, pady=2,
                command=lambda h=h, m=m: self.set_preset(h, m)
            )
            btn.pack(side="left", padx=(0, 6))

        # Dynamic trigger preview
        self.preview_lbl = tk.Label(
            timer_inner, text="Will trigger at: calculating...",
            font=("Segoe UI", 9, "bold"), fg=self.accent_green, bg=self.card_bg
        )
        self.preview_lbl.pack(anchor="w", pady=(4, 0))

        # 4. Message & Options Card
        msg_card = self.create_card(main_frame, "3. Prompt & Automation Settings")
        msg_card.pack(fill="x", pady=(0, 12))

        msg_inner = tk.Frame(msg_card, bg=self.card_bg)
        msg_inner.pack(fill="x", padx=14, pady=10)

        msg_row = tk.Frame(msg_inner, bg=self.card_bg)
        msg_row.pack(fill="x", pady=(0, 8))

        tk.Label(msg_row, text="Message to send:", font=("Segoe UI", 9), fg=self.text_color, bg=self.card_bg).pack(side="left", padx=(0, 8))
        msg_entry = tk.Entry(
            msg_row, textvariable=self.message_var, font=("Segoe UI", 10),
            bg="#18181b", fg=self.text_color, insertbackground="white", relief="solid"
        )
        msg_entry.pack(side="left", fill="x", expand=True)

        # Options checkmarks
        opts_frame = tk.Frame(msg_inner, bg=self.card_bg)
        opts_frame.pack(fill="x")

        awake_cb = tk.Checkbutton(
            opts_frame, text="Keep PC awake while countdown is running (prevents Windows sleep)",
            variable=self.keep_awake_var, font=("Segoe UI", 9), fg=self.text_color,
            bg=self.card_bg, activebackground=self.card_bg, selectcolor="#3f3f46"
        )
        awake_cb.pack(anchor="w")

        click_cb = tk.Checkbutton(
            opts_frame, text="Auto-click chat box before typing (recommended for GUI apps)",
            variable=self.auto_click_var, font=("Segoe UI", 9), fg=self.text_color,
            bg=self.card_bg, activebackground=self.card_bg, selectcolor="#3f3f46"
        )
        click_cb.pack(anchor="w")

        # 5. Big Control Buttons
        ctrl_frame = tk.Frame(main_frame, bg=self.bg_color)
        ctrl_frame.pack(fill="x", pady=(0, 12))

        self.start_btn = tk.Button(
            ctrl_frame, text="▶  START TIMER", font=("Segoe UI", 11, "bold"),
            fg="#052e16", bg=self.accent_green, activebackground="#4ade80",
            relief="flat", cursor="hand2", pady=8, command=self.start_timer
        )
        self.start_btn.pack(side="left", fill="x", expand=True, padx=(0, 8))

        self.cancel_btn = tk.Button(
            ctrl_frame, text="⏹  CANCEL", font=("Segoe UI", 11, "bold"),
            fg=self.text_color, bg="#3f3f46", activebackground="#52525b",
            relief="flat", cursor="hand2", pady=8, state="disabled", command=self.cancel_timer
        )
        self.cancel_btn.pack(side="left", padx=(0, 8))

        self.test_btn = tk.Button(
            ctrl_frame, text="⚡ TEST NOW (3s delay)", font=("Segoe UI", 9, "bold"),
            fg="#1e1b4b", bg="#818cf8", activebackground="#a5b4fc",
            relief="flat", cursor="hand2", pady=8, command=self.run_test_now
        )
        self.test_btn.pack(side="left")

        # 6. Countdown Live Display
        self.live_card = tk.Frame(main_frame, bg="#27272a", bd=1, relief="solid")
        self.live_card.pack(fill="x", pady=(0, 12))

        live_inner = tk.Frame(self.live_card, bg="#27272a")
        live_inner.pack(fill="x", padx=14, pady=10)

        self.countdown_lbl = tk.Label(
            live_inner, text="STATUS: READY",
            font=("Segoe UI", 18, "bold"), fg=self.text_muted, bg="#27272a"
        )
        self.countdown_lbl.pack()

        self.progress_var = tk.DoubleVar(value=0.0)
        self.progress_bar = ttk.Progressbar(live_inner, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill="x", pady=(8, 4))

        # 7. Activity Log
        log_frame = tk.Frame(main_frame, bg=self.bg_color)
        log_frame.pack(fill="both", expand=True)

        tk.Label(log_frame, text="Activity Log:", font=("Segoe UI", 9, "bold"), fg=self.text_muted, bg=self.bg_color).pack(anchor="w")

        self.log_text = tk.Text(
            log_frame, height=5, bg="#09090b", fg="#e4e4e7",
            font=("Consolas", 9), relief="solid", bd=1, wrap="word"
        )
        self.log_text.pack(fill="both", expand=True, pady=(2, 0))
        self.log_msg("Ready. Select target and duration, then click START TIMER.")

    def create_card(self, parent, title):
        card = tk.Frame(parent, bg=self.card_bg, bd=1, relief="solid")
        hdr = tk.Label(
            card, text=f"  {title}", font=("Segoe UI", 10, "bold"),
            fg=self.text_color, bg="#3f3f46", anchor="w", pady=4
        )
        hdr.pack(fill="x")
        return card

    def log_msg(self, text):
        now_str = datetime.datetime.now().strftime("%H:%M:%S")
        self.log_text.insert("end", f"[{now_str}] {text}\n")
        self.log_text.see("end")

    def set_custom_target(self, name):
        self.custom_app_var.set(name)
        self.target_app_var.set("custom")
        self.refresh_app_status()

    def on_app_selected(self):
        self.refresh_app_status()
        self.update_target_preview()

    def refresh_app_status(self):
        target = self.get_effective_target()
        hwnd, title = find_app_window(target)
        if hwnd:
            self.app_status_lbl.config(
                text=f"● '{target}' is OPEN (Window: '{title}')",
                fg=self.accent_green
            )
        else:
            self.app_status_lbl.config(
                text=f"○ '{target}' not detected on screen (Ensure it is open)",
                fg="#facc15"
            )

    def set_preset(self, h, m):
        self.hours_var.set(str(h))
        self.minutes_var.set(str(m))
        self.mode_var.set("duration")
        self.update_target_preview()

    def update_target_preview(self):
        if self.is_running:
            return

        try:
            h = int(self.hours_var.get() or 0)
            m = int(self.minutes_var.get() or 0)
            total_sec = (h * 3600) + (m * 60)
            if total_sec > 0:
                t = datetime.datetime.now() + datetime.timedelta(seconds=total_sec)
                self.preview_lbl.config(
                    text=f"Target: Today at {t.strftime('%I:%M:%S %p')} (in {h}h {m}m)",
                    fg=self.accent_green
                )
            else:
                self.preview_lbl.config(text="Please set a duration greater than 0", fg="#facc15")
        except Exception:
            self.preview_lbl.config(text="Invalid time values", fg=self.accent_red)

    def run_test_now(self):
        if self.is_running:
            messagebox.showinfo("Busy", "A timer is already running. Please cancel it first.")
            return

        target = self.get_effective_target()
        msg = self.message_var.get().strip() or "continue"
        auto_click = self.auto_click_var.get()

        self.log_msg(f"Test initiated for '{target}'! Triggering in 3 seconds...")
        self.test_btn.config(state="disabled")

        def test_worker():
            for i in range(3, 0, -1):
                self.countdown_lbl.config(
                    text=f"TESTING IN {i}s...",
                    fg="#818cf8"
                )
                time.sleep(1)

            self.countdown_lbl.config(text="ACTIVATING TARGET...", fg=self.accent_green)
            success = activate_and_send(target, msg, auto_click=auto_click, log_func=self.log_msg)

            self.root.after(0, lambda: self.finish_test(success))

        threading.Thread(target=test_worker, daemon=True).start()

    def finish_test(self, success):
        self.test_btn.config(state="normal")
        self.countdown_lbl.config(
            text="TEST COMPLETED" if success else "TEST FAILED",
            fg=self.accent_green if success else self.accent_red
        )
        self.refresh_app_status()

    def start_timer(self):
        try:
            h = int(self.hours_var.get() or 0)
            m = int(self.minutes_var.get() or 0)
            self.total_seconds = (h * 3600) + (m * 60)
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter valid numbers for Hours and Minutes.")
            return

        if self.total_seconds <= 0:
            messagebox.showwarning("Zero Duration", "Please set a duration greater than 0.")
            return

        self.is_running = True
        self.remaining_seconds = self.total_seconds
        self.target_time = datetime.datetime.now() + datetime.timedelta(seconds=self.total_seconds)

        target = self.get_effective_target()
        msg = self.message_var.get().strip() or "continue"

        if self.keep_awake_var.get():
            prevent_pc_sleep()
            self.log_msg("PC Keep-Awake enabled (will prevent sleep while waiting).")

        self.log_msg(f"Timer started! Target: {self.target_time.strftime('%I:%M:%S %p')} for '{target}'.")

        self.start_btn.config(state="disabled", bg="#27272a", fg=self.text_muted)
        self.cancel_btn.config(state="normal", bg=self.accent_red)
        self.test_btn.config(state="disabled")

        self.timer_thread = threading.Thread(target=self.countdown_loop, daemon=True)
        self.timer_thread.start()

    def countdown_loop(self):
        target = self.get_effective_target()
        msg = self.message_var.get().strip() or "continue"
        auto_click = self.auto_click_var.get()

        while self.is_running and self.remaining_seconds > 0:
            hrs = self.remaining_seconds // 3600
            mins = (self.remaining_seconds % 3600) // 60
            secs = self.remaining_seconds % 60
            time_str = f"{hrs:02d}:{mins:02d}:{secs:02d}"

            pct = ((self.total_seconds - self.remaining_seconds) / self.total_seconds) * 100
            self.progress_var.set(pct)

            self.countdown_lbl.config(
                text=f"REMAINING: {time_str}",
                fg=self.accent_green
            )

            time.sleep(1)
            self.remaining_seconds -= 1

        if self.is_running:
            self.countdown_lbl.config(text="TRIGGERING RESUME...", fg=self.accent_green)
            self.progress_var.set(100.0)
            self.log_msg(f"Timer reached! Resuming conversation on '{target}'...")

            success = activate_and_send(target, msg, auto_click=auto_click, log_func=self.log_msg)

            if self.keep_awake_var.get():
                restore_pc_sleep()

            self.is_running = False
            self.root.after(0, lambda: self.on_timer_finished(success))

    def on_timer_finished(self, success):
        self.start_btn.config(state="normal", bg=self.accent_green, fg="#052e16")
        self.cancel_btn.config(state="disabled", bg="#3f3f46")
        self.test_btn.config(state="normal")
        self.countdown_lbl.config(
            text="PROMPT SENT SUCCESSFULLY!" if success else "EXECUTION FAILED",
            fg=self.accent_green if success else self.accent_red
        )
        self.log_msg("Task complete. Ready for next schedule.")

    def cancel_timer(self):
        if not self.is_running:
            return

        self.is_running = False
        restore_pc_sleep()
        self.log_msg("Timer cancelled by user.")

        self.start_btn.config(state="normal", bg=self.accent_green, fg="#052e16")
        self.cancel_btn.config(state="disabled", bg="#3f3f46")
        self.test_btn.config(state="normal")
        self.countdown_lbl.config(text="CANCELLED", fg="#facc15")
        self.progress_var.set(0.0)


def main():
    attach_to_default_desktop()
    root = tk.Tk()
    ico_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app_icon.ico")
    if os.path.exists(ico_path):
        try:
            root.iconbitmap(ico_path)
        except Exception:
            pass
    app = AutoContinueApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()

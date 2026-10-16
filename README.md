# ⚡ CMDA — Continue_My_Dear_Agent

<div align="center">

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)
![Platform](https://img.shields.io/badge/Platform-Windows-0078D6?logo=windows&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)
![Status](https://img.shields.io/badge/Status-Active-brightgreen)

**An intelligent, lightweight desktop automation agent that automatically resumes your AI conversations when usage limits reset.**

*Supports Claude Desktop, ChatGPT Desktop, Cursor, VS Code, AI CLI tools, and Web browsers.*

</div>

---

## 💡 Why CMDA?

When working on complex coding tasks or long conversations with state-of-the-art AI models, hitting a rate limit is frustrating:

> *"You've reached your Claude 3.5 Sonnet limit. Usage resets in 5 hours."*  
> *"You've reached your ChatGPT limit until 06:30 AM."*

Instead of setting an alarm, interrupting your sleep, or constantly checking the clock, **CMDA (Continue_My_Dear_Agent)** waits out the cooldown period, prevents your PC from falling into deep sleep, automatically restores your active window, and types `"continue"` into the chat box so your work immediately picks back up.

---

## 🌟 Key Features

* **Universal Compatibility:** Works out-of-the-box with **Desktop Apps**, **IDEs**, **CLI Terminals**, and **Web Browsers**.
* **Pre-Configured App Profiles:** One-click presets for **Claude Desktop** and **ChatGPT Desktop** with live window detection.
* **Custom Target Selector:** Easily target any IDE (Cursor, VS Code, Windsurf), terminal (Windows Terminal, PowerShell, WSL, Aider, Claude Code), or browser tab (Chrome, Edge).
* **Anti-Sleep Engine:** Keeps your computer awake using Windows API (`SetThreadExecutionState`) without interfering with screen dimming.
* **Foreground Lock Bypass:** Uses Windows thread input attachment and key event pulsing to bring minimized windows reliably to the foreground.
* **Instant Verification (`⚡ TEST NOW`):** A 3-second delay test button lets you verify window focus, paste, and submit immediately before starting a multi-hour countdown.
* **Desktop Shortcut Generator:** Generates a `.lnk` shortcut with a custom high-resolution icon and silent background launcher (`pythonw.exe`).
* **Multi-Instance Ready:** Run two instances side-by-side to track cooldowns on both Claude and ChatGPT simultaneously.

---

## 🖥️ How It Works (Universal Target Guide)

CMDA uses dynamic window enumeration and Windows subsystem hooks, allowing it to target any interface:

| Target Category | Examples | How to Use in CMDA |
| :--- | :--- | :--- |
| **Desktop Apps** | Claude Desktop, ChatGPT Windows App | Select `🟣 Claude` or `🟢 ChatGPT` directly |
| **AI IDEs** | Cursor, VS Code (Copilot / Continue), Windsurf | Select `💻 Custom` → click `Cursor` or `VS Code` |
| **CLI / Terminals** | Aider, Claude Code, Gemini CLI, PowerShell, WSL | Select `💻 Custom` → click `Terminal` |
| **Web Browsers** | ChatGPT Web, Claude Web in Chrome / Edge / Brave | Select `💻 Custom` → click `Chrome` or `Edge` |

---

## 🎨 GUI Design & Layout

CMDA is designed with a modern, dark-themed dashboard:

1. **Header:** Status and branding with subtle accent borders.
2. **Target Selector:** Radio cards with live connection badges:
   * `● OPEN` (green): Active window detected.
   * `○ NOT DETECTED` (yellow): App is not open yet (CMDA can launch registered apps automatically).
3. **Cooldown Presets:** Quick pill buttons for `5 Hours`, `4h 30m`, `3 Hours`, `1 Hour`, `30 Min`, or `1 Min (Test)`.
4. **Target Time Preview:** Dynamically calculates and displays the exact clock timestamp (e.g. *Today at 06:15:00 AM*).
5. **Prompt Customization:** Default is `"continue"`, or enter custom prompts like `"Please continue where you left off"`.
6. **Smart Safety Toggles:**
   * `[x] Keep PC awake while countdown is running`
   * `[x] Auto-click chat box before typing` (ensures cursor focus in Electron/GUI apps)
7. **Action Center:**
   * `▶ START TIMER`: Arms the scheduler.
   * `⏹ CANCEL`: Aborts the active timer anytime.
   * `⚡ TEST NOW (3s delay)`: Runs an immediate 3-second dry run.
8. **Live Countdown & Activity Log:** Real-time countdown timer, progress bar, and timestamped audit log.

---

## 🚀 Quickstart & Installation

### 1. Prerequisites
* **Windows 10 / 11**
* **Python 3.10+**

### 2. Clone Repository
```bash
git clone https://github.com/baturdenada/CMDA.git
cd CMDA
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Create Desktop Shortcut (Optional but Recommended)
Run the shortcut creator to add a one-click desktop icon with custom artwork:
```bash
python create_shortcut.py
```

### 5. Launch CMDA
```bash
# Launch directly
python app.py

# Or silent launch (no command prompt window)
pythonw app.py
```

---

## ⚙️ Architecture & Technical Details

### 1. Windows Interactive Desktop Bridging
Electron and UWP apps run on the interactive user desktop (`WinSta0\default`). CMDA explicitly attaches background execution threads to `OpenDesktopW("default")` so it can enumerate, restore, and focus windows even when started from background tasks or secondary desktops.

### 2. Focus Stealing Lock Bypass
Windows enforces restrictions against background processes taking focus (`LockSetForegroundWindow`). CMDA bypasses this cleanly by:
1. Identifying the current foreground thread (`GetWindowThreadProcessId`).
2. Attaching the current thread input queue to the active foreground thread (`AttachThreadInput`).
3. Emitting a synthetic Alt key pulse (`keybd_event(0x12, ...)`).
4. Calling `SetForegroundWindow` and `BringWindowToTop`.
5. Detaching the thread input queue.

### 3. Sleep Prevention
To prevent Windows from suspending background execution while you are away:
```python
ctypes.windll.kernel32.SetThreadExecutionState(
    ES_CONTINUOUS | ES_SYSTEM_REQUIRED | ES_DISPLAY_REQUIRED
)
```
When the timer expires or is cancelled, power settings are automatically restored to default.

---

## 🤝 Contributing

Contributions, issues, and feature requests are welcome!
Feel free to open an issue or submit a pull request.

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).

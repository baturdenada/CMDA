import os
import sys

try:
    import win32com.client
    use_com = True
except ImportError:
    use_com = False

desktop = os.path.join(os.path.expanduser("~"), "Desktop")
shortcut_path = os.path.join(desktop, "AI Auto-Continue.lnk")

python_dir = os.path.dirname(sys.executable)
pythonw_path = os.path.join(python_dir, "pythonw.exe")
app_dir = r"c:\Users\Administrator\Documents\Antigravity\AutoContinueAgent"
app_script = os.path.join(app_dir, "app.py")
icon_path = os.path.join(app_dir, "app_icon.ico")

if use_com:
    shell = win32com.client.Dispatch("WScript.Shell")
    shortcut = shell.CreateShortCut(shortcut_path)
    shortcut.TargetPath = pythonw_path
    shortcut.Arguments = f'"{app_script}"'
    shortcut.WorkingDirectory = app_dir
    shortcut.IconLocation = f"{icon_path},0"
    shortcut.Description = "AI Auto-Continue Agent for Claude & ChatGPT"
    shortcut.Save()
    print("Shortcut created via COM at:", shortcut_path)
else:
    # Fallback to powershell script
    ps_cmd = f"""
    $WshShell = New-Object -ComObject WScript.Shell
    $Shortcut = $WshShell.CreateShortcut('{shortcut_path}')
    $Shortcut.TargetPath = '{pythonw_path}'
    $Shortcut.Arguments = '"{app_script}"'
    $Shortcut.WorkingDirectory = '{app_dir}'
    $Shortcut.IconLocation = '{icon_path},0'
    $Shortcut.Description = 'AI Auto-Continue Agent for Claude & ChatGPT'
    $Shortcut.Save()
    """
    import subprocess
    subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd], check=True)
    print("Shortcut created via PowerShell at:", shortcut_path)

# Clean up old bat file on Desktop if present
bat_path = os.path.join(desktop, "AI Auto-Continue.bat")
if os.path.exists(bat_path):
    try:
        os.remove(bat_path)
        print("Removed legacy .bat file from Desktop.")
    except Exception as e:
        print("Could not remove old bat:", e)

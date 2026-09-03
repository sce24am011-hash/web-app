import os
import sys
import subprocess
import shutil

def run_command(cmd, cwd=None):
    print(f" -> Running: {' '.join(cmd)}")
    res = subprocess.run(cmd, cwd=cwd)
    return res.returncode == 0

def install_system():
    print("=" * 65)
    print("    DeepCheck Classroom - Complete Installation & Setup")
    print("=" * 65)
    
    workspace = os.path.abspath(os.path.dirname(__file__))
    frontend_dir = os.path.join(workspace, "frontend")
    backend_dir = os.path.join(workspace, "backend")

    # 1. Install Backend Python Dependencies
    print("\n[Step 1/4] Installing Python Backend dependencies...")
    req_file = os.path.join(backend_dir, "requirements.txt")
    run_command([sys.executable, "-m", "pip", "install", "--quiet", "-r", req_file])

    # 2. Install Frontend NPM Dependencies
    print("\n[Step 2/4] Installing Node.js frontend dependencies...")
    npm_cmd = "npm.cmd" if os.name == "nt" else "npm"
    run_command([npm_cmd, "install"], cwd=frontend_dir)

    # 3. Compile Production PWA Frontend
    print("\n[Step 3/4] Compiling high-performance production frontend bundle...")
    run_command([npm_cmd, "run", "build"], cwd=frontend_dir)

    # 4. Create Desktop Shortcut
    print("\n[Step 4/4] Creating Windows Desktop Application Shortcut...")
    userprofile = os.environ.get("USERPROFILE", "")
    desktop_candidates = [
        os.path.join(userprofile, "OneDrive", "Desktop"),
        os.path.join(userprofile, "Desktop")
    ]
    
    desktop_dir = None
    for d in desktop_candidates:
        if os.path.exists(d):
            desktop_dir = d
            break
            
    if not desktop_dir:
        desktop_dir = desktop_candidates[0]

    shortcut_path = os.path.join(desktop_dir, "DeepCheck Classroom.lnk")
    target_bat = os.path.join(workspace, "launch_app.bat")
    icon_file = os.path.join(frontend_dir, "public", "app_icon.ico")

    ps_commands = [
        "$WshShell = New-Object -ComObject WScript.Shell",
        f'$Shortcut = $WshShell.CreateShortcut("{shortcut_path}")',
        f'$Shortcut.TargetPath = "{target_bat}"',
        f'$Shortcut.WorkingDirectory = "{workspace}"',
        f'$Shortcut.IconLocation = "{icon_file}"',
        '$Shortcut.Description = "DeepCheck Classroom - AI Media Literacy & Analysis Platform"',
        "$Shortcut.Save()",
        f'Write-Host "[OK] Desktop Shortcut successfully created at: {shortcut_path}"'
    ]

    ps_file = os.path.join(workspace, "_make_shortcut.ps1")
    with open(ps_file, "w", encoding="utf-8") as f:
        f.write("\n".join(ps_commands))

    subprocess.run(["powershell", "-ExecutionPolicy", "Bypass", "-File", ps_file])
    if os.path.exists(ps_file):
        os.remove(ps_file)

    print("\n" + "=" * 65)
    print("    INSTALLATION COMPLETE SUCCESSFULLY!")
    print(f" -> Desktop Shortcut created: {shortcut_path}")
    print(f" -> Or double-click: {target_bat}")
    print("=" * 65 + "\n")

if __name__ == "__main__":
    install_system()

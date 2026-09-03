import os
import sys
import subprocess
import shutil

def build_standalone_executable():
    print("=" * 60)
    print("DeepCheck Classroom - Standalone Executable Builder")
    print("=" * 60)
    
    # 1. Build frontend production assets
    print("\n[Step 1/3] Compiling React frontend assets with PWA support...")
    frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'frontend'))
    npm_cmd = 'npm.cmd' if os.name == 'nt' else 'npm'
    res = subprocess.run([npm_cmd, 'run', 'build'], cwd=frontend_dir)
    if res.returncode != 0:
        print("[ERROR] Frontend build failed!")
        return False
        
    # 2. Check for PyInstaller
    print("\n[Step 2/3] Checking PyInstaller availability...")
    try:
        import PyInstaller
        has_pyinstaller = True
    except ImportError:
        has_pyinstaller = False
        
    if not has_pyinstaller:
        print("PyInstaller is not currently installed in this environment.")
        print("To build a single .exe, run: pip install pyinstaller")
        print("Note: You can already run the app natively anytime via: launch_app.bat or python desktop_app.py")
        return True
        
    # 3. Package executable
    print("\n[Step 3/3] Bundling with PyInstaller...")
    dist_assets_src = os.path.join(frontend_dir, 'dist')
    pyinstaller_args = [
        sys.executable, '-m', 'PyInstaller',
        '--name=DeepCheckClassroom',
        '--onefile',
        '--noconsole',
        f'--add-data={dist_assets_src};frontend/dist',
        f'--icon={os.path.join(frontend_dir, "public", "app_icon.ico")}',
        'desktop_app.py'
    ]
    subprocess.run(pyinstaller_args)
    print("\nBuild process complete. Executable located in /dist/DeepCheckClassroom.exe")
    return True

if __name__ == '__main__':
    build_standalone_executable()

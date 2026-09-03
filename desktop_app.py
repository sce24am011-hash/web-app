import os
import sys
import time
import subprocess
import threading
import webbrowser
import shutil
import socket
import argparse

def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('127.0.0.1', port)) == 0

def find_browser_app_executable():
    """Finds Edge or Chrome executable path on Windows / macOS / Linux for App Mode."""
    candidates = [
        # Windows standard paths
        os.path.expandvars(r"%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe"),
        os.path.expandvars(r"%ProgramFiles%\Microsoft\Edge\Application\msedge.exe"),
        os.path.expandvars(r"%LocalAppData%\Microsoft\Edge\Application\msedge.exe"),
        os.path.expandvars(r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%LocalAppData%\Google\Chrome\Application\chrome.exe"),
        # PATH lookups
        shutil.which("msedge"),
        shutil.which("chrome"),
        shutil.which("google-chrome"),
        shutil.which("chromium")
    ]
    for c in candidates:
        if c and os.path.exists(c):
            return c
    return None

def start_backend_server(host, port):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.join(base_dir, 'backend')
    sys.path.insert(0, backend_dir)
    
    os.environ['PORT'] = str(port)
    os.environ['HOST'] = str(host)
    from backend.app_standalone import app
    app.run(host=host, port=port, debug=False, use_reloader=False)

def main():
    parser = argparse.ArgumentParser(description="DeepCheck Classroom Desktop Application Launcher")
    parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", 5050)), help="Port to bind application server (default: 5050)")
    parser.add_argument("--host", type=str, default=os.environ.get("HOST", "127.0.0.1"), help="Host to bind application server (default: 127.0.0.1)")
    parser.add_argument("--proxy-url", type=str, default=os.environ.get("HTTP_PROXY", ""), help="Optional upstream HTTP proxy server URL")
    args = parser.parse_args()

    port = args.port
    host = args.host
    if args.proxy_url:
        os.environ["HTTP_PROXY"] = args.proxy_url
        os.environ["HTTPS_PROXY"] = args.proxy_url
        print(f" -> Upstream HTTP Proxy configured: {args.proxy_url}")

    print("=" * 60)
    print("Starting DeepCheck Classroom Native Desktop Application")
    print(f"Server Host: {host} | Configured Port: {port}")
    print("=" * 60)
    
    while is_port_in_use(port):
        print(f"Port {port} is busy, checking port {port+1}...")
        port += 1

    app_url = f"http://{host}:{port}"
    
    # 1. Start unified server in background thread
    server_thread = threading.Thread(target=start_backend_server, args=(host, port))
    server_thread.daemon = True
    server_thread.start()
    
    print(f" -> Local application server active on {app_url}")
    time.sleep(1.2) # Allow server to bind
    
    # 2. Launch Native App Window
    browser_exe = find_browser_app_executable()
    
    if browser_exe:
        print(f" -> Launching Native App Window using: {os.path.basename(browser_exe)}")
        profile_dir = os.path.join(os.environ.get('LOCALAPPDATA', os.path.expanduser('~')), 'DeepCheckClassroom', 'profile')
        os.makedirs(profile_dir, exist_ok=True)
        app_flags = [
            browser_exe,
            f"--app={app_url}",
            f"--user-data-dir={profile_dir}",
            "--window-size=1280,860",
            "--window-position=center",
            "--disable-features=TranslateUI",
            "--no-default-browser-check",
            "--disable-sync"
        ]
        proc = subprocess.Popen(app_flags)
        print("\nDeepCheck Classroom is now running in Desktop App Mode.")
        print("Close the application window to exit.")
        try:
            proc.wait()
        except KeyboardInterrupt:
            proc.terminate()
    else:
        print(" -> Opening in default browser interface...")
        webbrowser.open(app_url)
        print("\nPress Ctrl+C in this terminal to stop the application server.")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass

    print("DeepCheck Classroom Desktop Application closed.")

if __name__ == '__main__':
    main()

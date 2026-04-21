#!/usr/bin/env python3
"""
DocIntel Launcher - Runs both backend and frontend in a single window
"""

import subprocess
import sys
import os
import time
import signal
import threading
from pathlib import Path

# Colors for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_banner():
    banner = f"""
{Colors.CYAN}{Colors.BOLD}
===============================================================
                                                               
           >> DocIntel - Document Intelligence System          
                                                               
==============================================================={Colors.ENDC}
"""
    print(banner)

def get_venv_python():
    """Find the virtual environment Python executable"""
    script_dir = Path(__file__).parent.resolve()
    
    # Check for .venv
    venv_paths = [
        script_dir / ".venv" / "Scripts" / "python.exe",
        script_dir / "venv" / "Scripts" / "python.exe",
        script_dir / ".venv" / "bin" / "python",
        script_dir / "venv" / "bin" / "python",
    ]
    
    for path in venv_paths:
        if path.exists():
            return str(path)
    
    # Fall back to system python
    return sys.executable

def run_backend(script_dir, python_exe):
    """Run the backend server"""
    backend_dir = script_dir / "backend"
    req_file = backend_dir / "requirements.txt"
    
    # Install requirements if needed
    if req_file.exists():
        print(f"{Colors.YELLOW}[BACKEND] Installing dependencies...{Colors.ENDC}")
        subprocess.run(
            [python_exe, "-m", "pip", "install", "-q", "-r", str(req_file)],
            cwd=str(backend_dir)
        )
    
    print(f"{Colors.GREEN}[BACKEND] Starting FastAPI server on http://127.0.0.1:8000{Colors.ENDC}")
    
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    
    return subprocess.Popen(
        [python_exe, "-m", "uvicorn", "app.fixed_server:app", "--host", "127.0.0.1", "--port", "8000", "--reload"],
        cwd=str(backend_dir),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        env=env,
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0
    )

def run_frontend(script_dir):
    """Run the frontend server"""
    frontend_dir = script_dir / "frontend"
    
    print(f"{Colors.GREEN}[FRONTEND] Starting HTTP server on http://127.0.0.1:3000{Colors.ENDC}")
    
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    
    return subprocess.Popen(
        [sys.executable, "-m", "http.server", "3000"],
        cwd=str(frontend_dir),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        env=env,
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0
    )

def log_output(process, label, color):
    """Log output from a subprocess with a label"""
    try:
        for line in process.stdout:
            line = line.rstrip()
            if line:
                print(f"{color}[{label}]{Colors.ENDC} {line}")
    except Exception:
        pass

def wait_for_server(url, timeout=30):
    """Wait for a server to be ready"""
    import urllib.request
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            urllib.request.urlopen(url, timeout=2)
            return True
        except:
            time.sleep(0.5)
    return False

def open_browser(url):
    """Open the browser"""
    import webbrowser
    webbrowser.open(url)

def main():
    script_dir = Path(__file__).parent.resolve()
    python_exe = get_venv_python()
    
    print_banner()
    print(f"{Colors.CYAN}Using Python: {python_exe}{Colors.ENDC}\n")
    
    backend_proc = None
    frontend_proc = None
    
    def cleanup(signum=None, frame=None):
        print(f"\n{Colors.YELLOW}[SYSTEM] Shutting down servers...{Colors.ENDC}")
        if backend_proc:
            backend_proc.terminate()
        if frontend_proc:
            frontend_proc.terminate()
        time.sleep(1)
        if backend_proc and backend_proc.poll() is None:
            backend_proc.kill()
        if frontend_proc and frontend_proc.poll() is None:
            frontend_proc.kill()
        print(f"{Colors.GREEN}[SYSTEM] All servers stopped. Goodbye!{Colors.ENDC}")
        sys.exit(0)
    
    # Handle Ctrl+C
    signal.signal(signal.SIGINT, cleanup)
    if hasattr(signal, 'SIGTERM'):
        signal.signal(signal.SIGTERM, cleanup)
    
    try:
        # Start backend
        backend_proc = run_backend(script_dir, python_exe)
        
        # Start frontend
        frontend_proc = run_frontend(script_dir)
        
        # Start logging threads
        backend_thread = threading.Thread(target=log_output, args=(backend_proc, "BACKEND", Colors.BLUE), daemon=True)
        frontend_thread = threading.Thread(target=log_output, args=(frontend_proc, "FRONTEND", Colors.CYAN), daemon=True)
        backend_thread.start()
        frontend_thread.start()
        
        # Wait for servers to be ready
        print(f"\n{Colors.YELLOW}[SYSTEM] Waiting for servers to start...{Colors.ENDC}")
        
        backend_ready = wait_for_server("http://127.0.0.1:8000/health", timeout=30)
        frontend_ready = wait_for_server("http://127.0.0.1:3000", timeout=30)
        
        if backend_ready and frontend_ready:
            print(f"\n{Colors.GREEN}{Colors.BOLD}===============================================================")
            print(f"  [OK] Both servers are running!                              ")
            print(f"                                                               ")
            print(f"  [API] Backend:   http://127.0.0.1:8000                       ")
            print(f"  [APP] Frontend:  http://127.0.0.1:3000                       ")
            print(f"                                                               ")
            print(f"  [WEB] Opening browser...                                     ")
            print(f"==============================================================={Colors.ENDC}\n")
            
            time.sleep(1)
            open_browser("http://127.0.0.1:3000")
        else:
            if not backend_ready:
                print(f"{Colors.RED}[ERROR] Backend server failed to start{Colors.ENDC}")
            if not frontend_ready:
                print(f"{Colors.RED}[ERROR] Frontend server failed to start{Colors.ENDC}")
        
        print(f"{Colors.YELLOW}[SYSTEM] Press Ctrl+C to stop all servers{Colors.ENDC}\n")
        
        # Keep main thread alive
        while True:
            backend_alive = backend_proc.poll() is None
            frontend_alive = frontend_proc.poll() is None
            
            if not backend_alive:
                print(f"{Colors.RED}[ERROR] Backend server stopped unexpectedly!{Colors.ENDC}")
                cleanup()
            if not frontend_alive:
                print(f"{Colors.RED}[ERROR] Frontend server stopped unexpectedly!{Colors.ENDC}")
                cleanup()
            
            time.sleep(2)
            
    except KeyboardInterrupt:
        cleanup()
    except Exception as e:
        print(f"{Colors.RED}[ERROR] {e}{Colors.ENDC}")
        cleanup()

if __name__ == "__main__":
    main()

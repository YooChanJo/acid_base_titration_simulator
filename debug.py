# =======================================================
# This script is for debug
# Run: python debug.py or python debug.py VENV_NAME
# =======================================================
import subprocess
import os
import sys

exit_flag = False
def run(name: str = "main", venv: bool = False, venv_name: str | None = None):
    python_exe = "python" if not venv else os.path.join(venv_name, "Scripts" if os.name == "nt" else "bin", "python")
    global exit_flag
    print(f"--- Running {name}.py (Press 'q' to quit, 'r' to restart) ---")
    process = subprocess.Popen(
        [python_exe, "-u", f"{name}.py"], # -u flag for no buffer
    )
    # Runs while the process is alive
    while True:
        cmd = input().lower().strip()
        if cmd == 'q' or cmd == 'r':
            exit_flag = (cmd == 'q')
            process.terminate()
            process.wait()
            print(f"{name}.py terminated by user\n")
            break

# Main Entry Point
def main():
    venv = len(sys.argv) > 1
    venv_name = sys.argv[1] if venv else None
    while True:
        run("main", venv, venv_name)
        if exit_flag: break
        print("--- Restarting... ---")

# Run entry point if directly run
if __name__ == "__main__": main()
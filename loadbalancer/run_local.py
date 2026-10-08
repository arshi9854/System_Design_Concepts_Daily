import os
from pathlib import Path
import subprocess
import sys
import time

PROJECT_DIR = Path(__file__).resolve().parent

def main():
    processes = []
    environment = os.environ.copy()
    environment["BACKEND_URLS"] = ",".join(
        f"http://localhost:{port}" for port in (8081, 8082, 8083)
    )

    commands = [
        ["server.py", "8081"],
        ["server.py", "8082"],
        ["server.py", "8083"],
        ["load_balancer.py"],
    ]

    try:
        for command in commands:
            process = subprocess.Popen(
                [sys.executable, *command],
                cwd=PROJECT_DIR,
                env=environment
            )
            processes.append(process)
        print("Starting local servers. Press Ctrl+C to stop them.", flush=True)

        while True:
            for process in processes:
                if process.poll() is not None:
                    raise RuntimeError(
                        f"A server exited with code {process.returncode}. "
                        "Check the output above."
                    )
            time.sleep(0.5)

    except KeyboardInterrupt:
        print("\nStopping local servers...")

    finally:
        for process in processes:
            if process.poll() is None:
                process.terminate()

        for process in processes:
            try:
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()


if __name__ == "__main__":
    main()
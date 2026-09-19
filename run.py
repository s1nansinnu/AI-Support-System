"""
Single-command launcher.

Starts both the FastAPI backend (Uvicorn) and the Streamlit frontend
as separate subprocesses, then waits until either exits or Ctrl-C.

Usage:
    python run.py
"""
import subprocess
import sys
import time


def main() -> None:
    print("=" * 60)
    print("  🚀  AI Support Ticket System")
    print("=" * 60)

    # ── Backend ───────────────────────────────────────────────────────────────
    print("\n📡 Starting FastAPI backend  →  http://127.0.0.1:8000")
    backend = subprocess.Popen(
        [
            sys.executable, "-m", "uvicorn", "main:app",
            "--host", "127.0.0.1",
            "--port", "8000",
        ],
        cwd="backend",
    )

    # Give Uvicorn a moment to bind the port
    time.sleep(2)

    # ── Frontend ──────────────────────────────────────────────────────────────
    print("💻 Starting Streamlit frontend  →  http://127.0.0.1:8501\n")
    frontend = subprocess.Popen(
        [
            sys.executable, "-m", "streamlit", "run", "main.py",
            "--server.port", "8501",
            "--server.headless", "true",
        ],
        cwd="frontend",
    )

    print("✅ Both services are running.")
    print("   Streamlit UI  : http://127.0.0.1:8501")
    print("   FastAPI Docs  : http://127.0.0.1:8000/docs")
    print("   Press Ctrl+C to stop.\n")

    try:
        while True:
            time.sleep(1)
            if backend.poll() is not None:
                print("⚠️  Backend exited unexpectedly.")
                break
            if frontend.poll() is not None:
                print("⚠️  Frontend exited unexpectedly.")
                break
    except KeyboardInterrupt:
        print("\n🛑 Shutting down…")
    finally:
        for proc in (frontend, backend):
            if proc.poll() is None:
                proc.terminate()
                try:
                    proc.wait(timeout=5)
                except Exception:
                    proc.kill()
        print("All services stopped.")


if __name__ == "__main__":
    main()

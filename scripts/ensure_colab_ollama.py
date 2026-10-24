#!/usr/bin/env python3
"""Idempotent local Ollama bootstrap for Google Colab GPU sessions.

The public notebook explicitly authorizes the official Ollama installer.
No model is pulled here; inference and data remain on the Colab VM.
"""
import json
import shutil
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path

API = "http://127.0.0.1:11434/api/version"


def _version():
    try:
        with urllib.request.urlopen(API, timeout=2) as response:
            payload = json.load(response)
        return payload.get("version") if isinstance(payload, dict) else None
    except (OSError, ValueError, urllib.error.URLError):
        return None


def ensure_ollama_ready(output_dir, *, timeout_seconds=100):
    if not shutil.which("nvidia-smi"):
        raise RuntimeError("No NVIDIA GPU in this session; choose a GPU in Colab Runtime settings.")

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    binary = shutil.which("ollama")
    if not binary:
        fallback = Path("/usr/local/bin/ollama")
        if fallback.is_file():
            binary = str(fallback)
    if not binary:
        print("Ollama not installed. Installing it on the Colab GPU server...")
        subprocess.run(
            ["bash", "-lc", "set -euo pipefail; curl -fsSL https://ollama.com/install.sh | sh"],
            check=True,
            timeout=240,
        )
        binary = shutil.which("ollama")
        if not binary and Path("/usr/local/bin/ollama").is_file():
            binary = "/usr/local/bin/ollama"
        if not binary:
            raise RuntimeError("Ollama installer finished but binary was not found; check installation output.")

    version = _version()
    if version:
        print("Ollama ready:", version)
        return binary

    log_path = output_dir / "ollama-server.log"
    print("Starting local Ollama server. Logs:", log_path)
    with log_path.open("a", encoding="utf-8") as log:
        process = subprocess.Popen([binary, "serve"], stdout=log, stderr=subprocess.STDOUT)

    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        version = _version()
        if version:
            print("Ollama ready:", version)
            return binary
        if process.poll() is not None:
            raise RuntimeError("Ollama exited before becoming ready. See "+str(log_path))
        time.sleep(1)
    raise RuntimeError("Timed out starting Ollama. See "+str(log_path))

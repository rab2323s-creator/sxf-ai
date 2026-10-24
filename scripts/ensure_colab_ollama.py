#!/usr/bin/env python3
"""Rootless, idempotent Ollama setup for SXF Google Colab GPU notebooks.

Uses the official Linux archive (see https://docs.ollama.com/linux) instead of
the system installer, which may fail in hosted notebook environments. The model
runtime and all benchmark output stay on the cloud VM, not the user's laptop.
"""
import hashlib
import json
import platform
import shutil
import subprocess
import sys
import tarfile
import time
import urllib.error
import urllib.request
from pathlib import Path

API = "http://127.0.0.1:11434/api/version"
OFFICIAL_ARCHIVE = "https://ollama.com/download/ollama-linux-amd64.tar.zst"


def _version():
    try:
        with urllib.request.urlopen(API, timeout=2) as response:
            payload = json.load(response)
        return payload.get("version") if isinstance(payload, dict) else None
    except (OSError, ValueError, urllib.error.URLError):
        return None


def _run_checked(command, purpose, *, timeout):
    """Expose actionable stderr rather than just CalledProcessError."""
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired as error:
        raise RuntimeError(purpose + " timed out: " + str(error)) from error
    if result.returncode:
        detail = (result.stderr or result.stdout or "No diagnostic text returned").strip()
        raise RuntimeError(purpose + " failed (exit " + str(result.returncode) +
                           "): " + detail[-1800:])
    return result


def _install_portable(output_dir):
    """Download and safely unpack the upstream Linux amd64 runtime, without sudo."""
    if platform.system() != "Linux" or platform.machine() not in ("x86_64", "AMD64"):
        raise RuntimeError("Portable Ollama archive currently supports Linux amd64 Colab GPUs only.")

    install_dir = output_dir.parent / "sxf-ollama-runtime"
    binary = install_dir / "bin" / "ollama"
    if binary.is_file():
        return str(binary)
    install_dir.mkdir(parents=True, exist_ok=True)

    # Current upstream package is large; fail with an explicit message if disk is low.
    if shutil.disk_usage(install_dir).free < 5 * 1024**3:
        raise RuntimeError("Not enough free Colab disk for Ollama. Need at least 5 GiB before downloading.")

    archive = install_dir / "ollama-linux-amd64.tar.zst"
    if not archive.is_file() or archive.stat().st_size == 0:
        print("Downloading official Ollama Linux GPU runtime to the Colab server (large archive)...", flush=True)
        _run_checked(
            ["curl", "--fail", "--location", "--show-error", "--silent",
             "--retry", "3", "--connect-timeout", "30", "--max-time", "2400",
             "--output", str(archive), OFFICIAL_ARCHIVE],
            "Ollama official archive download", timeout=2450,
        )
    digest = hashlib.sha256(archive.read_bytes()).hexdigest() if archive.stat().st_size < 256 * 1024**2 else None
    if digest:
        print("Ollama archive SHA-256:", digest)
    else:
        hasher = hashlib.sha256()
        with archive.open("rb") as stream:
            for chunk in iter(lambda: stream.read(4 * 1024 * 1024), b""):
                hasher.update(chunk)
        print("Ollama archive SHA-256:", hasher.hexdigest())

    try:
        import zstandard
    except ImportError:
        print("Installing Python zstandard decoder for the upstream Ollama archive...", flush=True)
        _run_checked([sys.executable, "-m", "pip", "install", "--quiet", "zstandard"],
                     "zstandard dependency installation", timeout=240)
        import zstandard

    print("Extracting Ollama locally without sudo or system services...", flush=True)
    try:
        with archive.open("rb") as source:
            with zstandard.ZstdDecompressor().stream_reader(source) as reader:
                with tarfile.open(fileobj=reader, mode="r|") as package:
                    package.extractall(path=install_dir, filter="data")
    except (OSError, ValueError, tarfile.TarError, zstandard.ZstdError) as error:
        raise RuntimeError("Unable to extract official Ollama archive: " + str(error)) from error
    if not binary.is_file():
        raise RuntimeError("Official Ollama package extracted but bin/ollama was not found: " + str(install_dir))
    archive.unlink(missing_ok=True)
    return str(binary)


def ensure_ollama_ready(output_dir, *, timeout_seconds=100):
    if not shutil.which("nvidia-smi"):
        raise RuntimeError("No NVIDIA GPU in this session; choose a Colab GPU first.")

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    binary = shutil.which("ollama")
    if not binary:
        for fallback in (Path("/usr/local/bin/ollama"), Path("/usr/bin/ollama")):
            if fallback.is_file():
                binary = str(fallback)
                break
    if not binary:
        print("Ollama is missing. Using the official rootless archive instead of install.sh.",
              flush=True)
        binary = _install_portable(output_dir)

    # The executable must actually work before attempting large model pulls.
    _run_checked([binary, "--version"], "Ollama binary check", timeout=30)
    version = _version()
    if version:
        print("Ollama ready:", version)
        return binary

    log_path = output_dir / "ollama-server.log"
    print("Starting local Ollama server. Log:", log_path, flush=True)
    with log_path.open("a", encoding="utf-8") as log:
        process = subprocess.Popen([binary, "serve"], stdout=log, stderr=subprocess.STDOUT)

    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        version = _version()
        if version:
            print("Ollama ready:", version)
            return binary
        if process.poll() is not None:
            raise RuntimeError("Ollama server exited. Check " + str(log_path) +
                               ": " + log_path.read_text(errors="replace")[-1200:])
        time.sleep(1)
    raise RuntimeError("Ollama did not start. Check " + str(log_path) +
                       ": " + log_path.read_text(errors="replace")[-1200:])

from __future__ import annotations

import platform
import socket
import subprocess
import time
from typing import Iterable

from .models import CommandResult, HttpSummary, TcpSummary


def run_command(command: list[str], timeout: int = 10) -> CommandResult:
    start = time.time()
    try:
        proc = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding="utf-8",
            errors="ignore",
        )
        return CommandResult(
            command=" ".join(command),
            success=proc.returncode == 0,
            stdout=proc.stdout,
            stderr=proc.stderr,
            return_code=proc.returncode,
            duration_ms=int((time.time() - start) * 1000),
        )
    except FileNotFoundError:
        return CommandResult(
            command=" ".join(command),
            success=False,
            stdout="",
            stderr=f"命令不存在: {command[0]}",
            return_code=127,
            duration_ms=int((time.time() - start) * 1000),
        )
    except subprocess.TimeoutExpired as ex:
        return CommandResult(
            command=" ".join(command),
            success=False,
            stdout=ex.stdout or "",
            stderr=f"命令超时: {timeout}s",
            return_code=124,
            duration_ms=int((time.time() - start) * 1000),
        )


def is_windows() -> bool:
    return platform.system().lower().startswith("win")


def collect_local_network() -> dict[str, CommandResult]:
    if is_windows():
        return {
            "ipconfig": run_command(["ipconfig", "/all"], timeout=12),
            "route": run_command(["route", "print", "-4"], timeout=8),
            "arp": run_command(["arp", "-a"], timeout=8),
        }

    ipconfig = run_command(["ip", "addr"], timeout=8)
    if not ipconfig.success and ipconfig.return_code == 127:
        ipconfig = run_command(["ifconfig"], timeout=8)

    route = run_command(["ip", "route"], timeout=8)
    if not route.success and route.return_code == 127:
        route = run_command(["route", "-n"], timeout=8)

    arp = run_command(["ip", "neigh"], timeout=8)
    if not arp.success and arp.return_code == 127:
        arp = run_command(["arp", "-an"], timeout=8)

    return {"ipconfig": ipconfig, "route": route, "arp": arp}


def ping(host: str, count: int = 2, timeout_ms: int = 1000) -> CommandResult:
    if is_windows():
        return run_command(["ping", "-n", str(count), "-w", str(timeout_ms), host], timeout=8)
    timeout_s = max(1, int(timeout_ms / 1000))
    return run_command(["ping", "-c", str(count), "-W", str(timeout_s), host], timeout=8)


def tracert(host: str, hops: int = 10, timeout_ms: int = 500) -> CommandResult:
    if is_windows():
        return run_command(["tracert", "-d", "-h", str(hops), "-w", str(timeout_ms), host], timeout=18)
    timeout_s = max(1, int(timeout_ms / 1000))
    return run_command(["traceroute", "-n", "-m", str(hops), "-w", str(timeout_s), host], timeout=18)


def test_tcp_port(host: str, port: int, timeout: float = 2.0) -> TcpSummary:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    try:
        sock.connect((host, port))
        return TcpSummary(target=host, port=port, success=True)
    except Exception as ex:  # noqa: BLE001
        return TcpSummary(target=host, port=port, success=False, error=str(ex))
    finally:
        sock.close()


def test_http(url: str, timeout: float = 3.0) -> HttpSummary:
    try:
        from urllib import request

        req = request.Request(url=url, method="GET")
        with request.urlopen(req, timeout=timeout) as resp:
            status = getattr(resp, "status", None) or resp.getcode()
            return HttpSummary(url=url, success=200 <= status < 500, status_code=status)
    except Exception as ex:  # noqa: BLE001
        return HttpSummary(url=url, success=False, error=str(ex))


def test_multi_tcp(host: str, ports: Iterable[int], timeout: float = 2.0) -> list[TcpSummary]:
    return [test_tcp_port(host, p, timeout=timeout) for p in ports]

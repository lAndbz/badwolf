from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class CommandResult:
    command: str
    success: bool
    stdout: str
    stderr: str
    return_code: int
    duration_ms: int


@dataclass
class PingSummary:
    success: bool
    sent: int = 0
    received: int = 0
    loss_percent: int = 100
    avg_ms: float | None = None


@dataclass
class TcpSummary:
    target: str
    port: int
    success: bool
    error: str | None = None


@dataclass
class HttpSummary:
    url: str
    success: bool
    status_code: int | None = None
    error: str | None = None


@dataclass
class RouteEntry:
    destination: str
    netmask: str
    gateway: str
    interface: str
    metric: int


@dataclass
class RouteSummary:
    defaults: list[RouteEntry] = field(default_factory=list)
    best_match: RouteEntry | None = None
    warnings: list[str] = field(default_factory=list)


@dataclass
class SSHDiagnosis:
    enabled: bool
    connected: bool = False
    error: str | None = None
    outputs: dict[str, str] = field(default_factory=dict)
    findings: list[str] = field(default_factory=list)


@dataclass
class DiagnosticInput:
    target_ip: str
    target_type: str = "普通主机"
    target_port: int | None = None
    run_tracert: bool = False
    run_http: bool = False
    run_https: bool = False
    run_ssh: bool = False
    ssh_host: str | None = None
    ssh_device_type: str = "huawei"
    ssh_username: str | None = None
    ssh_password: str | None = None
    ssh_ports_filter: list[str] = field(default_factory=list)
    baseline_path: str | None = None


@dataclass
class DiagnosticContext:
    started_at: datetime
    hostname: str
    params: DiagnosticInput
    local: dict[str, CommandResult] = field(default_factory=dict)
    route_summary: RouteSummary = field(default_factory=RouteSummary)
    ping_loopback: PingSummary | None = None
    ping_gateway: PingSummary | None = None
    ping_target: PingSummary | None = None
    tracert: CommandResult | None = None
    tcp: TcpSummary | None = None
    http: HttpSummary | None = None
    https: HttpSummary | None = None
    ssh: SSHDiagnosis = field(default_factory=lambda: SSHDiagnosis(enabled=False))
    baseline_result: dict[str, Any] = field(default_factory=dict)
    conclusions: list[dict[str, Any]] = field(default_factory=list)
    risks: list[str] = field(default_factory=list)
    next_steps: list[str] = field(default_factory=list)

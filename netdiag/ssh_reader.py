from __future__ import annotations

from dataclasses import dataclass

from .models import SSHDiagnosis
from .parser import summarize_huawei

HUAWEI_WHITELIST = [
    "display version",
    "display device",
    "display current-configuration",
    "display interface brief",
    "display interface",
    "display ip interface brief",
    "display vlan",
    "display port vlan",
    "display mac-address",
    "display arp",
    "display stp brief",
    "display stp interface",
    "display eth-trunk",
    "display lldp neighbor brief",
    "display lldp neighbor",
    "display cpu-usage",
    "display memory-usage",
    "display logbuffer",
    "display transceiver diagnosis interface",
    "display clock",
    "display ntp status",
    "display ssh server status",
    "display snmp-agent",
]

FORBIDDEN_KEYWORDS = [
    "system-view",
    "save",
    "reboot",
    "reset",
    "shutdown",
    "undo",
    "interface ",
    "vlan ",
    "port ",
    "stelnet server enable",
    "configure terminal",
    "write memory",
    "copy running-config startup-config",
]


@dataclass
class SSHOptions:
    host: str
    username: str
    password: str
    device_type: str = "huawei"
    include_current_config: bool = False
    interface_filters: list[str] | None = None


def _safe_commands(opts: SSHOptions) -> list[str]:
    cmds = [c for c in HUAWEI_WHITELIST if opts.include_current_config or c != "display current-configuration"]
    if opts.interface_filters:
        filtered = []
        for intf in opts.interface_filters:
            filtered.append(f"display interface {intf}")
            filtered.append(f"display transceiver diagnosis interface {intf}")
        cmds = [c for c in cmds if c not in {"display interface", "display transceiver diagnosis interface"}] + filtered

    for c in cmds:
        lower = c.lower().strip()
        if any(k in lower for k in FORBIDDEN_KEYWORDS):
            raise ValueError(f"检测到高风险命令，已阻断: {c}")
        if not lower.startswith("display "):
            raise ValueError(f"检测到非只读命令，已阻断: {c}")
    return cmds


def run_ssh_readonly(opts: SSHOptions) -> SSHDiagnosis:
    diag = SSHDiagnosis(enabled=True)
    try:
        import paramiko
    except ImportError:
        diag.error = "未安装 paramiko，无法执行 SSH 只读诊断。"
        return diag

    try:
        commands = _safe_commands(opts)
    except Exception as ex:  # noqa: BLE001
        diag.error = str(ex)
        return diag

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        client.connect(
            hostname=opts.host,
            username=opts.username,
            password=opts.password,
            look_for_keys=False,
            allow_agent=False,
            timeout=5,
            banner_timeout=5,
            auth_timeout=5,
        )
        diag.connected = True
        for cmd in commands:
            _, stdout, stderr = client.exec_command(cmd, timeout=10)
            out = stdout.read().decode("utf-8", errors="ignore")
            err = stderr.read().decode("utf-8", errors="ignore")
            diag.outputs[cmd] = out if out.strip() else err
        diag.findings = summarize_huawei(diag.outputs)
    except Exception as ex:  # noqa: BLE001
        diag.error = f"SSH 连接或命令执行失败: {ex}"
    finally:
        client.close()
    return diag

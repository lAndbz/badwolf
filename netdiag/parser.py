from __future__ import annotations

import ipaddress
import re

from .models import CommandResult, PingSummary, RouteEntry, RouteSummary


PING_WINDOWS = re.compile(r"Sent = (\d+), Received = (\d+), Lost = (\d+) \((\d+)% loss\)")
PING_LINUX = re.compile(r"(\d+) packets transmitted, (\d+) received, .*?(\d+)% packet loss")
RTT_WINDOWS = re.compile(r"Average = (\d+)ms")
RTT_LINUX = re.compile(r"min/avg/max/[a-z]+ = [\d.]+/([\d.]+)/")


def parse_ping(result: CommandResult) -> PingSummary:
    text = f"{result.stdout}\n{result.stderr}"
    mw = PING_WINDOWS.search(text)
    if mw:
        sent, recv, _, loss = (int(v) for v in mw.groups())
        avg = RTT_WINDOWS.search(text)
        return PingSummary(success=recv > 0, sent=sent, received=recv, loss_percent=loss, avg_ms=float(avg.group(1)) if avg else None)

    ml = PING_LINUX.search(text)
    if ml:
        sent, recv, loss = (int(v) for v in ml.groups())
        avg = RTT_LINUX.search(text)
        return PingSummary(success=recv > 0, sent=sent, received=recv, loss_percent=loss, avg_ms=float(avg.group(1)) if avg else None)

    success = result.return_code == 0
    return PingSummary(success=success, sent=0, received=1 if success else 0, loss_percent=0 if success else 100)


def parse_route_print(text: str, target_ip: str) -> RouteSummary:
    summary = RouteSummary()
    lines = [ln.rstrip() for ln in text.splitlines() if ln.strip()]

    pattern = re.compile(
        r"^(\d+\.\d+\.\d+\.\d+)\s+(\d+\.\d+\.\d+\.\d+)\s+(\d+\.\d+\.\d+\.\d+)\s+(\d+\.\d+\.\d+\.\d+)\s+(\d+)$"
    )

    routes: list[RouteEntry] = []
    for ln in lines:
        m = pattern.match(ln.strip())
        if not m:
            continue
        dest, mask, gw, iface, metric = m.groups()
        routes.append(RouteEntry(destination=dest, netmask=mask, gateway=gw, interface=iface, metric=int(metric)))

    defaults = [r for r in routes if r.destination == "0.0.0.0" and r.netmask == "0.0.0.0" and r.gateway != "0.0.0.0"]
    summary.defaults = sorted(defaults, key=lambda x: x.metric)
    if len(summary.defaults) > 1:
        summary.warnings.append("检测到多默认路由，可能存在 VPN/虚拟网卡/路由优先级干扰。")

    try:
        target = ipaddress.ip_address(target_ip)
    except ValueError:
        summary.warnings.append("目标 IP 格式无效，无法进行最佳路由匹配。")
        return summary

    best: tuple[int, int, RouteEntry] | None = None
    for route in routes:
        try:
            net = ipaddress.ip_network(f"{route.destination}/{route.netmask}", strict=False)
        except ValueError:
            continue
        if target in net:
            score = (net.prefixlen, -route.metric)
            if best is None or score > (best[0], best[1]):
                best = (score[0], score[1], route)

    if best:
        summary.best_match = best[2]
    else:
        summary.warnings.append("未找到与目标匹配的显式路由，可能依赖默认路由。")

    if not summary.defaults:
        summary.warnings.append("未识别到有效默认路由。")
    return summary


def parse_tracert_timeout_hops(text: str) -> int:
    timeout_lines = 0
    for line in text.splitlines():
        if "*" in line and re.search(r"^\s*\d+", line):
            timeout_lines += 1
    return timeout_lines


def summarize_huawei(outputs: dict[str, str]) -> list[str]:
    findings: list[str] = []
    cpu_text = outputs.get("display cpu-usage", "")
    mem_text = outputs.get("display memory-usage", "")
    log_text = outputs.get("display logbuffer", "")

    cpu_match = re.search(r"CPU Usage\s*:\s*(\d+)%", cpu_text, re.IGNORECASE)
    if cpu_match and int(cpu_match.group(1)) > 80:
        findings.append("设备 CPU 利用率偏高（>80%）。")

    mem_match = re.search(r"Memory Using Percentage\s*:\s*(\d+)%", mem_text, re.IGNORECASE)
    if mem_match and int(mem_match.group(1)) > 85:
        findings.append("设备内存利用率偏高（>85%）。")

    if re.search(r"ERROR|DOWN|ALARM", log_text, re.IGNORECASE):
        findings.append("日志中存在 ERROR/DOWN/ALARM 关键字，建议人工复核。")

    if not findings:
        findings.append("设备只读检查未发现明显高风险项。")
    return findings

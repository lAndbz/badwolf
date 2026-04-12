from __future__ import annotations

import argparse
import socket
from datetime import datetime

from netdiag.baseline import compare_baseline, load_baseline
from netdiag.collector import collect_local_network, ping, test_http, test_tcp_port, tracert
from netdiag.diagnoser import run_rules
from netdiag.models import DiagnosticContext, DiagnosticInput, PingSummary
from netdiag.parser import parse_ping, parse_route_print
from netdiag.reporter import write_txt_report
from netdiag.ssh_reader import SSHOptions, run_ssh_readonly


def _step(idx: int, total: int, text: str) -> None:
    print(f"[{idx}/{total}] {text}")


def _parse_ports(raw: str | None) -> int | None:
    if not raw:
        return None
    return int(raw)


def build_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="厂区/园区网络自动化诊断程序 MVP")
    parser.add_argument("target_ip", help="目标 IP")
    parser.add_argument("--target-type", default="普通主机", help="目标类型")
    parser.add_argument("--port", help="可选目标 TCP 端口")
    parser.add_argument("--tracert", action="store_true", help="执行 tracert")
    parser.add_argument("--http", action="store_true", help="执行 HTTP 测试")
    parser.add_argument("--https", action="store_true", help="执行 HTTPS 测试")
    parser.add_argument("--ssh", action="store_true", help="执行 SSH 只读设备诊断")
    parser.add_argument("--ssh-host", help="设备管理 IP，默认取 target_ip")
    parser.add_argument("--ssh-username", help="SSH 用户名")
    parser.add_argument("--ssh-password", help="SSH 密码（建议改为交互输入）")
    parser.add_argument("--ssh-ports", nargs="*", default=[], help="仅检查指定端口")
    parser.add_argument("--include-running-config", action="store_true", help="允许采集 display current-configuration")
    parser.add_argument("--baseline", help="可选基线文件 YAML/JSON")
    return parser.parse_args()


def main() -> None:
    args = build_args()
    params = DiagnosticInput(
        target_ip=args.target_ip,
        target_type=args.target_type,
        target_port=_parse_ports(args.port),
        run_tracert=args.tracert,
        run_http=args.http,
        run_https=args.https,
        run_ssh=args.ssh,
        ssh_host=args.ssh_host or args.target_ip,
        ssh_username=args.ssh_username,
        ssh_password=args.ssh_password,
        ssh_ports_filter=args.ssh_ports,
        baseline_path=args.baseline,
    )

    total_steps = 8 if params.run_ssh else 7
    step = 1
    ctx = DiagnosticContext(started_at=datetime.now(), hostname=socket.gethostname(), params=params)

    _step(step, total_steps, "获取本机网络信息")
    ctx.local = collect_local_network()
    step += 1

    _step(step, total_steps, "解析默认路由")
    route_text = ctx.local.get("route").stdout if "route" in ctx.local else ""
    ctx.route_summary = parse_route_print(route_text, params.target_ip)
    step += 1

    _step(step, total_steps, "ping 回环与默认网关")
    ctx.ping_loopback = parse_ping(ping("127.0.0.1", count=1))
    if ctx.route_summary.defaults:
        gw = ctx.route_summary.defaults[0].gateway
        ctx.ping_gateway = parse_ping(ping(gw, count=1))
    else:
        ctx.ping_gateway = PingSummary(success=False)
    step += 1

    _step(step, total_steps, "ping 目标")
    ctx.ping_target = parse_ping(ping(params.target_ip, count=2))
    step += 1

    _step(step, total_steps, "测试目标端口")
    if params.target_port:
        ctx.tcp = test_tcp_port(params.target_ip, params.target_port, timeout=2.0)
    step += 1

    if params.run_http or params.run_https:
        _step(step, total_steps, "HTTP/HTTPS 测试")
        if params.run_http:
            ctx.http = test_http(f"http://{params.target_ip}")
        if params.run_https:
            ctx.https = test_http(f"https://{params.target_ip}")
        step += 1

    if params.run_tracert:
        _step(step, total_steps, "执行 tracert")
        ctx.tracert = tracert(params.target_ip, hops=10, timeout_ms=500)
        step += 1

    if params.run_ssh:
        _step(step, total_steps, "SSH 登录设备做只读诊断")
        ctx.ssh = run_ssh_readonly(
            SSHOptions(
                host=params.ssh_host or params.target_ip,
                username=params.ssh_username or "",
                password=params.ssh_password or "",
                include_current_config=args.include_running_config,
                interface_filters=params.ssh_ports_filter,
            )
        )
        if params.baseline_path and ctx.ssh.connected:
            baseline = load_baseline(params.baseline_path)
            ctx.baseline_result = compare_baseline(ctx.ssh.outputs, baseline)
        step += 1

    run_rules(ctx)

    _step(step, total_steps, "生成报告")
    report = write_txt_report(ctx)

    print("\n=== 诊断摘要 ===")
    for c in ctx.conclusions:
        print(f"- 最可能故障点: {c['最可能故障点']} (置信度: {c['置信度']})")
    print(f"报告已生成: {report}")


if __name__ == "__main__":
    main()

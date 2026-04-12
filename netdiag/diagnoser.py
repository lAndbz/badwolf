from __future__ import annotations

from .models import DiagnosticContext
from .parser import parse_tracert_timeout_hops


def _add(ctx: DiagnosticContext, point: str, confidence: str, evidence: list[str]) -> None:
    ctx.conclusions.append(
        {
            "最可能故障点": point,
            "置信度": confidence,
            "判断依据": evidence,
        }
    )


def run_rules(ctx: DiagnosticContext) -> None:
    p_loop = ctx.ping_loopback
    p_gw = ctx.ping_gateway
    p_target = ctx.ping_target

    if p_loop and not p_loop.success:
        _add(ctx, "本机 TCP/IP 协议栈异常", "高", ["ping 127.0.0.1 失败"])
        ctx.risks.append("本机网络组件异常会影响所有后续结论，应优先修复本机。")
        ctx.next_steps.extend(["重置本机网络协议栈", "检查网卡驱动与本机安全策略"])
        return

    if p_target and p_target.success:
        _add(ctx, "目标主机网络层连通", "高", ["目标 ping 成功"])
        if ctx.tcp and not ctx.tcp.success:
            _add(ctx, "目标业务端口不可达", "中", [f"目标 IP 可达但 TCP {ctx.tcp.port} 不可达"])
            ctx.next_steps.append("检查目标主机服务进程、端口监听及安全策略。")
        else:
            ctx.next_steps.append("如仍有业务异常，建议转应用层日志排查。")
        return

    app_reachable = (ctx.tcp and ctx.tcp.success) or (ctx.http and ctx.http.success) or (ctx.https and ctx.https.success)
    if p_target and (not p_target.success) and app_reachable:
        _add(
            ctx,
            "疑似禁用 ICMP 回显或路径策略拦截 ICMP",
            "高",
            ["目标 ping 失败", "但 TCP 端口或 HTTP/HTTPS 可达"],
        )
        ctx.risks.append("仅 ICMP 不通不等价于网络故障。")
        ctx.next_steps.append("核查主机防火墙 ICMP 策略和中间安全设备 ACL。")
        return

    if p_gw and (not p_gw.success) and p_target and (not p_target.success):
        _add(
            ctx,
            "本地链路/默认网关/VLAN 方向异常",
            "中",
            ["默认网关不可达", "目标也不可达"],
        )
        ctx.next_steps.extend(["检查本机网卡状态", "检查接入交换机端口/VLAN", "检查网关设备状态"])
    elif p_gw and p_gw.success and p_target and (not p_target.success):
        _add(
            ctx,
            "中间路径/路由/ACL/防火墙或目标主机异常",
            "中",
            ["默认网关可达", "目标不可达"],
        )
        ctx.next_steps.extend(["检查中间路由与安全策略", "检查目标主机在线状态"])

    if ctx.route_summary.warnings:
        ctx.risks.extend(ctx.route_summary.warnings)

    if ctx.tracert and ctx.tracert.stdout:
        timeout_hops = parse_tracert_timeout_hops(ctx.tracert.stdout)
        if timeout_hops >= 2:
            ctx.risks.append("tracert 出现持续超时，可能存在中间设备不响应、ACL 或路由丢弃。")

    if not ctx.conclusions:
        _add(ctx, "暂未定位明确故障点", "低", ["可用探测信息不足或结果互相矛盾"])
        ctx.next_steps.append("建议补充端口、应用和设备内诊断信息后复测。")

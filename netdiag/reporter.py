from __future__ import annotations

from datetime import datetime
from pathlib import Path

from .models import DiagnosticContext


def _yes_no(v: bool | None) -> str:
    if v is None:
        return "N/A"
    return "是" if v else "否"


def write_txt_report(ctx: DiagnosticContext, output_dir: str = "reports") -> Path:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = out / f"diag_{ctx.params.target_ip}_{stamp}.txt"

    lines: list[str] = []
    lines.append("=== 厂区/园区网络自动化诊断报告（MVP）===")
    lines.append(f"生成时间: {datetime.now().isoformat(sep=' ', timespec='seconds')}")
    lines.append(f"主机名: {ctx.hostname}")
    lines.append(f"目标信息: IP={ctx.params.target_ip}, 类型={ctx.params.target_type}, 端口={ctx.params.target_port}")
    lines.append("")

    lines.append("[本机网络摘要]")
    for k, v in ctx.local.items():
        lines.append(f"- {k}: {'成功' if v.success else '失败'} ({v.duration_ms}ms)")

    lines.append("")
    lines.append("[默认路由摘要]")
    if ctx.route_summary.defaults:
        for r in ctx.route_summary.defaults:
            lines.append(f"- 默认路由: 网关={r.gateway}, 接口={r.interface}, metric={r.metric}")
    else:
        lines.append("- 未识别到有效默认路由")
    if ctx.route_summary.best_match:
        br = ctx.route_summary.best_match
        lines.append(f"- 目标最佳匹配路由: {br.destination}/{br.netmask} via {br.gateway} if {br.interface}")
    for w in ctx.route_summary.warnings:
        lines.append(f"- 提示: {w}")

    lines.append("")
    lines.append("[原始检测结果摘要]")
    lines.append(f"- ping 127.0.0.1: {_yes_no(ctx.ping_loopback.success if ctx.ping_loopback else None)}")
    lines.append(f"- ping 默认网关: {_yes_no(ctx.ping_gateway.success if ctx.ping_gateway else None)}")
    lines.append(f"- ping 目标: {_yes_no(ctx.ping_target.success if ctx.ping_target else None)}")
    if ctx.tcp:
        lines.append(f"- TCP 端口 {ctx.tcp.port}: {_yes_no(ctx.tcp.success)}")
    if ctx.http:
        lines.append(f"- HTTP: {_yes_no(ctx.http.success)} 状态码={ctx.http.status_code}")
    if ctx.https:
        lines.append(f"- HTTPS: {_yes_no(ctx.https.success)} 状态码={ctx.https.status_code}")
    if ctx.tracert:
        lines.append(f"- tracert 执行: {_yes_no(ctx.tracert.success)}")

    lines.append("")
    lines.append("[设备只读诊断结果]")
    lines.append(f"- 启用 SSH: {_yes_no(ctx.ssh.enabled)}")
    lines.append(f"- SSH 连接成功: {_yes_no(ctx.ssh.connected)}")
    if ctx.ssh.error:
        lines.append(f"- SSH 错误: {ctx.ssh.error}")
    for f in ctx.ssh.findings:
        lines.append(f"- 设备发现: {f}")

    lines.append("")
    lines.append("[诊断结论]")
    for idx, c in enumerate(ctx.conclusions, start=1):
        lines.append(f"{idx}. 最可能故障点: {c['最可能故障点']}")
        lines.append(f"   置信度: {c['置信度']}")
        lines.append("   判断依据:")
        for e in c["判断依据"]:
            lines.append(f"   - {e}")

    lines.append("")
    lines.append("[风险提示]")
    for r in ctx.risks or ["暂无高风险提示"]:
        lines.append(f"- {r}")

    lines.append("")
    lines.append("[建议下一步检查项]")
    for s in ctx.next_steps or ["建议结合现场拓扑与日志继续核查"]:
        lines.append(f"- {s}")

    lines.append("")
    lines.append("[基线比对]")
    if ctx.baseline_result:
        lines.append(str(ctx.baseline_result))
    else:
        lines.append("未执行")

    path.write_text("\n".join(lines), encoding="utf-8")
    return path

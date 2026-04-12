from __future__ import annotations

from pathlib import Path
from typing import Any


def load_baseline(path: str | None) -> dict[str, Any]:
    if not path:
        return {}
    p = Path(path)
    if not p.exists():
        return {"error": f"基线文件不存在: {path}"}

    text = p.read_text(encoding="utf-8")
    if p.suffix.lower() in {".yaml", ".yml"}:
        try:
            import yaml

            return yaml.safe_load(text) or {}
        except Exception as ex:  # noqa: BLE001
            return {"error": f"YAML 解析失败: {ex}"}
    if p.suffix.lower() == ".json":
        import json

        return json.loads(text)
    return {"error": "仅支持 YAML/JSON 基线文件"}


def compare_baseline(ssh_outputs: dict[str, str], baseline: dict[str, Any]) -> dict[str, Any]:
    if not baseline:
        return {"enabled": False, "message": "未提供基线，跳过比对。"}

    issues: list[str] = []
    expected_hostname = baseline.get("hostname")
    if expected_hostname:
        ver = ssh_outputs.get("display version", "")
        if expected_hostname not in ver:
            issues.append(f"设备名称与基线不完全一致（期望包含: {expected_hostname}）。")

    expected_vlans = baseline.get("vlans", [])
    if expected_vlans:
        vlan_text = ssh_outputs.get("display vlan", "")
        for vlan in expected_vlans:
            if str(vlan) not in vlan_text:
                issues.append(f"未在设备输出中发现基线 VLAN: {vlan}")

    return {
        "enabled": True,
        "issues": issues,
        "healthy": len(issues) == 0,
    }

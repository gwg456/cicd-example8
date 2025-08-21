from __future__ import annotations

import json
import re
import socket
import sys
from dataclasses import dataclass
from typing import Optional
from urllib.request import urlopen


IPV4_RE = re.compile(r"^(?:\d{1,3}\.){3}\d{1,3}$")


@dataclass
class GeoResult:
    original: str
    ip: Optional[str]
    city: str
    region: str
    country: str
    org: str
    asn: str
    note: str = ""


def is_ipv4(text: str) -> bool:
    if not IPV4_RE.match(text):
        return False
    parts = [int(p) for p in text.split(".")]
    return all(0 <= p <= 255 for p in parts)


def resolve_host(text: str) -> Optional[str]:
    if is_ipv4(text):
        return text
    try:
        # prefer IPv4 if available
        info_list = socket.getaddrinfo(text, None, family=socket.AF_INET)
        if info_list:
            return info_list[0][4][0]
    except Exception:
        pass
    try:
        ip = socket.gethostbyname(text)
        return ip
    except Exception:
        return None


def geo_ip(ip: str) -> dict:
    url = (
        f"http://ip-api.com/json/{ip}?lang=zh-CN&fields="
        "status,message,query,country,regionName,city,as,org"
    )
    with urlopen(url, timeout=8) as resp:
        data = json.loads(resp.read().decode("utf-8", errors="ignore"))
        return data


def infer_city_from_hostname(host: str) -> Optional[str]:
    lower = host.lower()
    # 简单启发：域名中包含城市/地区缩写
    if ".hk." in lower or lower.endswith(".hk"):  # 香港
        return "香港"
    if any(tag in lower for tag in [".hkg.", "-hkg", "hkg-"]):
        return "香港"
    if ".tw." in lower or lower.endswith(".tw"):
        return "台湾"
    if any(tag in lower for tag in [".tyo.", "-tyo", "tyo-"]):
        return "东京"
    if any(tag in lower for tag in [".sin.", "-sin", "sin-"]):
        return "新加坡"
    return None


def lookup(token: str) -> GeoResult:
    token = token.strip()
    if token in {"?", "??", "???", "*", "N/A"}:
        return GeoResult(token, None, "未知", "", "", "", "", note="无响应/超时")

    ip = resolve_host(token)
    if ip is None:
        city_hint = infer_city_from_hostname(token) or ""
        return GeoResult(token, None, city_hint or "未知", "", "", "", "", note="无法解析主机名")

    try:
        data = geo_ip(ip)
        if data.get("status") != "success":
            raise RuntimeError(data.get("message") or "查询失败")
        return GeoResult(
            original=token,
            ip=ip,
            city=data.get("city", "") or infer_city_from_hostname(token) or "",
            region=data.get("regionName", ""),
            country=data.get("country", ""),
            org=data.get("org", ""),
            asn=data.get("as", ""),
        )
    except Exception as exc:
        # 回退：仅基于域名线索
        city_hint = infer_city_from_hostname(token) or ""
        return GeoResult(token, ip, city_hint or "未知", "", "", "", "", note=f"查询失败: {exc}")


def main() -> None:
    if len(sys.argv) < 2:
        print("用法: python tools/lookup_cities.py <ip_or_hostname_1> [<ip_or_hostname_2> ...]")
        sys.exit(1)

    items = sys.argv[1:]
    results = [lookup(x) for x in items]

    for idx, r in enumerate(results, 1):
        loc = " ".join(filter(None, [r.country, r.region, r.city])).strip()
        if not loc and r.city:
            loc = r.city
        ip_part = f" ({r.ip})" if r.ip and r.ip != r.original else ""
        note = f"  [{r.note}]" if r.note else ""
        print(f"{idx}. {r.original}{ip_part} -> {loc or '未知'} | {r.asn or r.org}{note}")


if __name__ == "__main__":
    main()




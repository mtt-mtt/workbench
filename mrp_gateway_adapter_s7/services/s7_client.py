"""Optional S7 client wrapper."""

from __future__ import annotations

from dataclasses import dataclass

try:
    import snap7
except Exception:  # pragma: no cover - optional dependency
    snap7 = None


@dataclass
class GatewayS7ClientResult:
    ok: bool
    data: dict | None = None
    errors: list[str] | None = None


class GatewayS7ClientHelper:
    def available(self):
        return snap7 is not None

    def describe(self):
        return {
            "available": self.available(),
            "backend": "python-snap7" if self.available() else "unavailable",
        }

    def build_client(self):
        if snap7 is None:
            return GatewayS7ClientResult(ok=False, errors=["python-snap7 is not installed"])
        try:
            client = snap7.client.Client()
            return GatewayS7ClientResult(ok=True, data={"client": client, "backend": "python-snap7"})
        except Exception as exc:  # pragma: no cover - defensive wrapper
            return GatewayS7ClientResult(ok=False, errors=[str(exc)])

    def connect(self, client, host, rack=0, slot=1, port=102):
        if client is None:
            return GatewayS7ClientResult(ok=False, errors=["S7 client instance is required"])
        try:
            client.connect(host, rack, slot, tcp_port=int(port or 102))
            return GatewayS7ClientResult(ok=True, data={"host": host, "rack": rack, "slot": slot, "port": port})
        except Exception as exc:  # pragma: no cover - defensive wrapper
            return GatewayS7ClientResult(ok=False, errors=[str(exc)])

    def disconnect(self, client):
        if client is None:
            return GatewayS7ClientResult(ok=False, errors=["S7 client instance is required"])
        try:
            client.disconnect()
            return GatewayS7ClientResult(ok=True, data={"client": client})
        except Exception as exc:  # pragma: no cover - defensive wrapper
            return GatewayS7ClientResult(ok=False, errors=[str(exc)])

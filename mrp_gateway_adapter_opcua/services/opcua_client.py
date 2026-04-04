"""Optional OPC UA client wrapper."""

from __future__ import annotations

from dataclasses import dataclass

try:
    from opcua import Client as OpcUaClient
except Exception:  # pragma: no cover - optional dependency
    OpcUaClient = None

try:
    from asyncua import Client as AsyncOpcUaClient
except Exception:  # pragma: no cover - optional dependency
    AsyncOpcUaClient = None


@dataclass
class GatewayOpcuaClientResult:
    ok: bool
    data: dict | None = None
    errors: list[str] | None = None


class GatewayOpcuaClientHelper:
    def available(self):
        return OpcUaClient is not None or AsyncOpcUaClient is not None

    def backend_name(self):
        if OpcUaClient is not None:
            return "python-opcua"
        if AsyncOpcUaClient is not None:
            return "asyncua"
        return "unavailable"

    def describe(self):
        return {
            "available": self.available(),
            "backend": self.backend_name(),
            "python_opcua": OpcUaClient is not None,
            "asyncua": AsyncOpcUaClient is not None,
        }

    def build_client(self, endpoint_url, username=None, password=None, security_policy=None, security_mode=None, timeout=5.0):
        if OpcUaClient is None:
            return GatewayOpcuaClientResult(
                ok=False,
                errors=["python-opcua is not installed"],
                data={"available": self.available(), "asyncua": AsyncOpcUaClient is not None},
            )
        try:
            client = OpcUaClient(endpoint_url)
            if username:
                client.set_user(username)
            if password:
                client.set_password(password)
            if security_policy and security_mode and hasattr(client, "set_security_string"):
                client.set_security_string(f"{security_policy},{security_mode}")
            if hasattr(client, "session_timeout") and timeout:
                client.session_timeout = int(float(timeout) * 1000)
            return GatewayOpcuaClientResult(ok=True, data={"client": client, "backend": self.backend_name()})
        except Exception as exc:  # pragma: no cover - defensive wrapper
            return GatewayOpcuaClientResult(ok=False, errors=[str(exc)])

    def connect(self, client):
        if client is None:
            return GatewayOpcuaClientResult(ok=False, errors=["OPC UA client instance is required"])
        try:
            client.connect()
            return GatewayOpcuaClientResult(ok=True, data={"client": client})
        except Exception as exc:  # pragma: no cover - defensive wrapper
            return GatewayOpcuaClientResult(ok=False, errors=[str(exc)])

    def disconnect(self, client):
        if client is None:
            return GatewayOpcuaClientResult(ok=False, errors=["OPC UA client instance is required"])
        try:
            client.disconnect()
            return GatewayOpcuaClientResult(ok=True, data={"client": client})
        except Exception as exc:  # pragma: no cover - defensive wrapper
            return GatewayOpcuaClientResult(ok=False, errors=[str(exc)])

    def read_node_value(self, client, node_id):
        if client is None:
            return GatewayOpcuaClientResult(ok=False, errors=["OPC UA client instance is required"])
        try:
            node = client.get_node(node_id)
            return GatewayOpcuaClientResult(ok=True, data={"node_id": node_id, "value": node.get_value()})
        except Exception as exc:  # pragma: no cover - defensive wrapper
            return GatewayOpcuaClientResult(ok=False, errors=[str(exc)])

    def write_node_value(self, client, node_id, value):
        if client is None:
            return GatewayOpcuaClientResult(ok=False, errors=["OPC UA client instance is required"])
        try:
            node = client.get_node(node_id)
            node.set_value(value)
            return GatewayOpcuaClientResult(ok=True, data={"node_id": node_id, "value": value})
        except Exception as exc:  # pragma: no cover - defensive wrapper
            return GatewayOpcuaClientResult(ok=False, errors=[str(exc)])

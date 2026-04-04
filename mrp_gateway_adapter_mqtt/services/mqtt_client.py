"""Optional MQTT client wrapper.

This addon should install cleanly even when paho-mqtt is not available.
"""

from __future__ import annotations

from dataclasses import dataclass

try:
    import paho.mqtt.client as paho_client
except Exception:  # pragma: no cover - optional dependency
    paho_client = None


@dataclass
class GatewayMqttClientResult:
    ok: bool
    data: dict | None = None
    errors: list[str] | None = None


class GatewayMqttClientHelper:
    def __init__(self):
        self._client_module = paho_client

    @property
    def available(self):
        return self._client_module is not None

    @property
    def backend_name(self):
        return "paho-mqtt" if self.available else "unavailable"

    def describe(self):
        return {
            "available": self.available,
            "backend": self.backend_name,
            "message": "paho-mqtt is available" if self.available else "paho-mqtt is not installed",
        }

    def build_client(self, client_id=None, clean_session=True, userdata=None, protocol=None, transport="tcp"):
        if not self.available:
            return GatewayMqttClientResult(ok=False, errors=["paho-mqtt is not installed"])
        try:
            kwargs = {}
            if client_id is not None:
                kwargs["client_id"] = client_id
            if userdata is not None:
                kwargs["userdata"] = userdata
            if protocol is not None:
                kwargs["protocol"] = protocol
            if transport:
                kwargs["transport"] = transport
            try:
                client = self._client_module.Client(clean_session=clean_session, **kwargs)
            except TypeError:
                kwargs.pop("transport", None)
                client = self._client_module.Client(**kwargs)
                if hasattr(client, "_clean_session"):
                    client._clean_session = clean_session
            return GatewayMqttClientResult(ok=True, data={"client": client, "backend": self.backend_name})
        except Exception as exc:  # pragma: no cover - defensive wrapper
            return GatewayMqttClientResult(ok=False, errors=[str(exc)])

    def connect(self, client, host, port=1883, keepalive=60, bind_address="", clean_start=None):
        if not self.available:
            return GatewayMqttClientResult(ok=False, errors=["paho-mqtt is not installed"])
        if client is None:
            return GatewayMqttClientResult(ok=False, errors=["MQTT client instance is required"])
        try:
            kwargs = {"host": host, "port": int(port or 1883), "keepalive": int(keepalive or 60)}
            if bind_address:
                kwargs["bind_address"] = bind_address
            if clean_start is not None:
                kwargs["clean_start"] = clean_start
            client.connect(**kwargs)
            return GatewayMqttClientResult(ok=True, data={"client": client, "host": host, "port": int(port or 1883)})
        except Exception as exc:  # pragma: no cover - defensive wrapper
            return GatewayMqttClientResult(ok=False, errors=[str(exc)])

    def subscribe(self, client, topic, qos=0):
        if not self.available:
            return GatewayMqttClientResult(ok=False, errors=["paho-mqtt is not installed"])
        if client is None:
            return GatewayMqttClientResult(ok=False, errors=["MQTT client instance is required"])
        try:
            client.subscribe(topic, qos=int(qos or 0))
            return GatewayMqttClientResult(ok=True, data={"topic": topic, "qos": int(qos or 0)})
        except Exception as exc:  # pragma: no cover - defensive wrapper
            return GatewayMqttClientResult(ok=False, errors=[str(exc)])

    def publish(self, client, topic, payload, qos=0, retain=False):
        if not self.available:
            return GatewayMqttClientResult(ok=False, errors=["paho-mqtt is not installed"])
        if client is None:
            return GatewayMqttClientResult(ok=False, errors=["MQTT client instance is required"])
        try:
            info = client.publish(topic, payload=payload, qos=int(qos or 0), retain=bool(retain))
            return GatewayMqttClientResult(ok=True, data={"topic": topic, "mid": getattr(info, "mid", None), "rc": getattr(info, "rc", None)})
        except Exception as exc:  # pragma: no cover - defensive wrapper
            return GatewayMqttClientResult(ok=False, errors=[str(exc)])

    def disconnect(self, client):
        if not self.available:
            return GatewayMqttClientResult(ok=False, errors=["paho-mqtt is not installed"])
        if client is None:
            return GatewayMqttClientResult(ok=False, errors=["MQTT client instance is required"])
        try:
            client.disconnect()
            return GatewayMqttClientResult(ok=True, data={"client": client})
        except Exception as exc:  # pragma: no cover - defensive wrapper
            return GatewayMqttClientResult(ok=False, errors=[str(exc)])

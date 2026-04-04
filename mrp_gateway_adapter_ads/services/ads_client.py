import json

try:
    import pyads
except Exception:  # pragma: no cover - optional dependency
    pyads = None


class GatewayAdsClientHelper:
    def describe(self):
        if pyads is None:
            return {"available": False, "module": "pyads", "error": "pyads is not installed"}
        return {
            "available": True,
            "module": "pyads",
            "version": getattr(pyads, "__version__", None),
            "supports_notifications": hasattr(pyads, "Connection") and hasattr(pyads, "NotificationAttrib"),
        }

    def describe_subscription_support(self):
        description = self.describe()
        description.update(
            {
                "supports_notifications": True,
                "supports_subscriptions": True,
                "subscription_backend": "pyads" if description.get("available") else "stub",
            }
        )
        return description

    def build_connection_target(self, *, ams_net_id=None, host=None, port=None, ads_port=None):
        host = host or "127.0.0.1"
        port = int(port or 48898)
        ads_port = int(ads_port or 851)
        if ams_net_id:
            return f"ads://{ams_net_id}@{host}:{port}/port/{ads_port}"
        return f"ads://{host}:{port}/port/{ads_port}"

    def describe_notification(self, *, symbol_path=None, data_type=None):
        info = self.describe()
        return {
            **info,
            "symbol_path": symbol_path,
            "data_type": data_type,
            "mode": "device_notification" if info.get("supports_notifications") else "mock_notification",
        }

    def notification_handle_stub(self, *, symbol_path=None):
        return f"ads-sub::{symbol_path or 'symbol'}"

    def build_subscription_key(self, *, adapter_code, symbol_code, subscription_mode="change"):
        adapter_code = adapter_code or "adapter"
        symbol_code = symbol_code or "symbol"
        subscription_mode = subscription_mode or "change"
        return f"ads:{adapter_code}:{symbol_code}:{subscription_mode}"

    def build_dispatch_signal(self, *, adapter_code, symbol_code, event_kind="update"):
        adapter_code = adapter_code or "adapter"
        symbol_code = symbol_code or "symbol"
        event_kind = event_kind or "update"
        return f"ads.dispatch.{adapter_code}.{symbol_code}.{event_kind}"

    def build_notification_payload(
        self,
        *,
        adapter_code,
        symbol_code,
        subscription_key=None,
        event_kind="update",
        source="manual",
        value_text=None,
        value_json=None,
        result_json=None,
    ):
        return {
            "adapter_code": adapter_code,
            "symbol_code": symbol_code,
            "subscription_key": subscription_key or self.build_subscription_key(
                adapter_code=adapter_code, symbol_code=symbol_code
            ),
            "event_kind": event_kind or "update",
            "source": source or "manual",
            "value_text": value_text,
            "value_json": value_json,
            "result_json": result_json,
            "signal": self.build_dispatch_signal(
                adapter_code=adapter_code, symbol_code=symbol_code, event_kind=event_kind
            ),
        }

    def _normalize_callback_mapping(self, payload):
        if payload is None:
            return {}
        if isinstance(payload, dict):
            return dict(payload)
        if isinstance(payload, (list, tuple)):
            normalized = {"raw_callback": list(payload)}
            if payload:
                normalized["handle"] = payload[0]
            if len(payload) > 1:
                second = payload[1]
                if isinstance(second, dict):
                    normalized.update(second)
                else:
                    normalized["value"] = second
            if len(payload) > 2:
                normalized["timestamp"] = payload[2]
            if len(payload) > 3 and "value" not in normalized:
                normalized["value"] = payload[3]
            return normalized
        return {"raw_callback": payload}

    def normalize_device_notification_payload(
        self,
        payload=None,
        *,
        adapter_code=None,
        symbol_code=None,
        subscription_key=None,
        event_kind=None,
        source=None,
    ):
        data = self._normalize_callback_mapping(payload)
        adapter_code = data.get("adapter_code") or adapter_code
        symbol_code = data.get("symbol_code") or symbol_code
        subscription_key = data.get("subscription_key") or subscription_key or self.build_subscription_key(
            adapter_code=adapter_code,
            symbol_code=symbol_code,
            subscription_mode=data.get("subscription_mode") or "change",
        )
        event_kind = data.get("event_kind") or data.get("kind") or event_kind or "change"
        source = data.get("source") or source or "runtime"
        state = data.get("state") or data.get("notification_state") or ("acknowledged" if data.get("acknowledged") else "dispatched")
        value = data.get("value")
        value_text = data.get("value_text")
        if value_text is None and value is not None:
            value_text = value if isinstance(value, str) else str(value)
        value_json = data.get("value_json")
        if value_json is None and value is not None:
            value_json = value if isinstance(value, (dict, list)) else {"value": value}
        result_json = data.get("result_json")
        if result_json is None:
            result_json = {}
        raw_callback = data.get("raw_callback")
        if raw_callback is None:
            raw_callback = data
        notification = {
            "available": self.describe().get("available", False),
            "mode": "device_notification" if self.describe().get("supports_notifications") else "mock_notification",
            "adapter_code": adapter_code,
            "symbol_code": symbol_code,
            "subscription_key": subscription_key,
            "event_kind": event_kind,
            "source": source,
            "state": state,
            "acknowledged": bool(data.get("acknowledged") or state == "acknowledged"),
            "callback_handle": data.get("handle") or data.get("notification_handle"),
            "callback_timestamp": data.get("timestamp") or data.get("time"),
            "value": value,
            "value_text": value_text,
            "value_json": value_json,
            "result_json": result_json,
            "payload_json": raw_callback,
            "note": data.get("note"),
            "signal": self.build_dispatch_signal(
                adapter_code=adapter_code,
                symbol_code=symbol_code,
                event_kind=event_kind,
            ),
        }
        if data.get("subscription_mode"):
            notification["subscription_mode"] = data.get("subscription_mode")
        if data.get("severity"):
            notification["severity"] = data.get("severity")
        return notification

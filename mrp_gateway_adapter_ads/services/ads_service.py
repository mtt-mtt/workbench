import json

from odoo import fields, _

from odoo.addons.mrp_gateway_runtime.services.runtime_service import GatewayRuntimeService

from .ads_client import GatewayAdsClientHelper


class GatewayAdsService:
    def __init__(self, env):
        self.env = env
        self.client_helper = GatewayAdsClientHelper()

    def _registry_has_model(self, model_name):
        return model_name in self.env.registry.models

    def _model(self, model_name):
        if not self._registry_has_model(model_name):
            return None
        return self.env[model_name].sudo()

    def _model_has_field(self, model, field_name):
        return bool(model and field_name in model._fields)

    def _json_dumps(self, value):
        return json.dumps(value, ensure_ascii=False, default=str)

    def _json_loads(self, value, default=None):
        if value in (None, False, ""):
            return default if default is not None else {}
        if isinstance(value, (dict, list, tuple)):
            return value
        if isinstance(value, str):
            try:
                return json.loads(value)
            except Exception:
                return {"raw": value}
        return value

    def _runtime_service(self):
        return GatewayRuntimeService(self.env)

    def _adapter_code(self, adapter):
        return getattr(adapter, "code", None) if adapter else None

    def _symbol_model(self):
        return self._model("gateway.ads.symbol")

    def _subscription_model(self):
        return self._model("gateway.ads.subscription")

    def _notification_model(self):
        return self._model("gateway.ads.notification")

    def _resolve_subscription(self, subscription):
        Subscription = self._subscription_model()
        if Subscription is None:
            return None
        if hasattr(subscription, "_name") and getattr(subscription, "_name", None) == "gateway.ads.subscription":
            return subscription.exists()
        if isinstance(subscription, int):
            return Subscription.browse(subscription).exists()
        if isinstance(subscription, dict):
            if subscription.get("subscription_id"):
                return Subscription.browse(int(subscription["subscription_id"])).exists()
            if subscription.get("subscription_key"):
                return Subscription.search([("subscription_key", "=", subscription["subscription_key"])], limit=1)
        return None

    def _resolve_notification(self, notification):
        Notification = self._notification_model()
        if Notification is None:
            return None
        if hasattr(notification, "_name") and getattr(notification, "_name", None) == "gateway.ads.notification":
            return notification.exists()
        if isinstance(notification, int):
            return Notification.browse(notification).exists()
        if isinstance(notification, dict):
            if notification.get("notification_id"):
                return Notification.browse(int(notification["notification_id"])).exists()
            if notification.get("code"):
                return Notification.search([("code", "=", notification["code"])], limit=1)
        return None

    def _resolve_adapter_from_payload(self, payload):
        Adapter = self._model("gateway.ads.adapter")
        if Adapter is None:
            return None
        if hasattr(payload, "_name") and getattr(payload, "_name", None) == "gateway.ads.adapter":
            return payload.exists()
        if isinstance(payload, int):
            return Adapter.browse(payload).exists()
        payload = self._json_loads(payload, {})
        if isinstance(payload, dict):
            if payload.get("adapter_id"):
                return Adapter.browse(int(payload["adapter_id"])).exists()
            if payload.get("adapter_code"):
                return Adapter.search([("code", "=", payload["adapter_code"])], limit=1)
        return None

    def _resolve_symbol_from_callback(self, payload, adapter=None):
        Symbol = self._symbol_model()
        if Symbol is None:
            return None
        if hasattr(payload, "_name") and getattr(payload, "_name", None) == "gateway.ads.symbol":
            return payload.exists()
        if isinstance(payload, int):
            return Symbol.browse(payload).exists()
        payload = self._json_loads(payload, {})
        if not isinstance(payload, dict):
            return None
        if payload.get("symbol_id"):
            return Symbol.browse(int(payload["symbol_id"])).exists()
        if payload.get("symbol_code") and payload.get("adapter_code"):
            return Symbol.search([("adapter_id.code", "=", payload["adapter_code"]), ("code", "=", payload["symbol_code"])], limit=1)
        if payload.get("symbol_code") and adapter:
            return Symbol.search([("adapter_id", "=", adapter.id), ("code", "=", payload["symbol_code"])], limit=1)
        if payload.get("subscription_key"):
            Subscription = self._subscription_model()
            if Subscription is not None:
                subscription = Subscription.search([("subscription_key", "=", payload["subscription_key"])], limit=1)
                if subscription:
                    return subscription.symbol_id
        if adapter and adapter.symbol_ids:
            return adapter.symbol_ids.filtered(lambda record: record.active)[:1]
        return None

    def _symbol_subscription_key(self, symbol, subscription_mode=None):
        helper = self.client_helper
        return helper.build_subscription_key(
            adapter_code=self._adapter_code(symbol.adapter_id) if symbol else None,
            symbol_code=symbol.code if symbol else None,
            subscription_mode=subscription_mode or getattr(symbol, "subscription_mode", None) or "change",
        )

    def _symbol_dispatch_signal(self, symbol, event_kind="change"):
        helper = self.client_helper
        return helper.build_dispatch_signal(
            adapter_code=self._adapter_code(symbol.adapter_id) if symbol else None,
            symbol_code=symbol.code if symbol else None,
            event_kind=event_kind or "change",
        )

    def _subscription_summary(self, adapter):
        Subscription = self._subscription_model()
        if Subscription is None or not adapter:
            return {"total": 0, "active": 0, "subscribed": 0, "requested": 0, "paused": 0, "error": 0}
        subscriptions = Subscription.search([("adapter_id", "=", adapter.id)])
        summary = {"total": len(subscriptions), "active": 0, "subscribed": 0, "requested": 0, "paused": 0, "error": 0}
        for subscription in subscriptions:
            if getattr(subscription, "active", True) and subscription.state in {"requested", "subscribed"}:
                summary["active"] += 1
            summary[subscription.state] = summary.get(subscription.state, 0) + 1
        return summary

    def _notification_summary(self, adapter):
        Notification = self._notification_model()
        if Notification is None or not adapter:
            return {"total": 0, "queued": 0, "dispatched": 0, "acknowledged": 0, "failed": 0, "dropped": 0}
        notifications = Notification.search([("adapter_id", "=", adapter.id)])
        summary = {"total": len(notifications), "queued": 0, "dispatched": 0, "acknowledged": 0, "failed": 0, "dropped": 0}
        for notification in notifications:
            summary[notification.state] = summary.get(notification.state, 0) + 1
        return summary

    def _latest_datetime(self, values):
        values = [value for value in values if value]
        return max(values) if values else None

    def _attach_stream_summary(self, adapter, result):
        if not result or not isinstance(result, dict):
            return result
        data = result.get("data")
        if not isinstance(data, dict):
            data = {}
            result["data"] = data
        data["subscription_support"] = self.client_helper.describe_subscription_support()
        data["subscription_summary"] = self._subscription_summary(adapter)
        data["notification_summary"] = self._notification_summary(adapter)
        return result

    def _runtime_capability_summary(self, capability):
        supports = capability.get("supports") or {}
        labels = []
        for key, label in (
            ("poll", "poll"),
            ("push", "push"),
            ("read", "read"),
            ("write", "write"),
            ("subscribe", "subscribe"),
            ("diagnostic", "diagnostics"),
            ("repair", "repair"),
            ("reload", "reload"),
            ("load", "load"),
            ("unload", "unload"),
            ("dispatch", "dispatch"),
        ):
            if supports.get(key):
                labels.append(label)
        base = capability.get("adapter_type") or capability.get("transport") or "runtime"
        return f"{base}: {', '.join(labels)}" if labels else base

    def _resolve_adapter(self, adapter):
        Adapter = self._model("gateway.ads.adapter")
        if Adapter is None:
            return None
        if hasattr(adapter, "_name") and getattr(adapter, "_name", None) == "gateway.ads.adapter":
            return adapter.exists()
        if isinstance(adapter, int):
            return Adapter.browse(adapter).exists()
        if isinstance(adapter, dict):
            if adapter.get("adapter_id"):
                return Adapter.browse(int(adapter["adapter_id"])).exists()
            if adapter.get("code"):
                return Adapter.search([("code", "=", adapter["code"])], limit=1)
        return None

    def _resolve_symbol(self, symbol):
        Symbol = self._model("gateway.ads.symbol")
        if Symbol is None:
            return None
        if hasattr(symbol, "_name") and getattr(symbol, "_name", None) == "gateway.ads.symbol":
            return symbol.exists()
        if isinstance(symbol, int):
            return Symbol.browse(symbol).exists()
        if isinstance(symbol, dict):
            if symbol.get("symbol_id"):
                return Symbol.browse(int(symbol["symbol_id"])).exists()
            if symbol.get("adapter_id") and symbol.get("code"):
                return Symbol.search([("adapter_id", "=", int(symbol["adapter_id"])), ("code", "=", symbol["code"])], limit=1)
        return None

    def _symbol_signal_name(self, symbol):
        return f"gateway.ads.symbol:{symbol.adapter_id.code}:{symbol.code}"

    def _store_runtime_feedback(self, adapter, result, touch_field=None):
        if not adapter or not result:
            return result
        data = result.get("data") or {}
        capability = data.get("capability") or {}
        coordinator = data.get("coordinator") or {}
        runtime_adapter = data.get("adapter") or {}
        values = {
            "diagnostic_state": self._json_dumps(result),
            "runtime_diagnostic_summary": self._json_dumps({"capability": capability, "coordinator": coordinator, "signal": data.get("signal")}),
        }
        if runtime_adapter:
            values["runtime_adapter_id"] = runtime_adapter.get("id") if isinstance(runtime_adapter, dict) else False
        if capability:
            values["runtime_capability_json"] = capability.get("capability_json") or self._json_dumps(capability)
            values["runtime_capability_summary"] = self._runtime_capability_summary(capability)
        if touch_field:
            values[touch_field] = fields.Datetime.now()
        adapter.write(values)
        return result

    def _create_diagnostic(self, adapter, kind, state, message, detail=None, payload=None, result=None, symbol=None, subscription=None, notification=None):
        Diagnostic = self._model("gateway.ads.diagnostic")
        if Diagnostic is None:
            return None
        subscription_model = self._subscription_model()
        notification_model = self._notification_model()
        return Diagnostic.create(
            {
                "name": f"{adapter.code}-{kind}",
                "adapter_id": adapter.id,
                "symbol_id": symbol.id if symbol else False,
                "subscription_id": subscription.id if subscription and subscription_model and self._model_has_field(Diagnostic, "subscription_id") else False,
                "notification_id": notification.id if notification and notification_model and self._model_has_field(Diagnostic, "notification_id") else False,
                "kind": kind,
                "state": state,
                "message": message,
                "detail": detail or "",
                "payload_json": self._json_dumps(payload or {}),
                "result_json": self._json_dumps(result or {}),
                "observed_at": fields.Datetime.now(),
            }
        )

    def _upsert_subscription(self, symbol, *, state="requested", extra=None):
        Subscription = self._subscription_model()
        if Subscription is None or not symbol:
            return None
        extra = dict(extra or {})
        subscription_key = extra.get("subscription_key") or symbol.subscription_key or self._symbol_subscription_key(symbol, getattr(symbol, "subscription_mode", None))
        subscription = Subscription.search([("subscription_key", "=", subscription_key)], limit=1)
        values = {
            "name": extra.get("name") or f"{symbol.code} subscription",
            "code": extra.get("code") or subscription_key,
            "adapter_id": symbol.adapter_id.id,
            "symbol_id": symbol.id,
            "subscription_key": subscription_key,
            "dispatcher_signal": extra.get("dispatcher_signal") or symbol.dispatcher_signal or self._symbol_dispatch_signal(symbol, "change"),
            "subscription_mode": extra.get("subscription_mode") or symbol.subscription_mode or "change",
            "state": state,
            "active": extra.get("active", True),
            "priority": extra.get("priority", 10),
            "notify_on_change": extra.get("notify_on_change", symbol.notify_on_change),
            "payload_json": self._json_dumps(extra.get("payload") or {}),
        }
        now = fields.Datetime.now()
        if state == "subscribed":
            values["last_subscribed_at"] = now
        if state in {"paused", "cancelled"}:
            values["last_unsubscribed_at"] = now
        if state == "error":
            values["last_error_at"] = now
        if subscription:
            subscription.write(values)
        else:
            subscription = Subscription.create(values)
        symbol.write(
            {
                "subscription_enabled": state in {"requested", "subscribed"},
                "subscription_state": state if state in dict(symbol._fields["subscription_state"].selection) else symbol.subscription_state,
                "subscription_signal": values["dispatcher_signal"],
                "subscription_handle": subscription.subscription_key,
                "subscription_key": subscription_key,
                "dispatcher_signal": values["dispatcher_signal"],
                "last_subscription_at": now if state in {"requested", "subscribed"} else symbol.last_subscription_at,
                "last_unsubscription_at": now if state in {"paused", "cancelled"} else symbol.last_unsubscription_at,
                "last_error": extra.get("note") if state == "error" else symbol.last_error,
            }
        )
        return subscription

    def _create_notification(self, symbol, *, event_kind="update", state="queued", source="manual", payload=None, result=None, value_text=None, value_json=None, severity="low", subscription=None):
        Notification = self._notification_model()
        if Notification is None or not symbol:
            return None
        subscription = self._resolve_subscription(subscription) if subscription else None
        payload = dict(payload or {})
        result = dict(result or {})
        now = fields.Datetime.now()
        notification_values = {
            "name": f"{symbol.code}:{event_kind}",
            "code": f"{symbol.code}:{event_kind}:{now.strftime('%Y%m%d%H%M%S%f')}",
            "adapter_id": symbol.adapter_id.id,
            "symbol_id": symbol.id,
            "subscription_id": subscription.id if subscription else False,
            "event_kind": event_kind or "update",
            "state": state,
            "severity": severity,
            "source": source,
            "payload_json": self._json_dumps(payload),
            "value_text": value_text,
            "value_json": self._json_dumps(value_json) if isinstance(value_json, (dict, list)) else value_json,
            "result_json": self._json_dumps(result),
            "received_at": now,
        }
        if state in {"dispatched", "acknowledged"}:
            notification_values["dispatched_at"] = now
        if state == "acknowledged":
            notification_values["acknowledged_at"] = now
        notification = Notification.create(
            notification_values
        )
        now = fields.Datetime.now()
        symbol.write(
            {
                "last_event_at": now,
                "last_dispatch_at": now if state in {"dispatched", "acknowledged"} else symbol.last_dispatch_at,
                "last_value_text": value_text or symbol.last_value_text,
                "last_value_json": self._json_dumps(value_json) if isinstance(value_json, (dict, list)) else symbol.last_value_json,
                "update_count": (symbol.update_count or 0) + 1,
                "subscription_state": "subscribed" if state in {"dispatched", "acknowledged"} and symbol.subscription_state not in {"disabled", "cancelled"} else symbol.subscription_state,
            }
        )
        if subscription:
            subscription.write({"last_notified_at": now, "listener_count": (subscription.listener_count or 0) + 1})
        return notification

    def _consume_callback_payload(self, payload, adapter=None, symbol=None, subscription=None, extra=None):
        payload_data = self._json_loads(payload, {})
        if not isinstance(payload_data, dict):
            payload_data = {"raw_callback": payload_data}
        adapter = self._resolve_adapter(adapter) if adapter else self._resolve_adapter_from_payload(payload_data)
        symbol = self._resolve_symbol(symbol) if symbol else self._resolve_symbol_from_callback(payload_data, adapter=adapter)
        if not adapter and symbol:
            adapter = symbol.adapter_id
        if not adapter:
            return {"ok": False, "errors": ["Adapter not found"]}
        if not symbol:
            return {"ok": False, "errors": ["Symbol not found"]}
        subscription = self._resolve_subscription(subscription) if subscription else None
        if not subscription and payload_data.get("subscription_key"):
            subscription = self._resolve_subscription(payload_data)
        if not subscription:
            subscription = self._upsert_subscription(
                symbol,
                state="subscribed",
                extra={
                    "subscription_key": payload_data.get("subscription_key"),
                    "dispatcher_signal": payload_data.get("signal") or symbol.dispatcher_signal,
                    "subscription_mode": payload_data.get("subscription_mode") or symbol.subscription_mode,
                    "notify_on_change": payload_data.get("notify_on_change", symbol.notify_on_change),
                    "payload": payload_data,
                },
            )
        normalized = self.client_helper.normalize_device_notification_payload(
            payload_data,
            adapter_code=adapter.code,
            symbol_code=symbol.code,
            subscription_key=subscription.subscription_key if subscription else payload_data.get("subscription_key"),
            event_kind=payload_data.get("event_kind") or payload_data.get("kind") or "change",
            source=payload_data.get("source") or "runtime",
        )
        notification = self._create_notification(
            symbol,
            event_kind=normalized.get("event_kind") or "change",
            state=normalized.get("state") or "dispatched",
            source=normalized.get("source") or "runtime",
            payload={"callback": payload_data, "normalized": normalized, "extra": extra or {}},
            result=normalized,
            value_text=normalized.get("value_text"),
            value_json=normalized.get("value_json"),
            severity=normalized.get("severity") or "low",
            subscription=subscription,
        )
        if normalized.get("acknowledged") or normalized.get("state") == "acknowledged":
            self.acknowledge_notification(notification, extra={"note": normalized.get("note"), "payload": payload_data, "normalized": normalized})
        diagnostic = self._create_diagnostic(
            adapter,
            "snapshot",
            "success",
            "ADS device_notification callback consumed",
            detail=normalized.get("signal") or symbol.subscription_signal or symbol.dispatcher_signal or symbol.code,
            payload={"callback": payload_data, "normalized": normalized, "extra": extra or {}},
            result={"notification": notification.code if notification else None, "subscription": subscription.subscription_key if subscription else None},
            symbol=symbol,
            subscription=subscription,
            notification=notification,
        )
        return {
            "ok": True,
            "adapter_id": adapter.id,
            "symbol_id": symbol.id,
            "subscription_id": subscription.id if subscription else None,
            "notification_id": notification.id if notification else None,
            "diagnostic_id": diagnostic.id if diagnostic else None,
            "callback": normalized,
        }

    def consume_device_notification(self, payload, adapter=None, symbol=None, subscription=None, extra=None):
        return self._consume_callback_payload(payload, adapter=adapter, symbol=symbol, subscription=subscription, extra=extra)

    def acknowledge_notification(self, notification, extra=None):
        notification = self._resolve_notification(notification)
        if not notification:
            return {"ok": False, "errors": ["Notification not found"]}
        extra = dict(extra or {})
        now = fields.Datetime.now()
        notification._set_state("acknowledged", note=extra.get("note"))
        symbol = notification.symbol_id.exists()
        if symbol:
            symbol.write(
                {
                    "last_event_at": now,
                    "last_dispatch_at": now,
                    "subscription_state": "subscribed" if symbol.subscription_state not in {"disabled", "cancelled"} else symbol.subscription_state,
                }
            )
        subscription = notification.subscription_id.exists() if notification.subscription_id else None
        if subscription:
            subscription.write({"last_notified_at": now})
        diagnostic = self._create_diagnostic(
            notification.adapter_id,
            "diagnostic",
            "success",
            "ADS notification acknowledged",
            detail=notification.event_kind,
            payload={"notification": notification.code, "extra": extra},
            result={"notification_state": notification.state},
            symbol=symbol,
            subscription=subscription,
            notification=notification,
        )
        return {
            "ok": True,
            "notification_id": notification.id,
            "symbol_id": symbol.id if symbol else None,
            "subscription_id": subscription.id if subscription else None,
            "diagnostic_id": diagnostic.id if diagnostic else None,
        }

    def preview_subscription_plan(self, adapter):
        adapter = self._resolve_adapter(adapter)
        if not adapter:
            return {"ok": False, "errors": ["Adapter not found"]}
        helper_state = self.client_helper.describe_subscription_support()
        symbols = adapter.symbol_ids.sorted(lambda record: (record.sequence, record.id))
        plans = []
        for symbol in symbols:
            subscription_key = symbol.subscription_key or self.client_helper.build_subscription_key(
                adapter_code=adapter.code,
                symbol_code=symbol.code,
                subscription_mode=symbol.subscription_mode or "change",
            )
            plans.append(
                {
                    "symbol": symbol.code,
                    "subscription_key": subscription_key,
                    "signal": symbol.dispatcher_signal or self.client_helper.build_dispatch_signal(
                        adapter_code=adapter.code,
                        symbol_code=symbol.code,
                        event_kind="change",
                    ),
                    "mode": symbol.subscription_mode or "change",
                    "notify_on_change": symbol.notify_on_change,
                }
            )
        summary = {
            "symbol_count": len(symbols),
            "subscribable_count": len(symbols.filtered(lambda record: record.active and record.notify_on_change)),
            "readable_count": len(symbols.filtered(lambda record: record.access_mode in {"read", "read_write"})),
            "writable_count": len(symbols.filtered(lambda record: record.access_mode in {"write", "read_write"})),
            "subscription_backend": helper_state.get("subscription_backend"),
        }
        diagnostic = self._create_diagnostic(
            adapter,
            "browse",
            "info",
            "ADS subscription plan preview generated",
            detail=f"{summary['subscribable_count']} symbol(s)",
            payload={"plans": plans, "support": helper_state},
            result=summary,
        )
        adapter.write({"runtime_diagnostic_summary": self._json_dumps({"subscription_plan": summary})})
        return {"ok": True, "diagnostic_id": diagnostic.id if diagnostic else None, "summary": summary, "plans": plans, "support": helper_state}

    def subscribe_symbol(self, symbol, extra=None):
        symbol = self._resolve_symbol(symbol)
        if not symbol:
            return {"ok": False, "errors": ["Symbol not found"]}
        subscription = self._upsert_subscription(symbol, state="requested", extra=extra)
        notification = self._create_notification(
            symbol,
            event_kind="subscribe",
            state="dispatched",
            source="subscription",
            payload=extra or {},
            result={"subscription_key": subscription.subscription_key if subscription else None},
            subscription=subscription,
        )
        symbol.write({"subscription_state": "requested"})
        diagnostic = self._create_diagnostic(
            symbol.adapter_id,
            "diagnostic",
            "success",
            "ADS subscription requested",
            detail=symbol.subscription_signal or symbol.dispatcher_signal or symbol.code,
            payload=extra or {"symbol": symbol.code, "adapter": self._adapter_code(symbol.adapter_id)},
            result={"subscription": subscription.subscription_key if subscription else None, "notification": notification.code if notification else None},
            symbol=symbol,
            subscription=subscription,
            notification=notification,
        )
        return {"ok": True, "subscription_id": subscription.id if subscription else None, "notification_id": notification.id if notification else None, "diagnostic_id": diagnostic.id if diagnostic else None}

    def unsubscribe_symbol(self, symbol, extra=None):
        symbol = self._resolve_symbol(symbol)
        if not symbol:
            return {"ok": False, "errors": ["Symbol not found"]}
        subscription = self._upsert_subscription(symbol, state="cancelled", extra=extra)
        notification = self._create_notification(
            symbol,
            event_kind="unsubscribe",
            state="dispatched",
            source="subscription",
            payload=extra or {},
            result={"subscription_key": subscription.subscription_key if subscription else None},
            subscription=subscription,
        )
        symbol.write({"subscription_state": "cancelled", "subscription_enabled": False})
        diagnostic = self._create_diagnostic(
            symbol.adapter_id,
            "diagnostic",
            "success",
            "ADS subscription cancelled",
            detail=symbol.subscription_signal or symbol.dispatcher_signal or symbol.code,
            payload=extra or {},
            result={"subscription": subscription.subscription_key if subscription else None, "notification": notification.code if notification else None},
            symbol=symbol,
            subscription=subscription,
            notification=notification,
        )
        return {"ok": True, "subscription_id": subscription.id if subscription else None, "notification_id": notification.id if notification else None, "diagnostic_id": diagnostic.id if diagnostic else None}

    def push_symbol_notification(self, symbol, extra=None):
        symbol = self._resolve_symbol(symbol)
        if not symbol:
            return {"ok": False, "errors": ["Symbol not found"]}
        subscription = self._upsert_subscription(symbol, state="subscribed", extra=extra)
        notification = self._create_notification(
            symbol,
            event_kind=(extra or {}).get("event_kind") or "update",
            state="dispatched",
            source=(extra or {}).get("source") or "manual",
            payload=extra or {},
            result={"subscription_key": subscription.subscription_key if subscription else None},
            value_text=(extra or {}).get("value_text") or symbol.last_value_text or symbol.code,
            value_json=(extra or {}).get("value_json") or {},
            severity=(extra or {}).get("severity") or "low",
            subscription=subscription,
        )
        diagnostic = self._create_diagnostic(
            symbol.adapter_id,
            "snapshot",
            "success",
            "ADS symbol notification published",
            detail=symbol.subscription_signal or symbol.dispatcher_signal or symbol.code,
            payload=extra or {},
            result={"notification": notification.code if notification else None},
            symbol=symbol,
            subscription=subscription,
            notification=notification,
        )
        return {"ok": True, "notification_id": notification.id if notification else None, "subscription_id": subscription.id if subscription else None, "diagnostic_id": diagnostic.id if diagnostic else None}

    def refresh_symbol_subscription(self, symbol, extra=None):
        symbol = self._resolve_symbol(symbol)
        if not symbol:
            return {"ok": False, "errors": ["Symbol not found"]}
        if symbol.subscription_state not in {"subscribed", "requested"}:
            return self.subscribe_symbol(symbol, extra=extra)
        subscription = self._upsert_subscription(symbol, state="subscribed", extra=extra)
        diagnostic = self._create_diagnostic(
            symbol.adapter_id,
            "diagnostic",
            "info",
            "ADS subscription refreshed",
            detail=symbol.subscription_signal or symbol.dispatcher_signal or symbol.code,
            payload=extra or {},
            result={"subscription": subscription.subscription_key if subscription else None},
            symbol=symbol,
            subscription=subscription,
        )
        return {"ok": True, "subscription_id": subscription.id if subscription else None, "diagnostic_id": diagnostic.id if diagnostic else None}

    def subscribe_adapter_symbols(self, adapter):
        adapter = self._resolve_adapter(adapter)
        if not adapter:
            return {"ok": False, "errors": ["Adapter not found"]}
        results = [self.subscribe_symbol(symbol) for symbol in adapter.symbol_ids.filtered(lambda record: record.active and record.notify_on_change)]
        diagnostic = self._create_diagnostic(adapter, "diagnostic", "success", "ADS adapter subscriptions requested", detail=f"{len(results)} symbol(s)", payload={"results": results}, result=self._subscription_summary(adapter))
        return {"ok": True, "results": results, "diagnostic_id": diagnostic.id if diagnostic else None}

    def unsubscribe_adapter_symbols(self, adapter):
        adapter = self._resolve_adapter(adapter)
        if not adapter:
            return {"ok": False, "errors": ["Adapter not found"]}
        results = [self.unsubscribe_symbol(symbol) for symbol in adapter.symbol_ids.filtered(lambda record: record.subscription_state != "cancelled")]
        diagnostic = self._create_diagnostic(adapter, "diagnostic", "success", "ADS adapter subscriptions cancelled", detail=f"{len(results)} symbol(s)", payload={"results": results}, result=self._subscription_summary(adapter))
        return {"ok": True, "results": results, "diagnostic_id": diagnostic.id if diagnostic else None}

    def push_test_notification(self, adapter):
        adapter = self._resolve_adapter(adapter)
        if not adapter:
            return {"ok": False, "errors": ["Adapter not found"]}
        symbol = adapter.symbol_ids.filtered(lambda record: record.active)[:1]
        symbol = symbol[0] if symbol else False
        if not symbol:
            return {"ok": False, "errors": ["No active symbol found"]}
        result = self.consume_device_notification(
            {
                "adapter_code": adapter.code,
                "symbol_code": symbol.code,
                "subscription_key": symbol.subscription_key,
                "event_kind": "diagnostic",
                "source": "manual",
                "value_text": symbol.last_value_text or symbol.code,
                "value_json": {"value": symbol.last_value_text or symbol.code},
                "acknowledged": True,
                "severity": "low",
                "note": "Simulated ADS device_notification callback",
            },
            adapter=adapter,
            symbol=symbol,
        )
        return result

    def _write_symbol_update(self, symbol, *, value=None, payload=None, state=None, subscription_state=None, error=None):
        if not symbol:
            return None
        now = fields.Datetime.now()
        values = {}
        if value is not None:
            values["last_value_text"] = str(value)
            values["last_value_json"] = self._json_dumps({"value": value})
        if state:
            values["state"] = state
        if subscription_state:
            values["subscription_state"] = subscription_state
        if error is not None:
            values["last_error"] = error or False
        values["last_event_at"] = now
        values["last_dispatch_at"] = now
        values["last_read_at"] = now
        values["update_count"] = int(symbol.update_count or 0) + 1
        if payload is not None and value is None:
            values["last_value_json"] = self._json_dumps(payload)
        symbol.write(values)
        return symbol

    def register_adapter_definition(self, adapter_payload):
        Adapter = self._model("gateway.ads.adapter")
        if Adapter is None:
            return {"ok": False, "errors": ["gateway.ads.adapter model is not installed."]}
        payload = dict(adapter_payload or {})
        code = payload.get("code")
        adapter = Adapter.search([("code", "=", code)], limit=1) if code else Adapter.browse()
        values = {
            "name": payload.get("name") or code or _("ADS Adapter"),
            "code": code or self.env["ir.sequence"].next_by_code("gateway.ads.adapter") or _("New"),
            "device_code": payload.get("device_code"),
            "host": payload.get("host"),
            "port": payload.get("port"),
            "ams_net_id": payload.get("ams_net_id"),
            "ads_port": payload.get("ads_port"),
            "connection_target": payload.get("connection_target"),
            "poll_interval_seconds": payload.get("poll_interval_seconds"),
            "timeout_seconds": payload.get("timeout_seconds"),
            "retry_limit": payload.get("retry_limit"),
            "config_json": payload.get("config_json"),
            "config_text": payload.get("config_text"),
        }
        entry_code = payload.get("entry_code")
        app_code = payload.get("app_code")
        workstation_code = payload.get("workstation_code")
        Entry = self._model("gateway.entry")
        App = self._model("shopfloor.app")
        Workstation = self._model("shopfloor.workstation")
        if entry_code and Entry:
            values["entry_id"] = Entry.search([("code", "=", entry_code)], limit=1).id or False
        if app_code and App:
            values["app_id"] = App.search([("code", "=", app_code)], limit=1).id or False
        if workstation_code and Workstation:
            values["workstation_id"] = Workstation.search([("code", "=", workstation_code)], limit=1).id or False
        values = {key: value for key, value in values.items() if value not in (None, "")}
        if adapter:
            adapter.write(values)
        else:
            adapter = Adapter.create(values)
        runtime_result = self._runtime_service().register_adapter_definition(adapter._runtime_payload())
        capability = self._runtime_service().build_capability_payload(payload=adapter._runtime_payload())
        runtime_adapter = self._model("gateway.runtime.adapter")
        runtime_adapter = runtime_adapter.search([("code", "=", adapter.code)], limit=1) if runtime_adapter else None
        if runtime_adapter:
            adapter.write({"runtime_adapter_id": runtime_adapter.id})
        diagnostic = self._create_diagnostic(
            adapter,
            "connect",
            "info",
            "Adapter definition synchronized",
            detail=adapter.connection_target or adapter.ams_net_id or adapter.host or "",
            payload=payload,
            result={"state": adapter.state, "code": adapter.code, "runtime_result": runtime_result, "capability": capability},
        )
        adapter.write(
            {
                "last_sync_at": fields.Datetime.now(),
                "runtime_capability_json": capability.get("capability_json") or self._json_dumps(capability),
                "runtime_capability_summary": self._runtime_capability_summary(capability),
                "runtime_diagnostic_summary": self._json_dumps({"registration": {"state": adapter.state, "code": adapter.code}, "runtime_result": runtime_result, "capability": capability}),
                "diagnostic_state": self._json_dumps({"registration": {"state": adapter.state, "code": adapter.code}, "runtime_result": runtime_result}),
            }
        )
        return {"ok": True, "adapter_id": adapter.id, "runtime_result": runtime_result, "diagnostic_id": diagnostic.id if diagnostic else None}

    def preview_connectivity(self, adapter):
        adapter = self._resolve_adapter(adapter)
        if not adapter:
            return {"ok": False, "errors": ["Adapter not found"]}
        helper_state = self.client_helper.describe()
        capability = self._runtime_service().build_capability_payload(payload=adapter._runtime_payload())
        diagnostic = self._create_diagnostic(
            adapter,
            "connect",
            "warning" if not helper_state["available"] else "success",
            "ADS connectivity preview generated",
            detail=adapter.connection_target or adapter.ams_net_id or "",
            payload=adapter._runtime_payload(),
            result={"client": helper_state, "capability": capability},
        )
        adapter.write(
            {
                "runtime_capability_json": capability.get("capability_json") or self._json_dumps(capability),
                "runtime_capability_summary": self._runtime_capability_summary(capability),
                "runtime_diagnostic_summary": self._json_dumps({"client": helper_state, "capability": capability}),
            }
        )
        return {"ok": True, "diagnostic_id": diagnostic.id if diagnostic else None, "details": helper_state, "capability": capability}

    def preview_symbol_map(self, adapter):
        adapter = self._resolve_adapter(adapter)
        if not adapter:
            return {"ok": False, "errors": ["Adapter not found"]}
        symbols = adapter.symbol_ids.sorted(lambda record: (record.sequence, record.id))
        summary = {
            "symbol_count": len(symbols),
            "readable_count": len(symbols.filtered(lambda record: record.access_mode in {"read", "read_write"})),
            "writable_count": len(symbols.filtered(lambda record: record.access_mode in {"write", "read_write"})),
        }
        diagnostic = self._create_diagnostic(adapter, "browse", "info", "ADS symbol map preview generated", detail=f"{summary['symbol_count']} symbol(s)", payload=adapter._runtime_payload(), result=summary)
        adapter.write({"runtime_diagnostic_summary": self._json_dumps({"symbol_map": summary})})
        return {"ok": True, "diagnostic_id": diagnostic.id if diagnostic else None, "summary": summary}

    def submit_test_read(self, adapter, extra=None):
        adapter = self._resolve_adapter(adapter)
        if not adapter:
            return {"ok": False, "errors": ["Adapter not found"]}
        if not self._model("gateway.ads.symbol"):
            return {"ok": False, "errors": ["gateway.ads.symbol model is not installed"]}
        symbols = adapter.symbol_ids.filtered(lambda record: record.active)
        symbol = symbols[:1]
        symbol = symbol[0] if symbol else False
        if symbol:
            symbol.write({"last_read_at": fields.Datetime.now(), "last_value_text": symbol.last_value_text or "sample"})
        diagnostic = self._create_diagnostic(adapter, "read", "success", "ADS test read collected", detail=symbol.symbol_path if symbol else "", payload=extra or adapter._runtime_payload(), result={"symbol": symbol.code if symbol else None, "value": symbol.last_value_text if symbol else None}, symbol=symbol)
        adapter.write({"last_connect_at": fields.Datetime.now()})
        return {"ok": True, "diagnostic_id": diagnostic.id if diagnostic else None, "symbol": {"id": symbol.id, "code": symbol.code} if symbol else None}

    def submit_test_write(self, adapter, extra=None):
        adapter = self._resolve_adapter(adapter)
        if not adapter:
            return {"ok": False, "errors": ["Adapter not found"]}
        if not self._model("gateway.ads.symbol"):
            return {"ok": False, "errors": ["gateway.ads.symbol model is not installed"]}
        symbols = adapter.symbol_ids.filtered(lambda record: record.active and record.writable)
        symbol = symbols[:1]
        symbol = symbol[0] if symbol else False
        if symbol:
            symbol.write({"last_write_at": fields.Datetime.now(), "last_value_text": symbol.last_value_text or "written"})
        diagnostic = self._create_diagnostic(adapter, "write", "success", "ADS test write recorded", detail=symbol.symbol_path if symbol else "", payload=extra or adapter._runtime_payload(), result={"symbol": symbol.code if symbol else None, "value": symbol.last_value_text if symbol else None}, symbol=symbol)
        adapter.write({"last_connect_at": fields.Datetime.now()})
        return {"ok": True, "diagnostic_id": diagnostic.id if diagnostic else None, "symbol": {"id": symbol.id, "code": symbol.code} if symbol else None}

    def refresh_runtime(self, adapter, extra=None):
        adapter = self._resolve_adapter(adapter)
        if not adapter:
            return {"ok": False, "errors": ["Adapter not found"]}
        self.register_adapter_definition(adapter._runtime_payload())
        result = self._runtime_service().refresh_runtime({**adapter._runtime_payload(), **dict(extra or {})})
        self._attach_stream_summary(adapter, result)
        self._store_runtime_feedback(adapter, result, touch_field="last_sync_at")
        return result

    def repair_runtime(self, adapter, extra=None):
        adapter = self._resolve_adapter(adapter)
        if not adapter:
            return {"ok": False, "errors": ["Adapter not found"]}
        self.register_adapter_definition(adapter._runtime_payload())
        result = self._runtime_service().repair_runtime({**adapter._runtime_payload(), **dict(extra or {})})
        self._attach_stream_summary(adapter, result)
        self._store_runtime_feedback(adapter, result)
        return result

    def load_runtime(self, adapter, extra=None):
        adapter = self._resolve_adapter(adapter)
        if not adapter:
            return {"ok": False, "errors": ["Adapter not found"]}
        self.register_adapter_definition(adapter._runtime_payload())
        result = self._runtime_service().load_runtime({**adapter._runtime_payload(), **dict(extra or {})})
        self._attach_stream_summary(adapter, result)
        self._store_runtime_feedback(adapter, result, touch_field="last_sync_at")
        return result

    def reload_runtime(self, adapter, extra=None):
        adapter = self._resolve_adapter(adapter)
        if not adapter:
            return {"ok": False, "errors": ["Adapter not found"]}
        self.register_adapter_definition(adapter._runtime_payload())
        result = self._runtime_service().reload_runtime({**adapter._runtime_payload(), **dict(extra or {})})
        self._attach_stream_summary(adapter, result)
        self._store_runtime_feedback(adapter, result, touch_field="last_sync_at")
        return result

    def runtime_diagnostics(self, adapter, extra=None):
        adapter = self._resolve_adapter(adapter)
        if not adapter:
            return {"ok": False, "errors": ["Adapter not found"]}
        self.register_adapter_definition(adapter._runtime_payload())
        result = self._runtime_service().runtime_diagnostics({**adapter._runtime_payload(), **dict(extra or {})})
        self._attach_stream_summary(adapter, result)
        self._store_runtime_feedback(adapter, result)
        return result

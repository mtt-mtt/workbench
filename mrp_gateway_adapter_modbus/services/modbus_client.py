try:
    from pymodbus.client import ModbusSerialClient, ModbusTcpClient

    _PYMODBUS_IMPORT_PATH = "pymodbus.client"
except Exception:
    try:
        from pymodbus.client.sync import ModbusSerialClient, ModbusTcpClient

        _PYMODBUS_IMPORT_PATH = "pymodbus.client.sync"
    except Exception:
        ModbusSerialClient = None
        ModbusTcpClient = None
        _PYMODBUS_IMPORT_PATH = None


class OptionalPymodbusClient:
    def __init__(self, adapter_data):
        self.adapter_data = dict(adapter_data or {})

    @staticmethod
    def available():
        return ModbusTcpClient is not None or ModbusSerialClient is not None

    @staticmethod
    def import_path():
        return _PYMODBUS_IMPORT_PATH

    def capability_summary(self):
        transport = self.adapter_data.get("transport") or "tcp"
        return {
            "available": self.available(),
            "import_path": self.import_path(),
            "transport": transport,
            "supports_tcp": ModbusTcpClient is not None,
            "supports_serial": ModbusSerialClient is not None,
            "supports_tcp_tls": transport == "tcp_tls" and ModbusTcpClient is not None,
            "supported": transport == "mock"
            or (
                self.available()
                and (
                    transport in {"tcp", "tcp_tls"} and ModbusTcpClient is not None
                    or transport in {"rtu", "ascii"} and ModbusSerialClient is not None
                )
            ),
        }

    def create_client(self):
        transport = self.adapter_data.get("transport") or "tcp"
        timeout = float(self.adapter_data.get("timeout_seconds") or 3.0)
        if transport == "mock":
            return {
                "ok": True,
                "client": None,
                "mock": True,
                "details": {
                    **self.capability_summary(),
                    "mode": "mock",
                    "timeout": timeout,
                },
            }
        if not self.available():
            return {
                "ok": False,
                "available": False,
                "reason": "pymodbus is not installed",
                "details": self.capability_summary(),
            }
        if transport in {"tcp", "tcp_tls"}:
            if ModbusTcpClient is None:
                return {
                    "ok": False,
                    "available": False,
                    "reason": "TCP client class is unavailable in this pymodbus build",
                    "details": self.capability_summary(),
                }
            client = ModbusTcpClient(
                host=self.adapter_data.get("host") or "127.0.0.1",
                port=int(self.adapter_data.get("port") or 502),
                timeout=timeout,
            )
            return {
                "ok": True,
                "client": client,
                "details": {
                    **self.capability_summary(),
                    "mode": "tcp",
                    "host": self.adapter_data.get("host") or "127.0.0.1",
                    "port": int(self.adapter_data.get("port") or 502),
                    "timeout": timeout,
                },
            }
        if transport in {"rtu", "ascii"}:
            if ModbusSerialClient is None:
                return {
                    "ok": False,
                    "available": False,
                    "reason": "Serial client class is unavailable in this pymodbus build",
                    "details": self.capability_summary(),
                }
            client = ModbusSerialClient(
                method=transport,
                port=self.adapter_data.get("serial_port") or "/dev/ttyUSB0",
                baudrate=int(self.adapter_data.get("baudrate") or 9600),
                parity=self.adapter_data.get("parity") or "N",
                stopbits=int(self.adapter_data.get("stop_bits") or 1),
                timeout=timeout,
            )
            return {
                "ok": True,
                "client": client,
                "details": {
                    **self.capability_summary(),
                    "mode": transport,
                    "serial_port": self.adapter_data.get("serial_port") or "/dev/ttyUSB0",
                    "baudrate": int(self.adapter_data.get("baudrate") or 9600),
                    "parity": self.adapter_data.get("parity") or "N",
                    "stop_bits": int(self.adapter_data.get("stop_bits") or 1),
                    "timeout": timeout,
                },
            }
        return {
            "ok": False,
            "available": self.available(),
            "reason": f"Unsupported transport: {transport}",
            "details": self.capability_summary(),
        }

    def read_registers(self, operation):
        operation = dict(operation or {})
        client_result = self.create_client()
        if not client_result.get("ok"):
            return client_result
        client = client_result["client"]
        if client is None and client_result.get("mock"):
            return {
                "ok": True,
                "mock": True,
                "response": {
                    "operation": "read",
                    "function_code": int(operation.get("function_code") or 3),
                    "register_address": int(operation.get("register_address") or 0),
                    "register_count": int(operation.get("register_count") or 1),
                    "unit_id": int(operation.get("unit_id") or self.adapter_data.get("unit_id") or 1),
                },
                "details": client_result["details"],
            }
        connected = True
        if hasattr(client, "connect"):
            connected = bool(client.connect())
        if not connected:
            return {
                "ok": False,
                "reason": "Unable to connect to Modbus client",
                "details": client_result["details"],
            }
        function_code = int(operation.get("function_code") or 3)
        address = int(operation.get("register_address") or 0)
        count = int(operation.get("register_count") or 1)
        unit = int(operation.get("unit_id") or self.adapter_data.get("unit_id") or 1)
        try:
            if function_code == 1 and hasattr(client, "read_coils"):
                response = client.read_coils(address, count, unit=unit)
            elif function_code == 2 and hasattr(client, "read_discrete_inputs"):
                response = client.read_discrete_inputs(address, count, unit=unit)
            elif function_code == 4 and hasattr(client, "read_input_registers"):
                response = client.read_input_registers(address, count, unit=unit)
            else:
                response = client.read_holding_registers(address, count, unit=unit)
            if hasattr(response, "isError") and response.isError():
                return {
                    "ok": False,
                    "reason": "Modbus response indicated an error",
                    "response": response,
                    "details": client_result["details"],
                }
            return {
                "ok": True,
                "response": response,
                "details": client_result["details"],
            }
        finally:
            if hasattr(client, "close"):
                client.close()

    def write_registers(self, operation):
        operation = dict(operation or {})
        client_result = self.create_client()
        if not client_result.get("ok"):
            return client_result
        client = client_result["client"]
        if client is None and client_result.get("mock"):
            return {
                "ok": True,
                "mock": True,
                "response": {
                    "operation": "write",
                    "function_code": int(operation.get("function_code") or 16),
                    "register_address": int(operation.get("register_address") or 0),
                    "register_count": int(operation.get("register_count") or 1),
                    "unit_id": int(operation.get("unit_id") or self.adapter_data.get("unit_id") or 1),
                    "value": operation.get("value"),
                },
                "details": client_result["details"],
            }
        connected = True
        if hasattr(client, "connect"):
            connected = bool(client.connect())
        if not connected:
            return {
                "ok": False,
                "reason": "Unable to connect to Modbus client",
                "details": client_result["details"],
            }
        function_code = int(operation.get("function_code") or 16)
        address = int(operation.get("register_address") or 0)
        unit = int(operation.get("unit_id") or self.adapter_data.get("unit_id") or 1)
        value = operation.get("value")
        try:
            if function_code == 5 and hasattr(client, "write_coil"):
                response = client.write_coil(address, bool(value), unit=unit)
            elif function_code == 6 and hasattr(client, "write_register"):
                response = client.write_register(address, int(value), unit=unit)
            elif hasattr(client, "write_registers"):
                registers = value if isinstance(value, (list, tuple)) else [value]
                response = client.write_registers(address, list(registers), unit=unit)
            else:
                response = client.write_register(address, int(value), unit=unit)
            if hasattr(response, "isError") and response.isError():
                return {
                    "ok": False,
                    "reason": "Modbus response indicated an error",
                    "response": response,
                    "details": client_result["details"],
                }
            return {
                "ok": True,
                "response": response,
                "details": client_result["details"],
            }
        finally:
            if hasattr(client, "close"):
                client.close()

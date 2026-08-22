import json
import logging
import socket
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class MockEquipmentHandler(BaseHTTPRequestHandler):
    """
    HTTP Request Handler that simulates APC, WTI, and Raritan REST APIs.
    """
    vendor: str = "apc"
    channel_count: int = 8
    outlet_states: Dict[int, int] = {}  # channel -> 1 (ON) or 0 (OFF)

    def log_message(self, format, *args):
        # Suppress standard http.server stdout logging during trials
        pass

    def _send_json(self, status_code: int, data: dict):
        body = json.dumps(data).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_text(self, status_code: int, text: str):
        body = text.encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "text/plain")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = self.path

        # -------------------------------------------------------------
        # APC Mock Endpoints
        # -------------------------------------------------------------
        if self.vendor == "apc":
            if path == "/rest/v1/device":
                return self._send_json(200, {"model": "APC Mock PDU", "status": "operational", "outlets": self.channel_count})
            if path.startswith("/rest/v1/power/outlets/"):
                try:
                    channel = int(path.split("/")[-1])
                    state_int = self.outlet_states.get(channel, 1)
                    state_str = "ON" if state_int == 1 else "OFF"
                    return self._send_json(200, {"outlet": channel, "state": state_str})
                except ValueError:
                    return self._send_json(400, {"error": "Invalid outlet id"})

        # -------------------------------------------------------------
        # WTI Mock Endpoints
        # -------------------------------------------------------------
        elif self.vendor == "wti":
            if path in ("/api/v2/status", "/api/v2/status/"):
                return self._send_json(200, {"model": "WTI Mock PDU", "status": "online", "total_plugs": self.channel_count})
            if path in ("/api/v2/plugs", "/api/v2/plugs/"):
                plugs = [{"id": ch, "status": self.outlet_states.get(ch, 1)} for ch in range(1, self.channel_count + 1)]
                return self._send_json(200, plugs)
            if path.startswith("/api/v2/plugs/"):
                try:
                    channel = int(path.split("/")[-1])
                    status = self.outlet_states.get(channel, 1)
                    return self._send_json(200, {"id": channel, "status": status})
                except ValueError:
                    return self._send_json(400, {"error": "Invalid plug id"})

        # -------------------------------------------------------------
        # Raritan Mock Endpoints
        # -------------------------------------------------------------
        elif self.vendor == "raritan":
            if path in ("/model/pdu/0", "/model/pdu/0/"):
                return self._send_json(200, {"model": "Raritan Mock PDU", "outlets": self.channel_count, "status": "ready"})
            if path.startswith("/model/outlet/"):
                try:
                    idx = int(path.split("/")[-1])
                    channel = idx + 1
                    power_state = self.outlet_states.get(channel, 1)
                    return self._send_json(200, {"outlet": idx, "powerState": power_state})
                except ValueError:
                    return self._send_json(400, {"error": "Invalid outlet index"})

        self._send_text(404, "Endpoint not found")

    def do_PUT(self):
        path = self.path
        content_len = int(self.headers.get('Content-Length', 0))
        post_body = self.rfile.read(content_len).decode('utf-8')
        try:
            payload = json.loads(post_body) if post_body else {}
        except json.JSONDecodeError:
            payload = {}

        # -------------------------------------------------------------
        # APC Mock Endpoints
        # -------------------------------------------------------------
        if self.vendor == "apc":
            if path.startswith("/rest/v1/power/outlets/"):
                try:
                    channel = int(path.split("/")[-1])
                    state = payload.get("state", "ON").upper()
                    self.outlet_states[channel] = 1 if state == "ON" else 0
                    return self._send_json(200, {"outlet": channel, "state": state, "result": "success"})
                except ValueError:
                    return self._send_json(400, {"error": "Invalid outlet id"})

        # -------------------------------------------------------------
        # WTI Mock Endpoints
        # -------------------------------------------------------------
        elif self.vendor == "wti":
            if path.startswith("/api/v2/plugs/"):
                try:
                    channel = int(path.split("/")[-1])
                    action = int(payload.get("action", 1))
                    self.outlet_states[channel] = 1 if action == 1 else 0
                    return self._send_json(200, {"id": channel, "action": action, "status": self.outlet_states[channel]})
                except ValueError:
                    return self._send_json(400, {"error": "Invalid plug id"})

        # -------------------------------------------------------------
        # Raritan Mock Endpoints
        # -------------------------------------------------------------
        elif self.vendor == "raritan":
            if path.startswith("/model/outlet/"):
                try:
                    idx = int(path.split("/")[-1])
                    channel = idx + 1
                    power_state = int(payload.get("powerState", 1))
                    self.outlet_states[channel] = 1 if power_state == 1 else 0
                    return self._send_json(200, {"outlet": idx, "powerState": power_state, "result": "ok"})
                except ValueError:
                    return self._send_json(400, {"error": "Invalid outlet index"})

        self._send_text(404, "Endpoint not found")


class MockPduServer:
    """
    Context manager that starts a local mock HTTP server for APC, WTI, or Raritan PDUs.
    """
    def __init__(self, vendor: str = "apc", channel_count: int = 8, port: int = 0):
        self.vendor = vendor.lower()
        self.channel_count = channel_count
        self.requested_port = port
        self.server: Optional[HTTPServer] = None
        self.thread: Optional[threading.Thread] = None
        self.host = "127.0.0.1"
        self.port = port

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()

    def start(self):
        class CustomHandler(MockEquipmentHandler):
            pass

        CustomHandler.vendor = self.vendor
        CustomHandler.channel_count = self.channel_count
        CustomHandler.outlet_states = {ch: 1 for ch in range(1, self.channel_count + 1)}

        self.server = HTTPServer((self.host, self.requested_port), CustomHandler)
        self.port = self.server.server_port

        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        logger.debug(f"Started Mock {self.vendor.upper()} Server on {self.host}:{self.port}")

    def stop(self):
        if self.server:
            self.server.shutdown()
            self.server.server_close()
            self.server = None
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1.0)
            self.thread = None
        logger.debug("Stopped Mock Server")


# ANSI Color Codes for terminal formatting
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"


def determine_vendor(signature: str, driver_cls) -> str:
    sig = signature.lower()
    name = driver_cls.__name__.lower()
    if "apc" in sig or "apc" in name:
        return "apc"
    elif "wti" in sig or "wti" in name:
        return "wti"
    elif "raritan" in sig or "raritan" in name:
        return "raritan"
    elif "dummy" in sig or "dummy" in name:
        return "dummy"
    return "generic"


def run_pdu_blackbox_trial(sig: str, driver_cls, live_ip: str = None, live_port: int = None, verbose: bool = True) -> bool:
    """
    Executes a complete 9-phase blackbox trial on a PDU model.
    """
    vendor = determine_vendor(sig, driver_cls)
    temp_driver = driver_cls()
    model_name = temp_driver.get_model()
    max_channels = temp_driver.get_max_channel()

    if verbose:
        print(f"\n{BOLD}========================================================================")
        print(f" TRIAL: {model_name}")
        print(f" Signature: {sig} | Vendor Family: {vendor.upper()} | Outlets: {max_channels}")
        print(f"========================================================================{RESET}")

    all_passed = True

    def log_step(step_no: int, description: str, passed: bool, details: str = "", raw: str = ""):
        nonlocal all_passed
        status_str = f"{GREEN}[PASS]{RESET}" if passed else f"{RED}[FAIL]{RESET}"
        if verbose:
            print(f"\n{BOLD}Step {step_no}: {description}{RESET} -> {status_str}")
            if details:
                print(f"  {DIM}{details}{RESET}")
            if raw:
                print(f"  {YELLOW}RAW_OUTPUT:{RESET}\n{DIM}{raw.strip()}{RESET}")
        if not passed:
            all_passed = False

    # Determine execution mode (Mock Simulation vs Live Target)
    if live_ip and live_port:
        target_ip = live_ip
        target_port = live_port
        server_ctx = None
        if verbose:
            print(f"Mode: {YELLOW}LIVE TARGET ({target_ip}:{target_port}){RESET}")
    else:
        if verbose:
            print(f"Mode: {CYAN}SIMULATED BLACKBOX (Local Mock Environment){RESET}")
        server_ctx = MockPduServer(vendor=vendor, channel_count=max_channels)
        server_ctx.start()
        target_ip = server_ctx.host
        target_port = server_ctx.port

    try:
        driver = driver_cls()

        # Step 1: Connect
        try:
            connected = driver.connect(target_ip, target_port)
            log_step(1, f"Connect to {target_ip}:{target_port}", connected, f"Connected status: {driver.connected}")
        except Exception as e:
            log_step(1, f"Connect to {target_ip}:{target_port}", False, f"Exception: {e}")
            return False

        # Step 2: Validate Model and Channel Count Reporting
        detected_model = driver.get_model()
        reported_channels = driver.get_max_channel()
        ch_ok = (reported_channels == max_channels)
        log_step(2, "Query Model & Channel Metadata", ch_ok, f"Model: '{detected_model}', Max Channel: {reported_channels}")

        # Step 3: Check Initial Channel 1 Status
        try:
            resp_init = driver.get_status(1)
            log_step(3, "Query Initial Status for Channel 1", resp_init.success,
                     f"Status: {resp_init.status}, Action: {resp_init.action}, Channel: {resp_init.channel}",
                     raw=resp_init.raw)
        except Exception as e:
            log_step(3, "Query Initial Status for Channel 1", False, f"Exception: {e}")

        # Step 4: Turn ON Channel 1
        try:
            resp_on = driver.turn_on(1)
            log_step(4, "Execute Turn ON for Channel 1", resp_on.success,
                     f"Success: {resp_on.success}, Action: {resp_on.action}",
                     raw=resp_on.raw)
        except Exception as e:
            log_step(4, "Execute Turn ON for Channel 1", False, f"Exception: {e}")

        # Step 5: Verify Status is ON
        try:
            resp_verify_on = driver.get_status(1)
            is_on = (resp_verify_on.status == "ON")
            log_step(5, "Verify Channel 1 State is ON", is_on,
                     f"Current Status: {resp_verify_on.status}",
                     raw=resp_verify_on.raw)
        except Exception as e:
            log_step(5, "Verify Channel 1 State is ON", False, f"Exception: {e}")

        # Step 6: Turn OFF Channel 1
        try:
            resp_off = driver.turn_off(1)
            log_step(6, "Execute Turn OFF for Channel 1", resp_off.success,
                     f"Success: {resp_off.success}, Action: {resp_off.action}",
                     raw=resp_off.raw)
        except Exception as e:
            log_step(6, "Execute Turn OFF for Channel 1", False, f"Exception: {e}")

        # Step 7: Boundary Check: Channel 0 (Must reject with ValueError)
        try:
            driver.turn_on(0)
            log_step(7, "Boundary Check: Channel 0 Rejection", False, "Expected ValueError was NOT raised for Channel 0")
        except ValueError as ve:
            log_step(7, "Boundary Check: Channel 0 Rejection", True, f"Correctly caught usage error: '{ve}'")
        except Exception as e:
            log_step(7, "Boundary Check: Channel 0 Rejection", False, f"Wrong exception type: {type(e).__name__}: {e}")

        # Step 8: Boundary Check: Upper Bound Overflow (Max + 1)
        overflow_ch = max_channels + 1
        try:
            driver.turn_on(overflow_ch)
            log_step(8, f"Boundary Check: Channel {overflow_ch} (> Max {max_channels}) Rejection", False,
                     f"Expected ValueError was NOT raised for Channel {overflow_ch}")
        except ValueError as ve:
            log_step(8, f"Boundary Check: Channel {overflow_ch} (> Max {max_channels}) Rejection", True,
                     f"Correctly caught usage error: '{ve}'")
        except Exception as e:
            log_step(8, f"Boundary Check: Channel {overflow_ch} Rejection", False, f"Wrong exception: {e}")

        # Step 9: Disconnect
        try:
            disconnected = driver.disconnect()
            log_step(9, "Disconnect Session", disconnected, "Clean session shutdown")
        except Exception as e:
            log_step(9, "Disconnect Session", False, f"Exception: {e}")

    finally:
        if server_ctx:
            server_ctx.stop()

    if verbose:
        print(f"\n{BOLD}------------------------------------------------------------------------")
        if all_passed:
            print(f" RESULT: {GREEN}ALL BLACKBOX CHECKS PASSED FOR {model_name.upper()}{RESET}")
        else:
            print(f" RESULT: {RED}ONE OR MORE CHECKS FAILED FOR {model_name.upper()}{RESET}")
        print(f"------------------------------------------------------------------------{RESET}\n")

    return all_passed


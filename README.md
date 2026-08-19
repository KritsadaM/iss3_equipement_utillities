# ISS3 Equipment Utility

Command-line utilities to discover and control ISS3 equipments — PDUs, terminal servers, and DAQs — through a common, pluggable driver architecture. Each utility auto-detects the connected device and dispatches to the right vendor driver, so operators don't need to know which model is on the other end of the IP address.

## Utilities

| Utility                | Equipment type   | Actions                  |
|-------------------------|------------------|---------------------------|
| `iss_pdu_utility`        | PDU              | `on`, `off`, `status`      |
| `iss_terminal_utility`   | Terminal Server  | status dump                |
| `iss_daq_utility`        | DAQ              | `start`, `stop`, `status`  |

## Installation

```bash
pip install -r requirements.txt
```

Or build a `.deb` package (see [Packaging](#packaging) below) and install it on the target host — the utilities land in `/usr/bin`.

## Usage

### PDU

```bash
iss_pdu_utility --ip_address 192.168.1.40 --port 80 on 3
iss_pdu_utility --ip_address 192.168.1.40 --port 80 off 3
iss_pdu_utility --ip_address 192.168.1.40 --port 80 status 3
```

### Terminal Server

```bash
iss_terminal_utility --ip_address 192.168.1.20 --port 22
```

### DAQ

```bash
iss_daq_utility --ip_address 192.168.1.30 --port 502 start
iss_daq_utility --ip_address 192.168.1.30 --port 502 stop
iss_daq_utility --ip_address 192.168.1.30 --port 502 status
```

### Credentials

Some equipment (e.g. the WTI PDU) requires a username/password. Override the default in one of two ways:

```bash
# Flag (visible in shell history / process list -- fine for username, avoid for password)
iss_pdu_utility --ip_address 192.168.1.40 --port 80 --username admin --password secret on 3

# Environment variable (preferred for passwords)
PDU_USERNAME=admin PDU_PASSWORD=secret iss_pdu_utility --ip_address 192.168.1.40 --port 80 on 3
```

Precedence: `--username`/`--password` flag → `PDU_USERNAME`/`PDU_PASSWORD` env var (`TS_*` / `DAQ_*` for the other two utilities) → the driver's own built-in default, if it has one.

## How it works

```
equipment_drivers/
├── interfaces.py         # Abstract base classes every driver implements
├── registry.py           # equipment_type -> signature -> driver class
├── discovery.py          # Finds the right driver for a given ip:port
├── responses.py          # PDUResponse: structured result of a PDU action
├── pdu/
│   ├── dummy_pdu.py
│   ├── apc_models.py
│   ├── wti_models.py
│   └── raritan_models.py
├── terminal_server/
│   └── dummy_ts.py
└── daq/
    └── dummy_daq.py
```

1. **Discovery** (`discover_and_instantiate`) asks every driver registered under the requested equipment type, in turn, "is this you?" via a `probe(ip, port)` classmethod. The first driver to say yes gets instantiated.
2. Drivers registered under the conventional `dummy_{equipment_type}_sig` signature are held back and used only as a last-resort fallback if nothing else matches — useful in dev/test, but something to phase out per equipment type once every real vendor has a working `probe()`.
3. Once a driver is instantiated, the utility calls `connect()`, runs the requested action, and calls `disconnect()`.

### PDU responses

`PDUDriver.turn_on` / `turn_off` / `get_status` return a `PDUResponse` dataclass rather than a bare tuple, so other Python code that imports a driver directly gets full detail:

```python
from equipment_drivers.pdu.wti_models import WtiVmrHd4d20Driver

driver = WtiVmrHd4d20Driver()
driver.connect("192.168.1.40", 80)
response = driver.turn_on(3)
# response.success, response.action, response.channel, response.raw, response.status, response.model
```

## Adding a new driver

1. Create a new file under the right subfolder (`pdu/`, `terminal_server/`, or `daq/`) — it's auto-imported, no need to edit `__init__.py`.
2. Subclass the matching interface (`PDUDriver`, `TerminalServerDriver`, or `DAQDriver`) from `equipment_drivers.interfaces`.
3. Implement `probe(cls, ip, port) -> bool` with real vendor detection (SNMP OID, HTTP banner, etc.) — keep it read-only and fast, and make sure it returns `False` (not an exception) for devices that aren't a match.
4. Register at the bottom of the file:
   ```python
   registry.register('pdu', 'your_vendor_sig', YourDriverClass)
   ```
5. Add tests under `tests/` following the pattern in `test_pdu_wti.py`.

## Testing

```bash
PYTHONPATH=$(pwd) python3 -m unittest discover tests
```

## CI

- **Jenkins** (`Jenkinsfile`) — runs the test suite, then `make release` to build and publish a `.deb` via GitHub CLI.
- **GitHub Actions** (`.github/workflows/python-package.yml`) — installs dependencies, lints with `flake8`, and runs the test suite on every push.

## Packaging

```bash
make deb          # Build the .deb locally
make deb-docker    # Build inside a clean Ubuntu container
make release       # Build and publish a GitHub release (requires `gh` CLI)
```

Installed layout: source under `/opt/iss-equipment-utillities/`, with `iss_pdu_utility`, `iss_terminal_utility`, and `iss_daq_utility` symlinked into `/usr/bin`.

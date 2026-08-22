# ISS3 Equipment Utility

Command-line utilities to discover and control ISS3 equipments — PDUs, terminal servers, and DAQs — through a common, pluggable driver architecture. Each utility auto-detects the connected device and dispatches to the right vendor driver, so operators don't need to know which model is on the other end of the IP address.

## Utilities

| Utility                | Equipment type   | Actions                                      |
|-------------------------|------------------|----------------------------------------------|
| `iss_pdu_utility`        | PDU              | `on`, `off`, `status` (live & `--mock` mode) |
| `iss_trial_utility`      | PDU Diagnostics  | Blackbox trial simulation & raw response inspection |
| `iss_mock_server`        | Equipment Server | Standalone local HTTP simulator for APC/WTI/Raritan |
| `iss_terminal_utility`   | Terminal Server  | status dump                                  |
| `iss_daq_utility`        | DAQ              | `start`, `stop`, `status`                    |

## Installation

```bash
pip install -r requirements.txt
```

Or build a `.deb` package (see [Packaging](#packaging) below) and install it on the target host — the utilities land in `/usr/bin`.

## Usage

### PDU

```bash
# Live hardware:
iss_pdu_utility --ip_address 192.168.1.40 --port 80 on 3
iss_pdu_utility --ip_address 192.168.1.40 --port 80 off 3
iss_pdu_utility --ip_address 192.168.1.40 --port 80 status 3

# Offline Mock Mode (zero hardware required):
iss_pdu_utility --mock --model apc_ap7900 on 1
iss_pdu_utility --mock --model wti_vmr_hd4d20 status 1-3
iss_pdu_utility --mock --model raritan_px3_5460 off 5
```

### Blackbox Trial Tool (Offline Mock Testing)

Run manual or automated blackbox trials against any model to inspect raw JSON/text output and test driver logic without hardware:

```bash
# List all 57+ supported hardware models
iss_trial_utility --list

# Run full 9-phase blackbox trial on a specific model
iss_trial_utility --model apc_ap7900
iss_trial_utility --model wti_vmr_hd4d20
iss_trial_utility --model raritan_px3_5460

# Test specific action on simulated hardware and see RAW_OUTPUT:
iss_trial_utility --model apc_ap7900 --action on --channel 1
iss_trial_utility --model apc_ap7900 --action status --channel 1-3
iss_trial_utility --model wti_vmr_hd4d20 --action off --channel 2

# Trial all models for a specific vendor
iss_trial_utility --vendor apc
iss_trial_utility --vendor wti
iss_trial_utility --vendor raritan

# Trial all 57 models in the entire catalog
iss_trial_utility --all

# Launch interactive menu
iss_trial_utility
```

### Standalone Mock Equipment Server

Start a persistent simulated HTTP server for testing `curl` or external scripts:

```bash
# Run APC mock server on port 8080
iss_mock_server --vendor apc --port 8080

# Run WTI mock server on port 8080
iss_mock_server --vendor wti --port 8080

# Run Raritan mock server on port 8080
iss_mock_server --vendor raritan --port 8080
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

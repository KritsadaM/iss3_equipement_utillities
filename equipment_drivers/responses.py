from dataclasses import dataclass
from typing import Optional


@dataclass
class PDUResponse:
    """
    Full result of a single PDU driver action (turn_on / turn_off / get_status).

    success: whether the action completed without error
    action:  'turn_on' | 'turn_off' | 'get_status'
    channel: the channel the action was performed on
    raw:     the unmodified raw response from the device/API
    status:  parsed status string ('ON' / 'OFF' / etc.), populated for
             get_status and left as None for turn_on/turn_off
    model:   equipment model string; drivers don't set this themselves
             (they don't always know the display name at action time), but
             callers can attach it, e.g. `response.model = driver.get_model()`
    """
    success: bool
    action: str
    channel: int
    raw: str
    status: Optional[str] = None
    model: Optional[str] = None

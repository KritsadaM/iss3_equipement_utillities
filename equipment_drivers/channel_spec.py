from typing import List, Optional


def parse_channels(spec: str, channel_count: Optional[int] = None) -> List[int]:
    """
    Parses a channel spec string into a sorted list of unique channel ints.

    Supported formats:
        "3"             -> [3]
        "3,4,5,6"       -> [3, 4, 5, 6]
        "3, 4, 5, 6"    -> [3, 4, 5, 6]   (whitespace around commas is fine)
        "3-6"           -> [3, 4, 5, 6]
        "1,3-5,8"       -> [1, 3, 4, 5, 8]
        "all"           -> 1..channel_count (case-insensitive: "ALL", "All", etc.)

    Raises ValueError with a descriptive message on any malformed input, or
    if 'all' is given but channel_count wasn't provided by the caller (the
    driver couldn't report how many channels it has).
    """
    spec = spec.strip()

    if spec.lower() == "all":
        if channel_count is None:
            raise ValueError("Channel 'all' requested, but the driver could not report its channel count")
        if channel_count < 1:
            raise ValueError(f"Driver reported an invalid channel count: {channel_count}")
        return list(range(1, channel_count + 1))

    parts = [p.strip() for p in spec.split(",") if p.strip()]
    if not parts:
        raise ValueError(f"Could not parse channel spec: '{spec}'")

    channels = set()
    for part in parts:
        if "-" in part:
            start_str, _, end_str = part.partition("-")
            start_str, end_str = start_str.strip(), end_str.strip()
            if not start_str or not end_str:
                raise ValueError(f"Invalid channel range: '{part}'")
            try:
                start, end = int(start_str), int(end_str)
            except ValueError:
                raise ValueError(f"Invalid channel range: '{part}'")
            if start > end:
                raise ValueError(f"Invalid channel range (start > end): '{part}'")
            channels.update(range(start, end + 1))
        else:
            try:
                channels.add(int(part))
            except ValueError:
                raise ValueError(f"Invalid channel: '{part}'")

    return sorted(channels)

from __future__ import annotations

import re
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any


@dataclass
class ParseResult:
    filament_mm: Optional[float] = None
    filament_g: Optional[float] = None
    time_seconds: Optional[int] = None
    slicer: Optional[str] = None
    source_file: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# Filament patterns (handles common comment formats)
_MM_RE = re.compile(r"filament used\s*\[mm\]\s*=\s*([0-9]*\.?[0-9]+)", re.IGNORECASE)
_G_RE = re.compile(r"filament used\s*\[g\]\s*=\s*([0-9]*\.?[0-9]+)", re.IGNORECASE)

# Cura: ;TIME:7200
_TIME_SECONDS_RE = re.compile(r"^;TIME:\s*([0-9]+)\s*$", re.IGNORECASE)

# Prusa/Bambu/Orca-ish: "; estimated printing time (normal mode) = 17h56m"
_TIME_HUMAN_RE = re.compile(r"estimated printing time.*?=\s*(.+)$", re.IGNORECASE)

# Other variants: "; printing time: 1h 23m"
_TIME_ALT_RE = re.compile(r"(printing time|print time)\s*:\s*(.+)$", re.IGNORECASE)

# Slicer detection (best effort)
_SLICER_HINTS = [
    ("Bambu Studio", re.compile(r"bambu\s*studio", re.IGNORECASE)),
    ("OrcaSlicer", re.compile(r"orcaslicer", re.IGNORECASE)),
    ("PrusaSlicer", re.compile(r"prusaslicer", re.IGNORECASE)),
    ("Cura", re.compile(r"\bcura\b", re.IGNORECASE)),
]


def _detect_slicer(header_blob: str) -> Optional[str]:
    for name, pattern in _SLICER_HINTS:
        if pattern.search(header_blob):
            return name
    return None


def _parse_human_time_to_seconds(text: str) -> Optional[int]:
    """
    Convert strings like:
      "17h56m"
      "17h 56m"
      "1h 2m 3s"
      "45m"
      "30s"
      "01:23:45" or "23:59"
    into total seconds.
    """
    if not text:
        return None

    s = text.strip().lower()
    s = s.replace(" ", "")

    # hh:mm:ss or mm:ss
    if re.match(r"^\d{1,2}:\d{2}(:\d{2})?$", s):
        parts = [int(p) for p in s.split(":")]
        if len(parts) == 2:
            minutes, seconds = parts
            return minutes * 60 + seconds
        hours, minutes, seconds = parts
        return hours * 3600 + minutes * 60 + seconds

    hours = minutes = seconds = 0

    h = re.search(r"(\d+)h", s)
    m = re.search(r"(\d+)m", s)
    sec = re.search(r"(\d+)s", s)

    if not (h or m or sec):
        return None

    if h:
        hours = int(h.group(1))
    if m:
        minutes = int(m.group(1))
    if sec:
        seconds = int(sec.group(1))

    return hours * 3600 + minutes * 60 + seconds


def parse_gcode(file_path: str) -> Dict[str, Any]:
    """
    Parse a G-code file and extract:
      - filament used (mm / g)
      - print time (seconds)
      - slicer name (best effort)
    Returns a dict for easy JSON/CSV/API use.
    """
    result = ParseResult(source_file=file_path)

    header_lines = []
    max_header_lines = 300  # enough to catch metadata without scanning entire file twice

    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        for idx, raw in enumerate(f):
            line = raw.strip()

            if idx < max_header_lines:
                header_lines.append(line)

            # Filament mm
            mm_match = _MM_RE.search(line)
            if mm_match and result.filament_mm is None:
                result.filament_mm = float(mm_match.group(1))

            # Filament g
            g_match = _G_RE.search(line)
            if g_match and result.filament_g is None:
                result.filament_g = float(g_match.group(1))

            # Time seconds (Cura)
            tsec_match = _TIME_SECONDS_RE.match(line)
            if tsec_match and result.time_seconds is None:
                result.time_seconds = int(tsec_match.group(1))

            # Human-readable time formats (Prusa/Bambu etc.)
            if result.time_seconds is None:
                hm = _TIME_HUMAN_RE.search(line)
                if hm:
                    parsed = _parse_human_time_to_seconds(hm.group(1))
                    if parsed is not None:
                        result.time_seconds = parsed

            if result.time_seconds is None:
                alt = _TIME_ALT_RE.search(line)
                if alt:
                    parsed = _parse_human_time_to_seconds(alt.group(2))
                    if parsed is not None:
                        result.time_seconds = parsed

            # Early exit if we’ve found everything (after some header area)
            if (
                result.filament_mm is not None
                and result.filament_g is not None
                and result.time_seconds is not None
                and idx > 250
            ):
                break

    result.slicer = _detect_slicer("\n".join(header_lines))
    return result.to_dict()

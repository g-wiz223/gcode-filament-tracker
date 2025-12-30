from typing import Dict, Optional


def parse_gcode(file_path: str) -> Dict[str, Optional[float]]:
    """
    Parse a G-code file and extract filament usage and print time.

    Returns a dictionary with:
    - filament_mm
    - filament_g
    - time_seconds
    """

    filament_mm = None
    filament_g = None
    time_seconds = None

    with open(file_path, "r", encoding="utf-8", errors="ignore") as file:
        for line in file:
            line = line.strip()

            # Filament used in millimeters
            if "filament used [mm]" in line.lower():
                try:
                    filament_mm = float(line.split("=")[-1].strip())
                except ValueError:
                    pass

            # Filament used in grams
            if "filament used [g]" in line.lower():
                try:
                    filament_g = float(line.split("=")[-1].strip())
                except ValueError:
                    pass

            # Estimated time in seconds (Cura-style)
            if line.startswith(";TIME:"):
                try:
                    time_seconds = float(line.replace(";TIME:", "").strip())
                except ValueError:
                    pass

    return {
        "filament_mm": filament_mm,
        "filament_g": filament_g,
        "time_seconds": time_seconds,
    }

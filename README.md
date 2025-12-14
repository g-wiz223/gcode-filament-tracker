# gcode-filament-tracker
Parse 3D printer G-code to extract filament usage and print time for inventory tracking.

- filament used (mm / grams if density + diameter provided)
- estimated print time (if available in comments)
- metadata (printer/profile hints if present)

This project is designed for automating inventory updates and usage logs (e.g., pushing results into Notion/Sheets/Zoho later).

## Features (current)
- Parse common `;` comment formats (PrusaSlicer / Bambu Studio / Cura-style where possible)
- Extract filament usage from lines like:
  - `; filament used [mm] = ...`
  - `; filament used [g] = ...`
  - `;Filament used: ...`
- Extract time estimates from lines like:
  - `; estimated printing time ...`
  - `;TIME:...`

## Roadmap
- Folder watcher (watchdog) to auto-process new files
- Output JSON/CSV for inventory systems
- Optional Notion API integration

## Quick start

```bash
python -m src.cli "path/to/file.gcode"


# gcode-filament-tracker

Parse 3D printer G-code files to extract filament usage and print time for inventory tracking and usage logging.

This is a backend-style utility: ingest a file → extract reliable metrics → output structured data (JSON/CSV) → optional integration hooks.

## What it extracts
- **filament_mm**: filament used in millimeters (if present in comments)
- **filament_g**: filament used in grams (if present in comments)
- **time_seconds**: estimated print time in seconds (if present in comments)
- **slicer**: best-effort slicer detection (PrusaSlicer / Bambu Studio / OrcaSlicer / Cura)

## Features
- CLI tool for parsing a single `.gcode` file
- Output to **JSON** and/or append rows to **CSV**
- **Watch mode**: monitor a folder and auto-process new `.gcode` files
- Best-effort parsing for common comment formats, including human-readable time (e.g. `17h56m`, `1h 2m 3s`, `01:23:45`)

## Quick start

### Install
```bash
pip install -r requirements.txt

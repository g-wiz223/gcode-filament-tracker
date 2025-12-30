from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Dict, Any, Optional

from src.gcode_parser import parse_gcode


def _sanitize_source_file(file_path: str, mode: str) -> str:
    """
    Avoid leaking internal folder structures in outputs.
    mode:
      - "full": keep full path
      - "name": keep only filename
    """
    p = Path(file_path)
    if mode == "name":
        return p.name
    return str(p)


def write_json(out_path: Path, data: Dict[str, Any]) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def write_csv(out_path: Path, data: Dict[str, Any]) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)

    row = {
        "source_file": data.get("source_file"),
        "slicer": data.get("slicer"),
        "filament_mm": data.get("filament_mm"),
        "filament_g": data.get("filament_g"),
        "time_seconds": data.get("time_seconds"),
    }

    file_exists = out_path.exists()
    with out_path.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(row.keys()))
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)


def process_file(
    file_path: str,
    json_out: Optional[str],
    csv_out: Optional[str],
    notion_db: Optional[str],
    print_output: bool,
    source_mode: str,
) -> Dict[str, Any]:
    parsed = parse_gcode(file_path)

    # sanitize path before output (portfolio safety)
    parsed["source_file"] = _sanitize_source_file(file_path, source_mode)

    if json_out:
        write_json(Path(json_out), parsed)

    if csv_out:
        write_csv(Path(csv_out), parsed)

    # Optional Notion push (portfolio-safe: requires user's own token/db)
    if notion_db:
        from src.notion_client import build_basic_props, create_usage_page

        title = Path(file_path).name
        props = build_basic_props(parsed)
        create_usage_page(database_id=notion_db, title=title, props=props)

    if print_output:
        print(json.dumps(parsed, indent=2))

    return parsed


def run_watch(
    folder: str,
    json_out: Optional[str],
    csv_out: Optional[str],
    notion_db: Optional[str],
    print_output: bool,
    source_mode: str,
) -> None:
    """
    Watch a folder for new .gcode files and process them automatically.
    """
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler

    watch_path = Path(folder).resolve()
    if not watch_path.exists():
        raise FileNotFoundError(f"Watch folder does not exist: {watch_path}")

    class Handler(FileSystemEventHandler):
        def on_created(self, event):
            if event.is_directory:
                return
            if not event.src_path.lower().endswith(".gcode"):
                return

            p = Path(event.src_path)

            # wait until file size stabilizes (prevents parsing half-copied files)
            last_size = -1
            for _ in range(12):
                try:
                    size = p.stat().st_size
                except FileNotFoundError:
                    return
                if size == last_size:
                    break
                last_size = size

            try:
                process_file(str(p), json_out, csv_out, notion_db, print_output, source_mode)
            except Exception as e:
                print(f"[watch] Failed to process {p.name}: {e}")

    print(f"[watch] Watching: {watch_path}")
    observer = Observer()
    observer.schedule(Handler(), str(watch_path), recursive=False)
    observer.start()

    try:
        observer.join()
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Parse G-code for filament usage and print time; export to JSON/CSV and optionally push to Notion."
    )
    parser.add_argument("file", nargs="?", help="Path to a .gcode file")
    parser.add_argument("--json-out", help="Write latest parsed output to a JSON file (e.g. output/latest.json)")
    parser.add_argument("--csv-out", help="Append parsed output as a row to a CSV file (e.g. output/usage.csv)")
    parser.add_argument("--no-print", action="store_true", help="Do not print JSON to console")
    parser.add_argument("--watch", help="Watch a folder for new .gcode files and auto-process")
    parser.add_argument("--notion-db", help="Notion database_id to create a new row/page per processed file")
    parser.add_argument(
        "--source-mode",
        choices=["name", "full"],
        default="name",
        help='How to store source_file in outputs: "name" (safe) or "full" (leaks folder structure). Default: name',
    )

    args = parser.parse_args()
    print_output = not args.no_print

    if args.watch:
        run_watch(args.watch, args.json_out, args.csv_out, args.notion_db, print_output, args.source_mode)
        return

    if not args.file:
        parser.error("Provide a file path or use --watch <folder>")

    process_file(args.file, args.json_out, args.csv_out, args.notion_db, print_output, args.source_mode)


if __name__ == "__main__":
    main()

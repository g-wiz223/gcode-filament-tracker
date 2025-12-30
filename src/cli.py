import sys
import json
from src.gcode_parser import parse_gcode


def main():
    if len(sys.argv) < 2:
        print("Usage: python -m src.cli <path_to_gcode_file>")
        sys.exit(1)

    file_path = sys.argv[1]

    result = parse_gcode(file_path)

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

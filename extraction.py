import sys
import re

START_MARKER = "=== EEPROM DUMP START ==="
END_MARKER   = "=== EEPROM DUMP END ==="

def extract_eeprom(input_path, output_path=None):
    with open(input_path, "r") as f:
        lines = f.readlines()

    sections = []
    header = None
    inside = False
    current = []

    for line in lines:
        stripped = line.strip()

        if stripped == START_MARKER:
            inside = True
            current = []
            continue

        if stripped == END_MARKER:
            inside = False
            if current:
                sections.append(current)
            current = []
            continue

        if inside:
            # Capture the header row (ax,ay,az,gx,gy,gz) once
            if stripped.startswith("ax,"):
                if header is None:
                    header = stripped
                continue
            # Only keep non-empty data lines
            if stripped:
                current.append(stripped)

    if not sections:
        print("No EEPROM dump sections found.", file=sys.stderr)
        sys.exit(1)

    # Build output
    out_lines = []
    if header:
        out_lines.append(header)
    for section in sections:
        out_lines.extend(section)

    output = "\n".join(out_lines) + "\n"

    if output_path:
        with open(output_path, "w") as f:
            f.write(output)
        total_rows = sum(len(s) for s in sections)
        print(f"Extracted {len(sections)} section(s), {total_rows} data rows → {output_path}")
    else:
        print(output, end="")


if __name__ == "__main__":
    input_file  = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) >= 3 else None
    extract_eeprom(input_file, output_file)
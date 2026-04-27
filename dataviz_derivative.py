from __future__ import annotations

import re
from pathlib import Path

import matplotlib.pyplot as plt


CHANNELS = ["ax", "ay", "az", "gx", "gy", "gz"]
DATA_DIRECTORIES = [
	Path("IMU_glasses_data_clean"),
	Path("IMU_necklace_data_clean"),
]
DEFAULT_SAVE_DIR: Path | None = Path("figures_derivative")
SHOW_FIGURES = False


def collect_input_files(data_directories: list[Path]) -> list[Path]:
	input_files: list[Path] = []

	for directory in data_directories:
		if not directory.exists():
			print(f"Skipping missing directory: {directory}")
			continue

		input_files.extend(sorted(directory.glob("*.txt")))

	return input_files


def build_output_dir(base_save_dir: Path, input_file: Path) -> Path:
	return base_save_dir / input_file.parent.name / input_file.stem


def get_next_block_number(save_dir: Path) -> int:
	max_number = 0
	pattern = re.compile(r"^block_(\d{3})\.png$")

	for file_path in save_dir.glob("block_*.png"):
		match = pattern.match(file_path.name)
		if not match:
			continue

		file_number = int(match.group(1))
		if file_number > max_number:
			max_number = file_number

	return max_number + 1


def parse_imu_blocks(file_path: Path) -> list[dict[str, object]]:
	blocks: list[dict[str, object]] = []
	current_rows: list[list[float]] = []
	current_expected: int | None = None

	with file_path.open("r", encoding="utf-8") as f:
		for line_number, raw_line in enumerate(f, start=1):
			line = raw_line.strip()

			if not line:
				continue

			if line.lower() == "ax,ay,az,gx,gy,gz":
				continue

			if line.lower().startswith("samples stored"):
				if current_expected is not None:
					blocks.append({"expected": current_expected, "rows": current_rows})

				current_rows = []
				current_expected = None

				_, _, value = line.partition(":")
				value = value.strip()
				if value:
					try:
						current_expected = int(value)
					except ValueError as exc:
						raise ValueError(
							f"Invalid sample count on line {line_number}: {line}"
						) from exc
				continue

			parts = [p.strip() for p in line.split(",")]
			if len(parts) != 6:
				continue

			try:
				row = [float(v) for v in parts]
			except ValueError:
				continue

			current_rows.append(row)

	if current_expected is not None:
		blocks.append({"expected": current_expected, "rows": current_rows})

	return blocks


def compute_derivative_rows(rows: list[list[float]]) -> list[list[float]]:
	derivative_rows: list[list[float]] = []

	for idx in range(1, len(rows)):
		prev_row = rows[idx - 1]
		curr_row = rows[idx]
		derivative_rows.append(
			[curr_row[channel_idx] - prev_row[channel_idx] for channel_idx in range(6)]
		)

	return derivative_rows


def plot_blocks_derivative(
	blocks: list[dict[str, object]],
	source_name: str,
	show: bool = True,
	save_dir: Path | None = None,
) -> None:
	if not blocks:
		raise ValueError("No 'Samples stored:' blocks found in the input file.")

	next_block_number = 1
	saved_count = 0
	if save_dir is not None:
		save_dir.mkdir(parents=True, exist_ok=True)
		next_block_number = get_next_block_number(save_dir)

	for idx, block in enumerate(blocks, start=1):
		rows = block["rows"]
		expected = block["expected"]

		if not isinstance(rows, list) or len(rows) < 2:
			continue

		derivative_rows = compute_derivative_rows(rows)
		x = list(range(1, len(rows)))

		fig, ax = plt.subplots(figsize=(11, 6))
		for channel_idx, channel_name in enumerate(CHANNELS):
			y = [sample[channel_idx] for sample in derivative_rows]
			ax.plot(x, y, label=channel_name, linewidth=1.4)

		ax.set_xlabel("Sample index")
		ax.set_ylabel("First derivative (delta/sample)")
		ax.set_title(
			f"{source_name} - Block {idx} derivative "
			f"(expected={expected}, actual={len(rows)}, derivative_points={len(derivative_rows)})"
		)
		ax.grid(True, alpha=0.3)
		ax.legend(ncols=3)
		fig.tight_layout()

		if save_dir is not None:
			output_path = save_dir / f"block_{next_block_number:03d}.png"
			fig.savefig(output_path, dpi=160)
			next_block_number += 1
			saved_count += 1

	if show:
		plt.show()
	else:
		plt.close("all")

	if save_dir is None:
		print("Figure saving is disabled because save_dir is None.")
	elif saved_count == 0:
		print(f"No figures were saved to {save_dir.resolve()} (no blocks with 2+ samples).")
	else:
		print(f"Saved {saved_count} figure(s) to {save_dir.resolve()}.")


input_files = collect_input_files(DATA_DIRECTORIES)
if not input_files:
	raise FileNotFoundError(
		"No .txt files found in the configured DATA_DIRECTORIES."
	)

print(f"Found {len(input_files)} input file(s) to process.")

for input_path in input_files:
	print(f"\nProcessing {input_path}...")

	try:
		blocks = parse_imu_blocks(input_path)
	except ValueError as exc:
		print(f"Skipped {input_path}: {exc}")
		continue

	if not blocks:
		print(f"Skipped {input_path}: no 'Samples stored:' blocks found.")
		continue

	output_dir = None
	if DEFAULT_SAVE_DIR is not None:
		output_dir = build_output_dir(DEFAULT_SAVE_DIR, input_path)

	plot_blocks_derivative(
		blocks=blocks,
		source_name=input_path.name,
		show=SHOW_FIGURES,
		save_dir=output_dir,
	)

	print(f"Parsed {len(blocks)} block(s) from {input_path}.")

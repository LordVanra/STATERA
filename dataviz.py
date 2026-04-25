from __future__ import annotations

import re
from pathlib import Path

import matplotlib.pyplot as plt


CHANNELS = ["ax", "ay", "az", "gx", "gy", "gz"]
DEFAULT_SAVE_DIR: Path | None = None

input_path = Path("IMU_necklace_data_clean/arnavwalk.txt")


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

			# Ignore CSV header lines (including the first line).
			if line.lower() == "ax,ay,az,gx,gy,gz":
				continue

			if line.lower().startswith("samples stored"):
				# Close previous block before starting a new one.
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

			# Parse sensor sample lines.
			parts = [p.strip() for p in line.split(",")]
			if len(parts) != 6:
				continue

			try:
				row = [float(v) for v in parts]
			except ValueError:
				continue

			current_rows.append(row)

	# Add the final block if one was open.
	if current_expected is not None:
		blocks.append({"expected": current_expected, "rows": current_rows})

	return blocks


def plot_blocks(
	blocks: list[dict[str, object]],
	source_name: str,
	show: bool = True,
	save_dir: Path | None = None,
) -> None:
	if not blocks:
		raise ValueError("No 'Samples stored:' blocks found in the input file.")

	next_block_number = 1
	if save_dir is not None:
		save_dir.mkdir(parents=True, exist_ok=True)
		next_block_number = get_next_block_number(save_dir)

	for idx, block in enumerate(blocks, start=1):
		rows = block["rows"]
		expected = block["expected"]

		if not isinstance(rows, list) or not rows:
			continue

		x = list(range(len(rows)))

		fig, ax = plt.subplots(figsize=(11, 6))
		for channel_idx, channel_name in enumerate(CHANNELS):
			y = [sample[channel_idx] for sample in rows]
			ax.plot(x, y, label=channel_name, linewidth=1.4)

		ax.set_xlabel("Sample index")
		ax.set_ylabel("Sensor value")
		ax.set_title(
			f"{source_name} - Block {idx} "
			f"(expected={expected}, actual={len(rows)})"
		)
		ax.grid(True, alpha=0.3)
		ax.legend(ncols=3)
		fig.tight_layout()

		if save_dir is not None:
			output_path = save_dir / f"block_{next_block_number:03d}.png"
			fig.savefig(output_path, dpi=160)
			next_block_number += 1

	if show:
		plt.show()
	else:
		plt.close("all")

blocks = parse_imu_blocks(input_path)
output_dir = DEFAULT_SAVE_DIR

plot_blocks(
    blocks=blocks,
    source_name=input_path.name,
    save_dir=output_dir,
)

print(f"Parsed {len(blocks)} block(s) from {input_path}.")
for i, block in enumerate(blocks, start=1):
    print(
        f"  Block {i}: expected={block['expected']} "
        f"actual={len(block['rows'])}"
    )


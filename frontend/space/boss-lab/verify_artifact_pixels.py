"""Reject detached white bloom blocks around the embedded Boss render."""

from pathlib import Path
import sys

import numpy as np
from PIL import Image


image_path = Path(sys.argv[1])
image = np.asarray(Image.open(image_path).convert("RGB"))
height, width, _ = image.shape

regions = {
    "lower": image[int(0.66 * height):int(0.92 * height), int(0.64 * width):int(0.80 * width)],
    "right": image[int(0.50 * height):int(0.82 * height), int(0.78 * width):int(0.91 * width)],
}
limits = {"lower": 800, "right": 300}

failures = []
for name, region in regions.items():
    channel_min = region.min(axis=2)
    channel_range = region.max(axis=2) - channel_min
    detached_white_pixels = int(((channel_min > 235) & (channel_range < 18)).sum())
    print(f"{name}: {detached_white_pixels} detached white pixels")
    if detached_white_pixels > limits[name]:
        failures.append(f"{name}={detached_white_pixels}>{limits[name]}")

if failures:
    raise SystemExit("Boss bloom artifact detected: " + ", ".join(failures))

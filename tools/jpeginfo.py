#!/usr/bin/env python3
"""Read JPEG width/height/components from the SOF marker. No dependencies.

Needed because the sandbox has no image library at all (no PIL, no ImageMagick),
yet a PDF image XObject must declare /Width, /Height and /ColorSpace.
JPEG bytes are embedded verbatim with the DCTDecode filter, so nothing is
re-encoded and no decoder is required.
"""
import struct
import sys
from pathlib import Path

SOF_MARKERS = {
    0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7,
    0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF,
}


def jpeg_info(path):
    data = Path(path).read_bytes()
    if data[0:2] != b"\xff\xd8":
        raise ValueError(f"{path}: not a JPEG (no SOI)")
    i = 2
    n = len(data)
    while i < n:
        # markers may be padded with any number of 0xFF fill bytes
        if data[i] != 0xFF:
            i += 1
            continue
        while i < n and data[i] == 0xFF:
            i += 1
        if i >= n:
            break
        marker = data[i]
        i += 1
        if marker in (0xD8, 0x01) or 0xD0 <= marker <= 0xD7:
            continue
        if marker == 0xD9:  # EOI
            break
        if i + 2 > n:
            break
        seglen = struct.unpack(">H", data[i:i + 2])[0]
        if marker in SOF_MARKERS:
            if i + 8 > n:
                raise ValueError(f"{path}: truncated SOF")
            precision = data[i + 2]
            height = struct.unpack(">H", data[i + 3:i + 5])[0]
            width = struct.unpack(">H", data[i + 5:i + 7])[0]
            comps = data[i + 7]
            progressive = marker == 0xC2
            return {
                "path": str(path),
                "width": width,
                "height": height,
                "components": comps,
                "bits": precision,
                "progressive": progressive,
                "bytes": n,
            }
        i += seglen
    raise ValueError(f"{path}: no SOF marker found")


if __name__ == "__main__":
    targets = sys.argv[1:] or sorted(
        str(p) for p in Path("assets/elevations").glob("*.jpeg")
    )
    for t in targets:
        info = jpeg_info(t)
        print(
            f"{Path(info['path']).name:18s} {info['width']:5d}x{info['height']:5d} "
            f"comps={info['components']} bits={info['bits']} "
            f"prog={info['progressive']} {info['bytes'] / 1024:7.1f}KB "
            f"aspect={info['width'] / info['height']:.3f}"
        )

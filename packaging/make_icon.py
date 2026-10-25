"""Draw the game icon (a pixel-art acorn) as packaging/acorn.ico, with no extra libraries.

The .ico holds PNG images, which Windows Vista and later read directly.
"""

import struct
import zlib
from pathlib import Path

ART = """
................
.......BB.......
......BB........
...CCCCCCCCCC...
..CCcCCcCCcCCC..
..CCCCCCCCCCCC..
...CCCCCCCCCC...
...GGGGGGGGGG...
...GgGGGGGGGG...
...GgGGGGGGGG...
....GgGGGGGG....
....GGGGGGGG....
.....GGGGGG.....
......GGGG......
.......GG.......
................
"""
COLORS = {
    ".": (0, 0, 0, 0),
    "B": (90, 55, 25, 255),  # stem
    "C": (122, 82, 48, 255),  # cap
    "c": (160, 115, 70, 255),  # cap dots
    "G": (232, 184, 74, 255),  # nut
    "g": (255, 224, 140, 255),  # shine
}


def png(size: int) -> bytes:
    rows = [line for line in ART.strip("\n").splitlines()]
    scale = size // len(rows)
    raw = bytearray()
    for y in range(size):
        raw.append(0)  # no filter
        for x in range(size):
            raw += bytes(COLORS[rows[y // scale][x // scale]])

    def chunk(kind: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data))

    header = struct.pack(">IIBBBBB", size, size, 8, 6, 0, 0, 0)
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header) + chunk(b"IDAT", zlib.compress(bytes(raw), 9)) + chunk(b"IEND", b"")


def ico(sizes=(16, 32, 48, 64, 128, 256)) -> bytes:
    images = [png(s) for s in sizes]
    out = struct.pack("<HHH", 0, 1, len(images))
    offset = 6 + 16 * len(images)
    for size, data in zip(sizes, images):
        out += struct.pack("<BBBBHHII", size % 256, size % 256, 0, 0, 1, 32, len(data), offset)
        offset += len(data)
    return out + b"".join(images)


if __name__ == "__main__":
    target = Path(__file__).with_name("acorn.ico")
    target.write_bytes(ico())
    print(f"wrote {target}")

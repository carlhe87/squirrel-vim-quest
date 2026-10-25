"""Everything drawn on screen: cell sprites, key caps, big pictures.

No emoji: only ASCII plus a few box-drawing and arrow characters that
Windows Terminal's default font draws one cell wide. A grid cell is drawn
4 characters wide and 2 lines tall, which looks roughly square.
"""

from __future__ import annotations

from rich.text import Text

CELL_W = 4
CELL_H = 2

GRASS_BG = "#1d3b1d"
BACKGROUND = "#0f2416"

KEY_COLORS = {
    "h": "#4da6ff", "j": "#4dd96b", "k": "#ffd84d", "l": "#ff5c5c",
    "w": "#b07cff", "b": "#4de0e0", "e": "#ff66cc",
    "0": "#e6e6e6", "$": "#ff9a3c",
}
KEY_ARROWS = {"h": "←", "j": "↓", "k": "↑", "l": "→", "w": "»", "b": "«", "e": "›", "0": "<", "$": ">"}
ARROW_TO_KEY = {"left": "h", "down": "j", "up": "k", "right": "l"}

# name -> (two lines of 4 chars, style)
SPRITES: dict[str, tuple[tuple[str, str], str]] = {
    "grass": (("    ", "    "), f"#3f6f3f on {GRASS_BG}"),
    "grass_dots": ((" .  ", "   ."), f"#3f6f3f on {GRASS_BG}"),
    "rock": (("▓▓▓▓", "▓▓▓▓"), "#9a9a9a on #4a4a4a"),
    "pip": (("(oo)", '(")~'), "bold #1a1a1a on #ff8c1a"),
    "pip_glow": (("(^^)", '(")~'), "bold #1a1a1a on #ffe066"),
    "pip_hurt": (("(><)", '(")~'), "bold #1a1a1a on #ff5c5c"),
    "ghost": (("(oo)", '(")~'), f"#c98a52 on {GRASS_BG}"),
    "acorn": (("(==)", " \\/ "), f"bold #e8b84a on {GRASS_BG}"),
    "acorn_fading": (("(==)", " \\/ "), f"#8a6e30 on {GRASS_BG}"),
    "snail": ((" __ ", "(@)_"), f"bold #ff8080 on {GRASS_BG}"),
    "fox": (("/\\/\\", "(><)"), "bold #1a1a1a on #e2572b"),
    "gate_closed": (("|##|", "|##|"), "bold #d8b074 on #6b4a2a"),
    "gate_open": (("|>>|", "|  |"), f"bold #6dff8a on {GRASS_BG}"),
}


def grass_for(r: int, c: int) -> str:
    return "grass_dots" if (r * 3 + c) % 5 == 0 else "grass"


def render_cells(cells: list[list[str]]) -> Text:
    """Draw a 2D list of sprite names."""
    lines = []
    for row in cells:
        for half in range(CELL_H):
            line = Text()
            for name in row:
                chars, style = SPRITES[name]
                line.append(chars[half], style=style)
            lines.append(line)
    return Text("\n").join(lines)


def side_by_side(blocks: list[Text], gap: int = 2) -> Text:
    """Put multi-line pictures next to each other, tops aligned."""
    split = [b.split("\n", allow_blank=True) for b in blocks]
    widths = [max((ln.cell_len for ln in lines), default=0) for lines in split]
    height = max(len(lines) for lines in split)
    out = []
    for i in range(height):
        line = Text()
        for j, lines in enumerate(split):
            part = lines[i] if i < len(lines) else Text()
            line.append_text(part)
            pad = widths[j] - part.cell_len + (gap if j < len(split) - 1 else 0)
            line.append(" " * pad)
        out.append(line)
    return Text("\n").join(out)


def key_cap(key: str, dim: bool = False) -> Text:
    """A small key with its arrow in the bottom edge, 3 lines tall."""
    color = "#555555" if dim else KEY_COLORS.get(key, "#dddddd")
    arrow = KEY_ARROWS.get(key, "─")
    style = f"bold {color}"
    return Text("\n").join([
        Text("╭───╮", style=style),
        Text(f"│ {key} │", style=style),
        Text(f"╰─{arrow}─╯", style=style),
    ])


def big_key(key: str) -> Text:
    """The big key used to introduce a key, 5 lines tall."""
    color = KEY_COLORS.get(key, "#dddddd")
    frame = f"bold {color}"
    face = f"bold #101010 on {color}"
    arrow = KEY_ARROWS.get(key, " ")
    lines = [
        Text("┌───────┐", style=frame),
        Text("│", style=frame) + Text("       ", style=face) + Text("│", style=frame),
        Text("│", style=frame) + Text(f"   {key}   ", style=face) + Text("│", style=frame),
        Text("│", style=frame) + Text(f"   {arrow}   ", style=face) + Text("│", style=frame),
        Text("└───────┘", style=frame),
    ]
    return Text("\n").join(lines)


KEYBOARD_ROWS = ["1234567890", "qwertyuiop", "asdfghjkl;", "zxcvbnm,./"]
SHIFTED = {"$": "4"}  # keys typed with shift, and the key they sit on

# Touch typing: which hand and finger presses each key, by column.
_FINGER_BY_COLUMN = [
    "left little", "left ring", "left middle", "left index", "left index",
    "right index", "right index", "right middle", "right ring", "right little",
]


def finger_for(key: str) -> str | None:
    base = SHIFTED.get(key, key)
    for row in KEYBOARD_ROWS:
        if base in row:
            finger = _FINGER_BY_COLUMN[row.index(base)] + " finger"
            return f"shift + {finger}" if key in SHIFTED else finger
    return None


def keyboard(active: str) -> Text:
    """The keyboard rows, staggered like a real one, with the active key lit.

    A shifted key like $ lights the key it sits on (4), drawn as $.
    The finger line is for the grown-up helping; the child follows the light.
    """
    base = SHIFTED.get(active, active)
    lines = []
    for i, row in enumerate(KEYBOARD_ROWS):
        line = Text(" " * i)
        for k in row:
            if k == base:
                line.append(f"[{active}]", style=f"bold #101010 on {KEY_COLORS.get(active, '#ffffff')}")
            elif k in KEY_COLORS:
                line.append(f"[{k}]", style=KEY_COLORS[k])
            else:
                line.append(f"[{k}]", style="#555555")
        lines.append(line)
    lines.append(Text(finger_for(active) or "", style="#888888"))
    return Text("\n").join(lines)


def stars(n: int, of: int = 3) -> Text:
    """Big stars, 3 lines tall: yellow when earned, gray when not."""
    shape = ("__/\\__", "\\    /", "/_/\\_\\")
    blocks = []
    for i in range(of):
        style = "bold #ffd84d" if i < n else "#4a4a4a"
        blocks.append(Text("\n").join(Text(line, style=style) for line in shape))
    return side_by_side(blocks, gap=3)


def small_stars(n: int, of: int = 3) -> Text:
    return Text("*" * n, style="bold #ffd84d") + Text("." * (of - n), style="#555555")


PIP_ART = r"""
    .--.
   /    \       __
  |  .-. \    /o  \_
  |  \  \ \__/     ._>
   \  '-'  /   ___/
    '-.__.'   (__)(__)
""".strip("\n")


def pip_art() -> Text:
    return Text(PIP_ART, style="bold #ff8c1a")


def center_stack(blocks: list[Text]) -> Text:
    """Stack pictures vertically, each centred as a whole (art keeps its shape)."""
    split = [b.split("\n", allow_blank=True) for b in blocks]
    width = max(ln.cell_len for lines in split for ln in lines)
    out = []
    for lines in split:
        block_w = max(ln.cell_len for ln in lines)
        left = (width - block_w) // 2
        for ln in lines:
            out.append(Text(" " * left) + ln + Text(" " * (width - left - ln.cell_len)))
    return Text("\n").join(out)

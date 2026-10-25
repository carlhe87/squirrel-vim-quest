"""Make the itch.io page images from the real game, into dist/itch/:

  screen-1-title.png ... screen-7-stars.png   1280 px wide screenshots
  cover.png                                   630 x 500, the itch.io cover image
  banner.png                                  960 x 240, the page header

The game runs headless (Textual's pilot) and saves each screen as SVG; a
headless Edge or Chrome turns the SVGs and two small HTML pages into PNGs.
Run:  .venv\\Scripts\\python packaging\\itch_assets.py
"""

from __future__ import annotations

import asyncio
import html
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "dist" / "itch"
sys.path.insert(0, str(ROOT))

BROWSERS = [
    Path(os.environ.get("ProgramFiles(x86)", "")) / "Microsoft/Edge/Application/msedge.exe",
    Path(os.environ.get("ProgramFiles", "")) / "Microsoft/Edge/Application/msedge.exe",
    Path(os.environ.get("ProgramFiles", "")) / "Google/Chrome/Application/chrome.exe",
]
SCREEN_WIDTH = 1280


def find_browser() -> Path:
    for path in BROWSERS:
        if path.exists():
            return path
    sys.exit("Need Microsoft Edge or Google Chrome to render the PNGs.")


async def capture_svgs(folder: Path) -> list[Path]:
    """Play through the game headless and save one SVG per interesting screen."""
    os.environ["SVQ_MUTE"] = "1"
    os.environ["SVQ_DATA_DIR"] = tempfile.mkdtemp()
    os.environ.pop("NO_COLOR", None)  # as main() does: the screenshots must be in color
    os.environ["COLORTERM"] = "truecolor"
    from squirrel_vim_quest.app import SquirrelApp
    from squirrel_vim_quest.levels import load_level

    shots = []

    def shot(app, name: str) -> None:
        app.save_screenshot(f"{name}.svg", str(folder))
        shots.append(folder / f"{name}.svg")

    def seeded(island: str, stone: int, **settings):
        level = load_level(island, stone)
        level.settings = {**level.settings, **settings}
        return level

    app = SquirrelApp()
    async with app.run_test(size=(120, 30)) as pilot:
        await pilot.pause(0.5)
        shot(app, "screen-1-title")

        for n in range(1, 6):
            app.save.record(f"island1/stone{n}", 3, 3)
        app.save.record("island2/stone1", 3, 0)
        app.save.record("island2/stone2", 2, 0)
        await pilot.press("enter")
        await pilot.pause(0.2)
        await pilot.press("j")
        await pilot.pause(0.2)
        shot(app, "screen-2-map")

        app.start_level(load_level("island1", 5))
        await pilot.pause(2.6)
        shot(app, "screen-3-fox-maze")
        app.pop_screen()

        app.start_level(load_level("island2", 1))
        await pilot.pause(1.0)
        shot(app, "screen-4-meet-w")
        app.pop_screen()

        app.start_level(seeded("island2", 3, seed=4))
        await pilot.pause(4.5)
        await pilot.press("w")
        await pilot.pause(2.6)
        shot(app, "screen-5-frog-river")
        app.pop_screen()

        app.start_level(seeded("island3", 5, seed=1, gust_every=2.5))
        await pilot.pause(4.6)
        shot(app, "screen-6-storm-bridge")
        app.screen.finish(3, 8)
        await pilot.pause(0.4)
        shot(app, "screen-7-stars")
    return shots


def render(browser: Path, page: Path, png: Path, width: int, height: int) -> None:
    subprocess.run(
        [
            str(browser), "--headless=new", "--disable-gpu", "--hide-scrollbars",
            f"--window-size={width},{height}", f"--screenshot={png}", page.as_uri(),
        ],
        check=True,
        timeout=90,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def svg_page(svg: Path) -> tuple[str, int]:
    """An HTML page showing the SVG 1280 px wide, and the height it needs."""
    match = re.search(r'viewBox="0 0 ([\d.]+) ([\d.]+)"', svg.read_text(encoding="utf-8"))
    w, h = float(match.group(1)), float(match.group(2))
    height = round(SCREEN_WIDTH * h / w)
    page = (
        "<html><body style='margin:0;background:#0f2416'>"
        f"<img src='{svg.name}' style='width:{SCREEN_WIDTH}px;display:block'></body></html>"
    )
    return page, height


def key_caps() -> str:
    from squirrel_vim_quest.sprites import KEY_COLORS

    caps = []
    for key in "hjklwbe0$":
        color = KEY_COLORS[key]
        caps.append(
            f"<span style='display:inline-block;min-width:22px;padding:4px 7px;margin:0 3px;"
            f"border:2px solid {color};border-radius:7px;color:{color};font-weight:bold;"
            f"text-align:center'>{html.escape(key)}</span>"
        )
    return "".join(caps)


def art_pages() -> dict[str, tuple[str, int, int]]:
    from squirrel_vim_quest.sprites import PIP_ART

    pip = html.escape(PIP_ART)
    font = "font-family:'Cascadia Mono','Cascadia Code',Consolas,monospace"
    base = f"margin:0;background:#0f2416;{font};overflow:hidden"
    title = "color:#ffd84d;font-weight:bold;letter-spacing:2px"
    cover = f"""<html><body style="{base};width:630px;height:500px;display:flex;flex-direction:column;
        align-items:center;justify-content:center">
      <pre style="color:#ff8c1a;font-size:21px;font-weight:bold;line-height:1.12;margin:0">{pip}</pre>
      <div style="{title};font-size:38px;margin-top:26px">SQUIRREL VIM QUEST</div>
      <div style="color:#dddddd;font-size:18px;margin-top:10px">Learn Vim keys with Pip the squirrel</div>
      <div style="font-size:18px;margin-top:22px">{key_caps()}</div>
      <div style="color:#8aa88a;font-size:14px;margin-top:20px">for kids 6+ &middot; read aloud &middot; Windows</div>
    </body></html>"""
    banner = f"""<html><body style="{base};width:960px;height:240px;display:flex;align-items:center;
        justify-content:center;gap:48px">
      <pre style="color:#ff8c1a;font-size:19px;font-weight:bold;line-height:1.1;margin:0">{pip}</pre>
      <div>
        <div style="{title};font-size:42px">SQUIRREL VIM QUEST</div>
        <div style="color:#dddddd;font-size:18px;margin:10px 0 18px">Learn Vim keys with Pip the squirrel</div>
        <div style="font-size:18px">{key_caps()}</div>
      </div>
    </body></html>"""
    return {"cover": (cover, 630, 500), "banner": (banner, 960, 240)}


def main() -> None:
    browser = find_browser()
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp)
        for svg in asyncio.run(capture_svgs(work)):
            page, height = svg_page(svg)
            page_file = work / f"{svg.stem}.html"
            page_file.write_text(page, encoding="utf-8")
            render(browser, page_file, OUT / f"{svg.stem}.png", SCREEN_WIDTH, height)
            print(f"  {svg.stem}.png")
        for name, (page, width, height) in art_pages().items():
            page_file = work / f"{name}.html"
            page_file.write_text(page, encoding="utf-8")
            render(browser, page_file, OUT / f"{name}.png", width, height)
            print(f"  {name}.png")
    print(f"Done: {OUT}")


if __name__ == "__main__":
    main()

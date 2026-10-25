"""World map: Pip walks between level stones with h j k l. Enter plays."""

from __future__ import annotations

from rich.text import Text

from ..levels import ISLANDS, STONES_PER_ISLAND, load_island
from ..sprites import SPRITES, small_stars
from ..strings import t
from .base import GameScreen

SLOT = 6  # width of one stone on the map
LINK = "--"


class MapScreen(GameScreen):
    def start(self) -> None:
        self.islands = {i.id: load_island(i.id) for i in ISLANDS if i.ready}
        self.island_i = 0
        self.stone_i = self._next_stone()
        self.say("pick_stone")

    def on_screen_resume(self) -> None:
        self.stone_i = self._next_stone()
        self.redraw()

    # -- progress ------------------------------------------------------

    def _stars(self, island_i: int, stone_i: int) -> int:
        island = ISLANDS[island_i]
        return self.app.save.stars_for(f"{island.id}/stone{stone_i + 1}")

    def _unlocked(self, island_i: int, stone_i: int) -> bool:
        if not ISLANDS[island_i].ready:
            return False
        if island_i > 0 and not self._stars(island_i - 1, STONES_PER_ISLAND - 1):
            return False
        return stone_i == 0 or self._stars(island_i, stone_i - 1) > 0

    def _next_stone(self) -> int:
        """The first stone not yet played, so a returning child starts there."""
        for i in range(STONES_PER_ISLAND):
            if self._unlocked(self.island_i, i) and not self._stars(self.island_i, i):
                return i
        return STONES_PER_ISLAND - 1 if self._unlocked(self.island_i, STONES_PER_ISLAND - 1) else 0

    # -- input ---------------------------------------------------------

    def on_motion(self, key: str) -> None:
        if key in "hl":
            step = -1 if key == "h" else 1
            target = self.stone_i + step
            if 0 <= target < STONES_PER_ISLAND and self._unlocked(self.island_i, target):
                self.stone_i = target
                self.audio.play("hop")
            else:
                self._blocked()
        else:
            target = self.island_i + (1 if key == "j" else -1)
            if 0 <= target < len(ISLANDS) and self._unlocked(target, 0):
                self.island_i = target
                self.stone_i = self._next_stone()
                self.audio.play("hop")
            elif 0 <= target < len(ISLANDS) and not ISLANDS[target].ready:
                self._blocked("coming_soon")
            else:
                self._blocked()

    def _blocked(self, line: str = "not_yet") -> None:
        self.shake()
        self.audio.play("wrong")
        self.say(line)

    def on_enter(self) -> None:
        island = ISLANDS[self.island_i]
        if self._unlocked(self.island_i, self.stone_i):
            self.app.start_level(self.islands[island.id][self.stone_i])

    def hint_key(self) -> str | None:
        if self.stone_i + 1 < STONES_PER_ISLAND and self._unlocked(self.island_i, self.stone_i + 1):
            return "l"
        return "h" if self.stone_i > 0 else None

    # -- drawing -------------------------------------------------------

    def render_status(self) -> Text:
        acorns = self.app.save.total_acorns()
        return Text(t("title").upper(), style="bold #ffd84d") + Text("        (=) ", style="bold #e8b84a") + Text(
            f"x {acorns}", style="bold #e8b84a"
        )

    def render_play(self) -> Text:
        lines: list[Text] = []
        water = Text("~" * (SLOT * STONES_PER_ISLAND + len(LINK) * (STONES_PER_ISLAND - 1) + 8), style="#2f6fa8")
        lines.append(water)
        for i, island in enumerate(ISLANDS):
            ready = self._unlocked(i, 0)
            lines.append(Text(""))
            name_style = "bold #ffffff" if ready else "#555555"
            name = Text("    " + t(island.name_key).upper(), style=name_style)
            if not island.ready:
                name.append("   " + t("coming_soon").upper(), style="bold #2f6fa8")
            lines.append(name)
            pip_top, pip_bottom = Text("    "), Text("    ")
            stones, stars = Text("    "), Text("    ")
            for s in range(STONES_PER_ISLAND):
                here = i == self.island_i and s == self.stone_i
                if here:
                    chars, style = SPRITES["pip"]
                    for line, half in ((pip_top, chars[0]), (pip_bottom, chars[1])):
                        line.append(" ")
                        line.append(half, style=style)
                        line.append(" ")
                else:
                    pip_top.append(" " * SLOT)
                    pip_bottom.append(" " * SLOT)
                if s < STONES_PER_ISLAND - 1:
                    pip_top.append(" " * len(LINK))
                    pip_bottom.append(" " * len(LINK))

                label = "(BOSS)" if s == STONES_PER_ISLAND - 1 else f"( {s + 1} )".ljust(SLOT)
                got = self._stars(i, s) if island.ready else 0
                if not self._unlocked(i, s):
                    style = "#555555"
                    if not island.ready:
                        label = "(BOSS)" if s == STONES_PER_ISLAND - 1 else "( - ) "
                elif got:
                    style = "bold #e8b84a"
                else:
                    style = "bold #ffffff"
                if here:
                    style = "bold #101010 on #ffd84d"
                stones.append(label, style=style)
                stars.append(" ")
                stars.append_text(small_stars(got) if self._unlocked(i, s) else Text("   "))
                stars.append("  ")
                if s < STONES_PER_ISLAND - 1:
                    stones.append(LINK, style="#8a6e30" if ready else "#333333")
                    stars.append(" " * len(LINK))
            if i == self.island_i:
                lines += [pip_top, pip_bottom]
            else:
                lines += [Text(""), Text("")]
            lines += [stones, stars]
        lines.append(Text(""))
        lines.append(water.copy())
        return Text("\n").join(lines)

    def render_keybar(self) -> Text:
        bar = super().render_keybar()
        return bar + Text("\n") + Text("Enter: play", style="bold #4dd96b")

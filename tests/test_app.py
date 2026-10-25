"""Drive the real app headless with Textual's pilot."""

import pytest

from squirrel_vim_quest.app import SquirrelApp
from squirrel_vim_quest.levels import load_level
from squirrel_vim_quest.screens import meet
from squirrel_vim_quest.screens.garden import GardenScreen
from squirrel_vim_quest.screens.map import MapScreen
from squirrel_vim_quest.screens.maze import MazeScreen
from squirrel_vim_quest.screens.pause import PauseScreen
from squirrel_vim_quest.screens.pong import PongScreen
from squirrel_vim_quest.screens.puzzle import PuzzleScreen
from squirrel_vim_quest.screens.rapids import RapidsScreen
from squirrel_vim_quest.screens.results import ResultsScreen
from squirrel_vim_quest.screens.river import RiverScreen
from squirrel_vim_quest.screens.storm import StormScreen

SIZE = (120, 30)


@pytest.fixture(autouse=True)
def quiet(monkeypatch, tmp_path):
    monkeypatch.setenv("SVQ_MUTE", "1")
    monkeypatch.setenv("SVQ_DATA_DIR", str(tmp_path))


async def wait_for(pilot, check, seconds=10.0):
    for _ in range(int(seconds / 0.05)):
        if check():
            return
        await pilot.pause(0.05)
    raise AssertionError("timed out")


async def test_title_to_map_and_locked_stone():
    app = SquirrelApp()
    async with app.run_test(size=SIZE) as pilot:
        await pilot.press("enter")
        assert isinstance(app.screen, MapScreen)
        await pilot.press("l")  # stone 2 is locked until stone 1 is played
        assert app.screen.stone_i == 0
        assert app.audio.last_line == "Not yet!"
        await pilot.press("j")  # Word River opens after the Fox Maze
        assert app.screen.island_i == 0
        assert app.audio.last_line == "Not yet!"


async def test_word_river_opens_after_island1_boss():
    app = SquirrelApp()
    async with app.run_test(size=SIZE) as pilot:
        app.save.record("island1/stone5", 2, 4)
        await pilot.press("enter")
        await pilot.press("j")
        assert app.screen.island_i == 1 and app.screen.stone_i == 0
        await pilot.press("j")  # Line Bridge opens after the Fish Rapids
        assert app.screen.island_i == 1
        assert app.audio.last_line == "Not yet!"
        await pilot.press("enter")
        assert app.screen.level.id == "island2/stone1"


def test_main_ignores_no_color(monkeypatch):
    import squirrel_vim_quest.app as app_module

    monkeypatch.setenv("NO_COLOR", "1")
    monkeypatch.setattr(app_module.SquirrelApp, "run", lambda self: None)
    app_module.main(["--no-wt"])
    import os

    assert "NO_COLOR" not in os.environ


def test_exe_relaunch_starts_a_fresh_copy(monkeypatch):
    """The relaunched .exe must not reuse the first copy's (soon deleted) unpack folder."""
    import squirrel_vim_quest.app as app_module

    calls = []
    monkeypatch.setattr(app_module.os, "name", "nt")
    monkeypatch.delenv("WT_SESSION", raising=False)
    monkeypatch.delenv("SVQ_NO_WT", raising=False)
    monkeypatch.setenv("_PYI_APPLICATION_HOME_DIR", r"C:\Temp\_MEI1234")
    monkeypatch.setattr(app_module.shutil, "which", lambda name: r"C:\wt.exe")
    monkeypatch.setattr(app_module.sys, "frozen", True, raising=False)
    monkeypatch.setattr(app_module.subprocess, "Popen", lambda cmd, env: calls.append((cmd, env)))
    assert app_module._relaunch_in_windows_terminal(["--no-wt"])
    cmd, env = calls[0]
    assert cmd[0] == r"C:\wt.exe" and cmd[-1] == "--no-wt"
    assert env["PYINSTALLER_RESET_ENVIRONMENT"] == "1"
    assert not any(k.startswith("_PYI_") for k in env)


def test_self_check_passes(capsys):
    import squirrel_vim_quest.app as app_module

    assert app_module.main(["--check"]) == 0
    out = capsys.readouterr().out
    assert "Line Bridge: 5 stones ok" in out and out.strip().endswith("OK")


async def test_meet_level_teaches_all_four_keys(monkeypatch):
    monkeypatch.setattr(meet, "DEMO_STEP", 0.1)
    app = SquirrelApp()
    async with app.run_test(size=SIZE) as pilot:
        await pilot.press("enter")
        app.start_level(load_level("island1", 1))
        await pilot.pause()
        for key in "jkhl":
            await wait_for(pilot, lambda: getattr(app.screen, "phase", None) == "try")
            assert app.screen.key == key
            await pilot.press("x")  # wrong key: shake, no progress
            assert app.screen.presses == 0
            await pilot.press(key, key, key)
            if key != "l":
                await wait_for(pilot, lambda: app.screen.phase == "demo")
        await wait_for(pilot, lambda: isinstance(app.screen, ResultsScreen))
        assert app.save.stars_for("island1/stone1") == 3
        await pilot.press("enter")
        assert isinstance(app.screen, MapScreen)
        assert app.screen.stone_i == 1  # Pip moved to the next stone


async def test_puzzle_par_gives_three_stars():
    app = SquirrelApp()
    async with app.run_test(size=SIZE) as pilot:
        await pilot.press("enter")
        app.start_level(load_level("island1", 2))
        await pilot.pause()
        assert isinstance(app.screen, PuzzleScreen)
        await pilot.press(*"jjllll")
        await wait_for(pilot, lambda: isinstance(app.screen, ResultsScreen))
        assert app.save.stars_for("island1/stone2") == 3


async def test_puzzle_slow_route_replays_par():
    app = SquirrelApp()
    async with app.run_test(size=SIZE) as pilot:
        await pilot.press("enter")
        app.start_level(load_level("island1", 2))
        await pilot.pause()
        await pilot.press(*"hlhlhl", *"jjllll")  # 12 keys, par is 6
        assert app.screen.phase == "replay"
        await wait_for(pilot, lambda: isinstance(app.screen, ResultsScreen))
        assert app.save.stars_for("island1/stone2") == 1


async def test_arrow_keys_blocked_and_hints():
    app = SquirrelApp()
    async with app.run_test(size=SIZE) as pilot:
        await pilot.press("enter")
        app.start_level(load_level("island1", 2))
        await pilot.pause()
        start = app.screen.state
        await pilot.press("down")
        assert app.screen.state == start
        assert app.audio.last_line == "Use j!"
        assert app.screen.steps == 0
        await pilot.press("x", "y", "z")
        assert app.audio.last_line == "Try j!"
        assert app.screen.steps == 0


async def test_tab_pause_menu_back_to_map():
    app = SquirrelApp()
    async with app.run_test(size=SIZE) as pilot:
        await pilot.press("enter")
        app.start_level(load_level("island1", 2))
        await pilot.pause()
        await pilot.press("tab")
        assert isinstance(app.screen, PauseScreen)
        await pilot.press("tab")
        assert isinstance(app.screen, PuzzleScreen)
        await pilot.press("tab", "j", "j", "enter")  # Play, Sound, Map
        assert isinstance(app.screen, MapScreen)


async def test_garden_runs_to_the_end():
    level = load_level("island1", 4)
    level.settings = {**level.settings, "duration": 3, "seed": 1}
    app = SquirrelApp()
    async with app.run_test(size=SIZE) as pilot:
        await pilot.press("enter")
        app.start_level(level)
        await wait_for(pilot, lambda: getattr(app.screen, "phase", None) == "play")
        assert isinstance(app.screen, GardenScreen)
        for _ in range(6):
            await pilot.press(app.screen.hint_key() or "l")
            await pilot.pause(0.15)
        await wait_for(pilot, lambda: isinstance(app.screen, ResultsScreen))
        assert app.save.stars_for("island1/stone4") >= 1


async def test_word_meet_w_then_b(monkeypatch):
    monkeypatch.setattr(meet, "DEMO_STEP", 0.1)
    app = SquirrelApp()
    async with app.run_test(size=SIZE) as pilot:
        await pilot.press("enter")
        app.start_level(load_level("island2", 1))
        await pilot.pause()
        await wait_for(pilot, lambda: getattr(app.screen, "phase", None) == "try")
        await pilot.press("w", "w", "w")
        assert app.screen.state[:2] == (0, 12)  # "cat sun big dog": 4th word
        await wait_for(pilot, lambda: getattr(app.screen, "phase", None) == "try" and app.screen.key == "b")
        await pilot.press("b", "b", "b")
        await wait_for(pilot, lambda: isinstance(app.screen, ResultsScreen))
        assert app.save.stars_for("island2/stone1") == 3


async def test_word_puzzle_w_beats_l():
    app = SquirrelApp()
    async with app.run_test(size=SIZE) as pilot:
        await pilot.press("enter")
        app.start_level(load_level("island2", 2))
        await pilot.pause()
        assert app.audio.last_line == "Go to the flag!"
        await pilot.press(*"wwwwww")
        await wait_for(pilot, lambda: isinstance(app.screen, ResultsScreen))
        assert app.save.stars_for("island2/stone2") == 3


async def test_bonus_meet_e_continues_into_puzzle(monkeypatch):
    monkeypatch.setattr(meet, "DEMO_STEP", 0.1)
    app = SquirrelApp()
    async with app.run_test(size=SIZE) as pilot:
        await pilot.press("enter")
        app.start_level(load_level("island2", 4))
        await wait_for(pilot, lambda: getattr(app.screen, "phase", None) == "try")
        await pilot.press("e", "e", "e")
        await wait_for(pilot, lambda: isinstance(app.screen, PuzzleScreen))
        await pilot.press(*"eeeeee")
        await wait_for(pilot, lambda: isinstance(app.screen, ResultsScreen))
        assert app.save.stars_for("island2/stone4") == 3


async def test_frog_river_runs_to_the_end():
    level = load_level("island2", 3)
    level.settings = {**level.settings, "duration": 4, "seed": 2, "drift_start": 0.3, "drift_end": 0.3}
    app = SquirrelApp()
    async with app.run_test(size=SIZE) as pilot:
        await pilot.press("enter")
        app.start_level(level)
        await wait_for(pilot, lambda: getattr(app.screen, "phase", None) == "play")
        assert isinstance(app.screen, RiverScreen)
        for _ in range(8):
            if not isinstance(app.screen, RiverScreen) or app.screen.phase != "play":
                break
            await pilot.press(app.screen.hint_key())
            await pilot.pause(0.2)
        await wait_for(pilot, lambda: isinstance(app.screen, ResultsScreen))
        assert app.save.stars_for("island2/stone3") >= 1


async def test_river_drift_carries_pip_and_edge_splashes():
    level = load_level("island2", 3)
    level.settings = {**level.settings, "seed": 5}
    app = SquirrelApp()
    async with app.run_test(size=SIZE) as pilot:
        await pilot.press("enter")
        app.start_level(level)
        await wait_for(pilot, lambda: getattr(app.screen, "phase", None) == "play")
        river = app.screen
        river.cursor = (0, 0, 0)
        river._drift()  # Pip was on the first letter: drifts off the edge
        assert river.bumps == 1
        assert river.line[river.cursor[1]] != " " and river.cursor[1] >= 3
        col = river.cursor[1]
        river.grace = 0
        river._drift()
        assert river.cursor[1] == col - 1  # rides the log
        assert river.line[river.cursor[1]] != " "


async def test_fish_rapids_won_by_following_hints():
    level = load_level("island2", 5)
    level.settings = {**level.settings, "fish_every": 999}  # no fish
    app = SquirrelApp()
    async with app.run_test(size=SIZE) as pilot:
        await pilot.press("enter")
        app.start_level(level)
        await wait_for(pilot, lambda: getattr(app.screen, "phase", None) == "play")
        assert isinstance(app.screen, RapidsScreen)
        for _ in range(60):
            if not isinstance(app.screen, RapidsScreen) or app.screen.phase != "play":
                break
            await pilot.press(app.screen.hint_key())
        await wait_for(pilot, lambda: isinstance(app.screen, ResultsScreen))
        # Hints only chase plain acorns and the flag, so gold is missed: 2 stars.
        assert app.save.stars_for("island2/stone5") == 2


async def test_fish_splash_sends_pip_home():
    level = load_level("island2", 5)
    level.settings = {**level.settings, "fish_every": 999}
    app = SquirrelApp()
    async with app.run_test(size=SIZE) as pilot:
        await pilot.press("enter")
        app.start_level(level)
        await wait_for(pilot, lambda: getattr(app.screen, "phase", None) == "play")
        rapids = app.screen
        await pilot.press("w", "w")
        rapids.fish.append({"cell": rapids.pip, "phase": "splash", "t": 0.5})
        await pilot.pause(0.25)
        assert rapids.state == rapids.home and rapids.bumps == 1


async def test_line_meet_dollar_then_zero(monkeypatch):
    monkeypatch.setattr(meet, "DEMO_STEP", 0.1)
    app = SquirrelApp()
    async with app.run_test(size=SIZE) as pilot:
        await pilot.press("enter")
        app.start_level(load_level("island3", 1))
        for key in "$0":
            await wait_for(pilot, lambda: getattr(app.screen, "phase", None) == "try" and app.screen.key == key)
            end = len("pip can run to the end") - 1
            for i in range(3):
                await wait_for(pilot, lambda: app.screen.phase == "try")
                await pilot.press(key)
                assert app.screen.state[1] == (end if key == "$" else 0)
        await wait_for(pilot, lambda: isinstance(app.screen, ResultsScreen))
        assert app.save.stars_for("island3/stone1") == 3


async def test_line_puzzle_par_route():
    app = SquirrelApp()
    async with app.run_test(size=SIZE) as pilot:
        await pilot.press("enter")
        app.start_level(load_level("island3", 2))
        await pilot.pause()
        await pilot.press("$", "j", "j", "j", "k", "0")
        await wait_for(pilot, lambda: isinstance(app.screen, ResultsScreen))
        assert app.save.stars_for("island3/stone2") == 3


async def test_ping_pong_catch_and_miss():
    level = load_level("island3", 3)
    level.settings = {**level.settings, "seed": 3, "duration": 60}
    app = SquirrelApp()
    async with app.run_test(size=SIZE) as pilot:
        await pilot.press("enter")
        app.start_level(level)
        await wait_for(pilot, lambda: getattr(app.screen, "phase", None) == "play")
        pong = app.screen
        assert isinstance(pong, PongScreen)
        await wait_for(pilot, lambda: pong.ball is not None)
        while pong.hint_key():
            await pilot.press(pong.hint_key())
        await wait_for(pilot, lambda: pong.caught == 1)
        await wait_for(pilot, lambda: pong.ball is not None)
        goal = pong._goal()
        # Stand on the other end of the ball's bridge and miss it.
        wrong = (goal[0], 0 if goal[1] else len(pong.board.lines[goal[0]]) - 1)
        pong.state = (wrong[0], wrong[1], wrong[1])
        await wait_for(pilot, lambda: pong.missed == 1)
        pong.time_left = 0.05
        await wait_for(pilot, lambda: isinstance(app.screen, ResultsScreen))
        assert app.save.stars_for("island3/stone3") == 3  # 1 miss is still 3 stars


async def test_storm_wind_blows_pip_home_and_boss_can_be_won():
    level = load_level("island3", 5)
    level.settings = {**level.settings, "seed": 2, "gust_every": 999}
    app = SquirrelApp()
    async with app.run_test(size=SIZE) as pilot:
        await pilot.press("enter")
        app.start_level(level)
        await wait_for(pilot, lambda: getattr(app.screen, "phase", None) == "play")
        storm = app.screen
        assert isinstance(storm, StormScreen)
        await pilot.press("j")
        storm.gust = {"row": storm.pip[0], "phase": "blow", "t": 0.5}
        await pilot.pause(0.25)
        assert storm.state == storm.home and storm.bumps == 1
        storm.gust = None
        for _ in range(200):
            if not isinstance(app.screen, StormScreen) or storm.phase != "play":
                break
            key = storm.hint_key()
            if key:
                await pilot.press(key)
            else:
                await pilot.pause(0.1)
        await wait_for(pilot, lambda: isinstance(app.screen, ResultsScreen))
        assert app.save.stars_for("island3/stone5") == 3


async def test_maze_boss_can_be_won_by_following_hints():
    level = load_level("island1", 5)
    level.settings = {**level.settings, "fox_every": 999}  # foxes stay home
    app = SquirrelApp()
    async with app.run_test(size=SIZE) as pilot:
        await pilot.press("enter")
        app.start_level(level)
        await wait_for(pilot, lambda: getattr(app.screen, "phase", None) == "play")
        assert isinstance(app.screen, MazeScreen)
        for _ in range(80):
            if not isinstance(app.screen, MazeScreen) or app.screen.phase != "play":
                break
            await pilot.press(app.screen.hint_key())
        await wait_for(pilot, lambda: isinstance(app.screen, ResultsScreen))
        assert app.save.stars_for("island1/stone5") == 3

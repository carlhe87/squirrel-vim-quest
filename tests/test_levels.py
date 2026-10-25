import pytest

from squirrel_vim_quest.engine.text import TEXT_KEYS
from squirrel_vim_quest.levels import ISLANDS, load_island
from squirrel_vim_quest.screens.board import TextBoard, make_board

LEVELS = [lv for island in ISLANDS if island.ready for lv in load_island(island.id)]


@pytest.mark.parametrize("level", LEVELS, ids=lambda lv: lv.id)
def test_level_is_well_formed(level):
    assert set(level.keys) <= set(TEXT_KEYS)
    if level.kind in ("meet", "bonus"):
        assert level.teach and set(level.teach) <= set(level.keys)
    if level.grid is not None:
        # Fits a default Windows Terminal (120 x 30) with 4x2 cells plus the frame.
        assert level.grid.width * 4 <= 110 and level.grid.height * 2 <= 20
    if level.text is not None:
        board = TextBoard(level.text)
        assert max(len(line) for line in level.text) * 4 <= 110 and len(level.text) * 3 <= 20
        # Kids' text: lowercase words and single spaces only, so w and W agree.
        for line in level.text:
            assert line == line.strip() and "  " not in line
            assert all(ch.islower() or ch == " " for ch in line)
        for pos in [level.start, *level.acorns, *level.gold] + ([level.flag] if level.flag else []):
            assert board.is_letter(pos)


@pytest.mark.parametrize("level", [lv for lv in LEVELS if lv.par is not None], ids=lambda lv: lv.id)
def test_puzzle_par_matches_solver(level):
    board = make_board(level)
    targets = set(level.acorns) | ({level.flag} if level.flag else set())
    route = board.solve(board.start(level.start), targets, level.keys)
    assert route is not None
    assert len(route) == level.par


def test_island1_boss_acorns_and_gate_reachable():
    boss = load_island("island1")[4]
    board = make_board(boss)
    assert board.solve(boss.start, boss.acorns, boss.keys) is not None
    assert board.route(boss.start, [boss.gate], "hjkl") is not None
    assert len(boss.foxes) == 2


def test_island2_boss_needs_e_for_gold():
    boss = load_island("island2")[4]
    board = make_board(boss)
    start = board.start(boss.start)
    everything = set(boss.acorns) | set(boss.gold) | {boss.flag}
    assert board.solve(start, everything, boss.keys) is not None
    # Without e the gold acorns on log ends can't be reached.
    assert board.solve(start, boss.gold, boss.keys.replace("e", "")) is None


def test_action_levels():
    garden = load_island("island1")[3]
    assert len(garden.snails) == 1 and garden.settings["duration"] <= 90
    river = load_island("island2")[2]
    assert river.settings["game"] == "river" and river.settings["duration"] <= 90
    assert all(w.isalpha() and w.islower() for w in river.settings["words"])

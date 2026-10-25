from squirrel_vim_quest.engine.grid import Grid, parse_map
from squirrel_vim_quest.engine.motions import move
from squirrel_vim_quest.engine.solver import path_to_nearest, solve, step_toward
from squirrel_vim_quest.screens.garden import action_stars
from squirrel_vim_quest.screens.maze import boss_stars
from squirrel_vim_quest.screens.puzzle import puzzle_stars


def test_hjkl_move_one_cell():
    g = Grid(["...", "...", "..."])
    assert move(g, (1, 1), "h") == (1, 0)
    assert move(g, (1, 1), "j") == (2, 1)
    assert move(g, (1, 1), "k") == (0, 1)
    assert move(g, (1, 1), "l") == (1, 2)


def test_edges_stop_like_vim():
    g = Grid(["...", "..."])
    assert move(g, (0, 0), "h") == (0, 0)
    assert move(g, (0, 0), "k") == (0, 0)
    assert move(g, (1, 2), "j") == (1, 2)
    assert move(g, (1, 2), "l") == (1, 2)


def test_rocks_block():
    g = Grid([".#."])
    assert move(g, (0, 0), "l") == (0, 0)


def test_parse_map_finds_items():
    grid, found = parse_map("P.o\n.#S\n")
    assert found["P"] == [(0, 0)]
    assert found["o"] == [(0, 2)]
    assert found["S"] == [(1, 2)]
    assert grid.is_open((0, 2)) and grid.is_rock((1, 1))


def test_solver_picks_best_order():
    grid, found = parse_map("o..P.o")
    # Going right first (2) then left (5) = 7; left first (3) then right (5) = 8.
    assert len(solve(grid, found["P"][0], found["o"])) == 7


def test_solver_none_when_unreachable():
    grid, found = parse_map("P#o")
    assert solve(grid, found["P"][0], found["o"]) is None


def test_path_avoids_blocked_cells():
    grid, _ = parse_map("...\n...\n...")
    route = path_to_nearest(grid, (0, 0), [(0, 2)], blocked=[(0, 1)])
    assert route is not None and len(route) == 4


def test_step_toward():
    grid, _ = parse_map("....")
    assert step_toward(grid, (0, 0), (0, 3)) == (0, 1)


def test_star_rules():
    assert puzzle_stars(6, 6) == 3
    assert puzzle_stars(9, 6) == 2
    assert puzzle_stars(10, 6) == 1
    assert action_stars(eaten=10, vanished=0, bumps=1) == 3
    assert action_stars(eaten=7, vanished=3, bumps=0) == 2
    assert action_stars(eaten=6, vanished=4, bumps=0) == 1
    assert boss_stars(1) == 3 and boss_stars(3) == 2 and boss_stars(4) == 1

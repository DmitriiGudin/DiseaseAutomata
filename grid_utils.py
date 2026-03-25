from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Iterator, List, Optional, Set, Tuple

import params


# ============================================================================
# State constants
# ============================================================================

SUSCEPTIBLE = 0
EXPOSED = 1
INFECTIOUS = 2
RECOVERED = 3

STATE_NAMES = {SUSCEPTIBLE: "S", EXPOSED: "E", INFECTIOUS: "I", RECOVERED: "R"}

STATE_FROM_NAME = {"S": SUSCEPTIBLE, "E": EXPOSED, "I": INFECTIOUS, "R": RECOVERED}


Coord = Tuple[int, int]
StateMap = Dict[Coord, int]
TimerMap = Dict[Coord, int]


# ============================================================================
# Basic geometry helpers
# ============================================================================

def in_bounds(x: int, y: int) -> bool:
    """Return True if (x, y) lies inside the grid."""
    return 0 <= x < params.GRID_WIDTH and 0 <= y < params.GRID_HEIGHT


def moore_neighbors(x: int, y: int) -> Iterator[Coord]:
    """
    Yield all valid Moore-neighborhood neighbors of (x, y).
    Moore neighborhood = 8 surrounding cells.
    """
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            if dx == 0 and dy == 0:
                continue
            nx = x + dx
            ny = y + dy
            if in_bounds(nx, ny):
                yield (nx, ny)


# ============================================================================
# Sparse state access
# ============================================================================

def create_empty_state_map() -> StateMap:
    """Return an empty sparse state map (all cells implicitly S)."""
    return {}


def create_empty_timer_map() -> TimerMap:
    """Return an empty timer map."""
    return {}


def get_state(state_map: StateMap, x: int, y: int) -> int:
    """
    Return the state at (x, y).
    Missing entries are implicitly susceptible.
    """
    return state_map.get((x, y), SUSCEPTIBLE)


def set_state(
    state_map: StateMap,
    timer_map: TimerMap,
    x: int,
    y: int,
    state: int,
    *,
    exposed_timer: int = 0,
) -> None:
    """
    Set the state at (x, y).

    Sparse-storage rule:
    - S is not stored
    - E, I, R are stored
    - timer_map is currently unused, but kept for compatibility
    """
    coord = (x, y)

    if state == SUSCEPTIBLE:
        state_map.pop(coord, None)
        timer_map.pop(coord, None)
        return

    state_map[coord] = state
    timer_map.pop(coord, None)


def clear_cell(state_map: StateMap, timer_map: TimerMap, x: int, y: int) -> None:
    """Reset a cell back to susceptible."""
    set_state(state_map, timer_map, x, y, SUSCEPTIBLE)


# ============================================================================
# Counting / local analysis
# ============================================================================

def count_infectious_neighbors(state_map: StateMap, x: int, y: int) -> int:
    """Count infectious neighbors of (x, y) in the Moore neighborhood."""
    count = 0
    for nx, ny in moore_neighbors(x, y):
        if state_map.get((nx, ny)) == INFECTIOUS:
            count += 1
    return count


def get_candidate_cells(state_map: StateMap) -> Set[Coord]:
    """
    Return the set of cells that might change on the next update.

    We only need to check:
    - all currently non-S cells
    - all neighbors of infectious cells, since those S cells may become E
    """
    candidates: Set[Coord] = set()

    for (x, y), state in state_map.items():
        candidates.add((x, y))
        if state == INFECTIOUS:
            for coord in moore_neighbors(x, y):
                candidates.add(coord)

    return candidates


def count_states(state_map: StateMap) -> Dict[int, int]:
    """
    Return counts of S/E/I/R across the whole grid.
    Since S is implicit, compute it from total size.
    """
    counts = {
        SUSCEPTIBLE: params.GRID_WIDTH * params.GRID_HEIGHT,
        EXPOSED: 0,
        INFECTIOUS: 0,
        RECOVERED: 0,
    }

    for state in state_map.values():
        counts[state] += 1
        counts[SUSCEPTIBLE] -= 1

    return counts


# ============================================================================
# Save / load maps
# ============================================================================

def save_map(filepath: str | Path, state_map: StateMap, timer_map: Optional[TimerMap] = None) -> None:
    """
    Save a sparse map to JSON.

    Format:
    {
        "width": ...,
        "height": ...,
        "cells": [
            {"x": 10, "y": 4, "state": 2},
            {"x": 11, "y": 4, "state": 1, "timer": 2}
        ]
    }

    Only non-S cells are stored.
    """
    if timer_map is None:
        timer_map = {}

    cells: List[dict] = []

    for (x, y), state in sorted(state_map.items(), key=lambda item: (item[0][1], item[0][0])):
        record = {
            "x": x,
            "y": y,
            "state": state,
        }
        cells.append(record)

    payload = {"width": params.GRID_WIDTH, "height": params.GRID_HEIGHT, "cells": cells}

    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)

    with filepath.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)


def load_map(filepath: str | Path) -> Tuple[StateMap, TimerMap]:
    """
    Load a sparse map from JSON.

    Returns:
        state_map, timer_map
    """
    filepath = Path(filepath)

    with filepath.open("r", encoding="utf-8") as f:
        payload = json.load(f)

    width = payload.get("width")
    height = payload.get("height")

    if width != params.GRID_WIDTH or height != params.GRID_HEIGHT:
        raise ValueError(f"Map dimensions ({width}, {height}) do not match params "
            f"({params.GRID_WIDTH}, {params.GRID_HEIGHT}).")

    state_map: StateMap = {}
    timer_map: TimerMap = {}

    for cell in payload.get("cells", []):
        x = int(cell["x"])
        y = int(cell["y"])
        state = int(cell["state"])

        if not in_bounds(x, y):
            raise ValueError(f"Cell ({x}, {y}) lies outside the grid.")

        if state not in (EXPOSED, INFECTIOUS, RECOVERED):
            raise ValueError(f"Invalid stored state {state} at ({x}, {y}).")

        state_map[(x, y)] = state

    return state_map, timer_map


def list_map_files(maps_dir: str | Path = "maps") -> List[Path]:
    """Return all .json map files inside maps_dir, sorted by name."""
    maps_path = Path(maps_dir)
    if not maps_path.exists():
        return []
    return sorted(maps_path.glob("*.json"))


# ============================================================================
# Optional conversion helpers
# ============================================================================

def to_dense_grid(state_map: StateMap) -> List[List[int]]:
    """
    Convert sparse state map to a dense 2D Python list.
    Useful for debugging or testing.
    """
    grid = [[SUSCEPTIBLE for _ in range(params.GRID_WIDTH)] for _ in range(params.GRID_HEIGHT)]

    for (x, y), state in state_map.items():
        grid[y][x] = state

    return grid
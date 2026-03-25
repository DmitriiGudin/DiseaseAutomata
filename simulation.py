# simulation.py

from __future__ import annotations

import copy
import random
from pathlib import Path
from typing import Tuple

import pygame

import params
from grid_utils import (
    SUSCEPTIBLE,
    EXPOSED,
    INFECTIOUS,
    RECOVERED,
    StateMap,
    TimerMap,
    count_infectious_neighbors,
    count_states,
    get_candidate_cells,
    load_map,
)


# ============================================================================
# Visual settings
# ============================================================================

WINDOW_WIDTH = params.GRID_WIDTH * params.CELL_SIZE
WINDOW_HEIGHT = params.GRID_HEIGHT * params.CELL_SIZE + 70

GRID_PIXEL_WIDTH = params.GRID_WIDTH * params.CELL_SIZE
GRID_PIXEL_HEIGHT = params.GRID_HEIGHT * params.CELL_SIZE

BACKGROUND_COLOR = (245, 245, 245)
GRID_LINE_COLOR = (210, 210, 210)
TEXT_COLOR = (20, 20, 20)

STATE_COLORS = {
    SUSCEPTIBLE: (25, 25, 25),      # dark gray / black
    EXPOSED: (240, 190, 40),        # yellow-orange
    INFECTIOUS: (210, 40, 40),      # red
    RECOVERED: (50, 90, 210),       # blue
}


# ============================================================================
# Core SEIR step
# ============================================================================

def infection_probability(num_infectious_neighbors: int) -> float:
    """
    Probability that an S-cell becomes E during one time step.

    Each infectious neighbor independently transmits with probability alpha.
    Therefore:
        P(no transmission) = (1 - alpha)^k
        P(infection)       = 1 - (1 - alpha)^k
    """
    if num_infectious_neighbors <= 0:
        return 0.0
    return 1.0 - (1.0 - params.alpha) ** num_infectious_neighbors


def step_simulation(state_map: StateMap, timer_map: TimerMap) -> Tuple[StateMap, TimerMap]:
    """
    Advance the simulation by one synchronous stochastic time step.

    Rules:
    - S -> E with probability 1 - (1 - alpha)^k, where k = number of I neighbors
    - E -> I with probability beta
    - I -> R with probability gamma
    - R stays R forever

    Notes:
    - timer_map is ignored and returned empty, since timers are no longer used
    - updates are synchronous: all transitions are sampled from the old state_map
    """
    next_state_map: StateMap = {}
    next_timer_map: TimerMap = {}

    candidate_cells = get_candidate_cells(state_map)

    for x, y in candidate_cells:
        coord = (x, y)
        current_state = state_map.get(coord, SUSCEPTIBLE)

        if current_state == SUSCEPTIBLE:
            k = count_infectious_neighbors(state_map, x, y)
            p_infect = infection_probability(k)

            if random.random() < p_infect:
                next_state_map[coord] = EXPOSED
            # else stays S implicitly

        elif current_state == EXPOSED:
            if random.random() < params.beta:
                next_state_map[coord] = INFECTIOUS
            else:
                next_state_map[coord] = EXPOSED

        elif current_state == INFECTIOUS:
            if random.random() < params.gamma:
                next_state_map[coord] = RECOVERED
            else:
                next_state_map[coord] = INFECTIOUS

        elif current_state == RECOVERED:
            next_state_map[coord] = RECOVERED

        else:
            raise ValueError(f"Unknown state {current_state} at {coord}")

    return next_state_map, next_timer_map


# ============================================================================
# Drawing helpers
# ============================================================================

def draw_grid(
    screen: pygame.Surface,
    state_map: StateMap,
    font: pygame.font.Font,
    fps: int,
    paused: bool,
    step_count: int,
) -> None:
    """Draw the current grid and footer text."""
    screen.fill(BACKGROUND_COLOR)

    cell_size = params.CELL_SIZE

    for y in range(params.GRID_HEIGHT):
        for x in range(params.GRID_WIDTH):
            state = state_map.get((x, y), SUSCEPTIBLE)
            color = STATE_COLORS[state]

            rect = pygame.Rect(
                x * cell_size,
                y * cell_size,
                cell_size,
                cell_size,
            )
            pygame.draw.rect(screen, color, rect)

    for x in range(params.GRID_WIDTH + 1):
        px = x * cell_size
        pygame.draw.line(screen, GRID_LINE_COLOR, (px, 0), (px, GRID_PIXEL_HEIGHT), 1)

    for y in range(params.GRID_HEIGHT + 1):
        py = y * cell_size
        pygame.draw.line(screen, GRID_LINE_COLOR, (0, py), (GRID_PIXEL_WIDTH, py), 1)

    footer_rect = pygame.Rect(0, GRID_PIXEL_HEIGHT, WINDOW_WIDTH, WINDOW_HEIGHT - GRID_PIXEL_HEIGHT)
    pygame.draw.rect(screen, (235, 235, 235), footer_rect)

    counts = count_states(state_map)
    status_text = (
        f"Step: {step_count}    "
        f"FPS: {fps}    "
        f"{'PAUSED' if paused else 'RUNNING'}    "
        f"S={counts[SUSCEPTIBLE]}  "
        f"E={counts[EXPOSED]}  "
        f"I={counts[INFECTIOUS]}  "
        f"R={counts[RECOVERED]}"
    )
    controls_text = "SPACE pause/resume | N single step | R reset | UP/DOWN speed | ESC quit"

    status_surface = font.render(status_text, True, TEXT_COLOR)
    controls_surface = font.render(controls_text, True, TEXT_COLOR)

    screen.blit(status_surface, (10, GRID_PIXEL_HEIGHT + 10))
    screen.blit(controls_surface, (10, GRID_PIXEL_HEIGHT + 35))


# ============================================================================
# Main runner
# ============================================================================

def run_simulation(map_path: str | Path) -> None:
    """
    Load a map and run the simulation interactively.
    """
    initial_state_map, initial_timer_map = load_map(map_path)

    state_map: StateMap = copy.deepcopy(initial_state_map)
    timer_map: TimerMap = copy.deepcopy(initial_timer_map)

    pygame.init()
    pygame.display.set_caption("Probabilistic SEIR Cellular Automaton")
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 24)

    paused = False
    running = True
    fps = params.FPS
    step_count = 0

    while running:
        do_single_step = False

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

                elif event.key == pygame.K_SPACE:
                    paused = not paused

                elif event.key == pygame.K_n:
                    if paused:
                        do_single_step = True

                elif event.key == pygame.K_r:
                    state_map = copy.deepcopy(initial_state_map)
                    timer_map = copy.deepcopy(initial_timer_map)
                    step_count = 0
                    paused = True

                elif event.key == pygame.K_UP:
                    fps = min(120, fps + 1)

                elif event.key == pygame.K_DOWN:
                    fps = max(1, fps - 1)

        if not paused or do_single_step:
            state_map, timer_map = step_simulation(state_map, timer_map)
            step_count += 1

        draw_grid(
            screen=screen,
            state_map=state_map,
            font=font,
            fps=fps,
            paused=paused,
            step_count=step_count,
        )

        pygame.display.flip()
        clock.tick(fps)

    pygame.quit()


# ============================================================================
# Optional direct launch for testing
# ============================================================================

if __name__ == "__main__":
    default_map = Path("maps") / "test_map.json"
    if not default_map.exists():
        raise FileNotFoundError(
            f"Could not find {default_map}. Create a map first or pass this through launcher.py."
        )
    run_simulation(default_map)
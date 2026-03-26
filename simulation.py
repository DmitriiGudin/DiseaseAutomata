from __future__ import annotations

import copy
import random
from pathlib import Path
from typing import Tuple

import pygame

from settings_utils import get_current_settings
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


BACKGROUND_COLOR = (245, 245, 245)
GRID_LINE_COLOR = (210, 210, 210)
TEXT_COLOR = (20, 20, 20)

STATE_COLORS = {
    SUSCEPTIBLE: (25, 25, 25),
    EXPOSED: (240, 190, 40),
    INFECTIOUS: (210, 40, 40),
    RECOVERED: (50, 90, 210),
}


def infection_probability(num_infectious_neighbors: int, alpha: float) -> float:
    if num_infectious_neighbors <= 0:
        return 0.0
    return 1.0 - (1.0 - alpha) ** num_infectious_neighbors


def step_simulation(state_map: StateMap, timer_map: TimerMap, alpha: float, beta: float, gamma: float) -> Tuple[StateMap, TimerMap]:
    next_state_map: StateMap = {}
    next_timer_map: TimerMap = {}

    candidate_cells = get_candidate_cells(state_map)

    for x, y in candidate_cells:
        coord = (x, y)
        current_state = state_map.get(coord, SUSCEPTIBLE)

        if current_state == SUSCEPTIBLE:
            k = count_infectious_neighbors(state_map, x, y)
            if random.random() < infection_probability(k, alpha):
                next_state_map[coord] = EXPOSED

        elif current_state == EXPOSED:
            if random.random() < beta:
                next_state_map[coord] = INFECTIOUS
            else:
                next_state_map[coord] = EXPOSED

        elif current_state == INFECTIOUS:
            if random.random() < gamma:
                next_state_map[coord] = RECOVERED
            else:
                next_state_map[coord] = INFECTIOUS

        elif current_state == RECOVERED:
            next_state_map[coord] = RECOVERED

        else:
            raise ValueError(f"Unknown state {current_state} at {coord}")

    return next_state_map, next_timer_map


def draw_grid(
    screen: pygame.Surface,
    state_map: StateMap,
    font: pygame.font.Font,
    fps: int,
    paused: bool,
    step_count: int,
    grid_width: int,
    grid_height: int,
    cell_size: int,
    grid_pixel_width: int,
    grid_pixel_height: int,
    window_width: int,
    window_height: int,
) -> None:
    screen.fill(BACKGROUND_COLOR)

    for y in range(grid_height):
        for x in range(grid_width):
            state = state_map.get((x, y), SUSCEPTIBLE)
            color = STATE_COLORS[state]
            rect = pygame.Rect(x * cell_size, y * cell_size, cell_size, cell_size)
            pygame.draw.rect(screen, color, rect)

    for x in range(grid_width + 1):
        px = x * cell_size
        pygame.draw.line(screen, GRID_LINE_COLOR, (px, 0), (px, grid_pixel_height), 1)

    for y in range(grid_height + 1):
        py = y * cell_size
        pygame.draw.line(screen, GRID_LINE_COLOR, (0, py), (grid_pixel_width, py), 1)

    footer_rect = pygame.Rect(0, grid_pixel_height, window_width, window_height - grid_pixel_height)
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

    screen.blit(status_surface, (10, grid_pixel_height + 10))
    screen.blit(controls_surface, (10, grid_pixel_height + 35))


def run_simulation(map_path: str | Path) -> None:
    settings = get_current_settings()
    grid_width = settings["GRID_WIDTH"]
    grid_height = settings["GRID_HEIGHT"]
    cell_size = settings["CELL_SIZE"]
    alpha = settings["alpha"]
    beta = settings["beta"]
    gamma = settings["gamma"]
    fps_default = settings["FPS"]

    window_width = grid_width * cell_size
    window_height = grid_height * cell_size + 70
    grid_pixel_width = grid_width * cell_size
    grid_pixel_height = grid_height * cell_size

    initial_state_map, initial_timer_map = load_map(map_path)

    state_map: StateMap = copy.deepcopy(initial_state_map)
    timer_map: TimerMap = copy.deepcopy(initial_timer_map)

    pygame.init()
    pygame.display.set_caption("Probabilistic SEIR Cellular Automaton")
    screen = pygame.display.set_mode((window_width, window_height))
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 24)

    paused = False
    running = True
    fps = fps_default
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
            state_map, timer_map = step_simulation(state_map, timer_map, alpha, beta, gamma)
            step_count += 1

        draw_grid(
            screen=screen,
            state_map=state_map,
            font=font,
            fps=fps,
            paused=paused,
            step_count=step_count,
            grid_width=grid_width,
            grid_height=grid_height,
            cell_size=cell_size,
            grid_pixel_width=grid_pixel_width,
            grid_pixel_height=grid_pixel_height,
            window_width=window_width,
            window_height=window_height,
        )

        pygame.display.flip()
        clock.tick(fps)

    pygame.quit()


if __name__ == "__main__":
    default_map = Path("maps") / "test_map.json"
    if not default_map.exists():
        raise FileNotFoundError(
            f"Could not find {default_map}. Create a map first or pass this through launcher.py."
        )
    run_simulation(default_map)
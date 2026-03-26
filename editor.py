from __future__ import annotations

from pathlib import Path
from typing import Optional

import pygame

from settings_utils import get_current_settings
from grid_utils import (
    SUSCEPTIBLE,
    EXPOSED,
    INFECTIOUS,
    RECOVERED,
    StateMap,
    TimerMap,
    create_empty_state_map,
    create_empty_timer_map,
    load_map,
    save_map,
    set_state,
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

BRUSH_LABELS = {
    SUSCEPTIBLE: "S",
    EXPOSED: "E",
    INFECTIOUS: "I",
    RECOVERED: "R",
}


def mouse_to_cell(mouse_pos: tuple[int, int], grid_pixel_width: int, grid_pixel_height: int, cell_size: int) -> Optional[tuple[int, int]]:
    mx, my = mouse_pos
    if not (0 <= mx < grid_pixel_width and 0 <= my < grid_pixel_height):
        return None
    return (mx // cell_size, my // cell_size)


def apply_brush(state_map: StateMap, timer_map: TimerMap, cell: tuple[int, int], brush_state: int) -> None:
    x, y = cell
    set_state(state_map, timer_map, x, y, brush_state, exposed_timer=0)


def draw_editor(
    screen: pygame.Surface,
    state_map: StateMap,
    font: pygame.font.Font,
    small_font: pygame.font.Font,
    current_brush: int,
    current_filename: str,
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

    line1 = f"Brush: {BRUSH_LABELS[current_brush]}    File: {current_filename}"
    line2 = "1=S  2=E  3=I  4=R   |   Left click: paint   Right click: S"
    line3 = "C: clear   S: save   L: load   ESC: quit"

    surf1 = font.render(line1, True, TEXT_COLOR)
    surf2 = small_font.render(line2, True, TEXT_COLOR)
    surf3 = small_font.render(line3, True, TEXT_COLOR)

    screen.blit(surf1, (10, grid_pixel_height + 8))
    screen.blit(surf2, (10, grid_pixel_height + 38))
    screen.blit(surf3, (10, grid_pixel_height + 62))


def prompt_filename(screen: pygame.Surface, clock: pygame.time.Clock, font: pygame.font.Font, prompt: str) -> Optional[str]:
    text = ""

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return None
                elif event.key == pygame.K_RETURN:
                    stripped = text.strip()
                    return stripped if stripped else None
                elif event.key == pygame.K_BACKSPACE:
                    text = text[:-1]
                else:
                    if event.unicode and (event.unicode.isalnum() or event.unicode in ("_", "-", " ")):
                        text += event.unicode

        screen.fill((240, 240, 240))
        prompt_surface = font.render(prompt, True, (20, 20, 20))
        text_surface = font.render(text if text else "_", True, (20, 20, 20))
        help_surface = font.render("ENTER confirm   ESC cancel", True, (80, 80, 80))

        screen.blit(prompt_surface, (30, 40))
        screen.blit(text_surface, (30, 85))
        screen.blit(help_surface, (30, 130))

        pygame.display.flip()
        clock.tick(30)


def run_editor(initial_map_path: str | Path | None = None) -> None:
    settings = get_current_settings()
    grid_width = settings["GRID_WIDTH"]
    grid_height = settings["GRID_HEIGHT"]
    cell_size = settings["CELL_SIZE"]

    window_width = grid_width * cell_size
    window_height = grid_height * cell_size + 95
    grid_pixel_width = grid_width * cell_size
    grid_pixel_height = grid_height * cell_size

    if initial_map_path is not None:
        state_map, timer_map = load_map(initial_map_path)
        current_filename = Path(initial_map_path).name
    else:
        state_map = create_empty_state_map()
        timer_map = create_empty_timer_map()
        current_filename = "unsaved_map.json"

    pygame.init()
    pygame.display.set_caption("SEIR Map Editor")
    screen = pygame.display.set_mode((window_width, window_height))
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 28)
    small_font = pygame.font.SysFont(None, 24)

    current_brush = INFECTIOUS
    running = True

    while running:
        left_pressed = pygame.mouse.get_pressed(num_buttons=3)[0]
        right_pressed = pygame.mouse.get_pressed(num_buttons=3)[2]

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_1:
                    current_brush = SUSCEPTIBLE
                elif event.key == pygame.K_2:
                    current_brush = EXPOSED
                elif event.key == pygame.K_3:
                    current_brush = INFECTIOUS
                elif event.key == pygame.K_4:
                    current_brush = RECOVERED
                elif event.key == pygame.K_c:
                    state_map = create_empty_state_map()
                    timer_map = create_empty_timer_map()
                    current_filename = "unsaved_map.json"
                elif event.key == pygame.K_s:
                    name = prompt_filename(screen, clock, font, "Save map as:")
                    if name is not None:
                        filename = f"{name}.json" if not name.endswith(".json") else name
                        save_path = Path("maps") / filename
                        save_map(save_path, state_map, timer_map)
                        current_filename = filename
                elif event.key == pygame.K_l:
                    name = prompt_filename(screen, clock, font, "Load map:")
                    if name is not None:
                        filename = f"{name}.json" if not name.endswith(".json") else name
                        load_path = Path("maps") / filename
                        if load_path.exists():
                            state_map, timer_map = load_map(load_path)
                            current_filename = filename

        cell = mouse_to_cell(pygame.mouse.get_pos(), grid_pixel_width, grid_pixel_height, cell_size)

        if cell is not None:
            if left_pressed:
                apply_brush(state_map, timer_map, cell, current_brush)
            elif right_pressed:
                apply_brush(state_map, timer_map, cell, SUSCEPTIBLE)

        draw_editor(
            screen=screen,
            state_map=state_map,
            font=font,
            small_font=small_font,
            current_brush=current_brush,
            current_filename=current_filename,
            grid_width=grid_width,
            grid_height=grid_height,
            cell_size=cell_size,
            grid_pixel_width=grid_pixel_width,
            grid_pixel_height=grid_pixel_height,
            window_width=window_width,
            window_height=window_height,
        )

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()


if __name__ == "__main__":
    run_editor()
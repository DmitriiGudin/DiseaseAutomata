from __future__ import annotations

from pathlib import Path
from typing import Optional

import pygame

from settings_editor import run_settings_editor


MAPS_DIR = Path("maps")

WINDOW_WIDTH = 700
WINDOW_HEIGHT = 520

BACKGROUND_COLOR = (245, 245, 245)
TITLE_COLOR = (20, 20, 20)
TEXT_COLOR = (30, 30, 30)
SUBTLE_TEXT_COLOR = (90, 90, 90)

BUTTON_COLOR = (225, 225, 225)
BUTTON_HOVER_COLOR = (200, 220, 255)
BUTTON_BORDER_COLOR = (140, 140, 140)

PANEL_COLOR = (235, 235, 235)


class Button:
    def __init__(self, rect: pygame.Rect, text: str):
        self.rect = rect
        self.text = text

    def draw(self, screen: pygame.Surface, font: pygame.font.Font, hovered: bool) -> None:
        fill = BUTTON_HOVER_COLOR if hovered else BUTTON_COLOR
        pygame.draw.rect(screen, fill, self.rect, border_radius=10)
        pygame.draw.rect(screen, BUTTON_BORDER_COLOR, self.rect, width=2, border_radius=10)

        text_surface = font.render(self.text, True, TEXT_COLOR)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)

    def contains(self, pos: tuple[int, int]) -> bool:
        return self.rect.collidepoint(pos)


def init_launcher_window() -> tuple[pygame.Surface, pygame.time.Clock]:
    """
    Initialize or re-initialize the launcher window after other modules may
    have called pygame.quit().
    """
    pygame.init()
    pygame.display.set_caption("SEIR Cellular Automaton Launcher")
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    clock = pygame.time.Clock()
    return screen, clock


def draw_title(
    screen: pygame.Surface,
    title_font: pygame.font.Font,
    small_font: pygame.font.Font,
) -> None:
    title_surface = title_font.render("SEIR Cellular Automaton", True, TITLE_COLOR)
    subtitle_surface = small_font.render(
        "Interactive epidemic cellular automaton simulator",
        True,
        SUBTLE_TEXT_COLOR,
    )

    title_rect = title_surface.get_rect(center=(WINDOW_WIDTH // 2, 70))
    subtitle_rect = subtitle_surface.get_rect(center=(WINDOW_WIDTH // 2, 110))

    screen.blit(title_surface, title_rect)
    screen.blit(subtitle_surface, subtitle_rect)


def main_menu(screen: pygame.Surface, clock: pygame.time.Clock) -> str:
    """
    Show the main launcher menu.

    Returns:
        "editor", "simulation", "settings", "about", or "quit"
    """
    title_font = pygame.font.SysFont(None, 48)
    button_font = pygame.font.SysFont(None, 34)
    small_font = pygame.font.SysFont(None, 24)

    button_width = 260
    button_height = 56
    x = (WINDOW_WIDTH - button_width) // 2
    y0 = 165
    gap = 18

    buttons = [
        Button(pygame.Rect(x, y0 + 0 * (button_height + gap), button_width, button_height), "Run Editor"),
        Button(pygame.Rect(x, y0 + 1 * (button_height + gap), button_width, button_height), "Run Simulation"),
        Button(pygame.Rect(x, y0 + 2 * (button_height + gap), button_width, button_height), "Settings"),
        Button(pygame.Rect(x, y0 + 3 * (button_height + gap), button_width, button_height), "About"),
        Button(pygame.Rect(x, y0 + 4 * (button_height + gap), button_width, button_height), "Quit"),
    ]

    actions = ["editor", "simulation", "settings", "about", "quit"]

    while True:
        mouse_pos = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return "quit"

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for button, action in zip(buttons, actions):
                    if button.contains(mouse_pos):
                        return action

        screen.fill(BACKGROUND_COLOR)
        draw_title(screen, title_font, small_font)

        for button in buttons:
            button.draw(screen, button_font, button.contains(mouse_pos))

        pygame.display.flip()
        clock.tick(60)


def choose_map_menu(screen: pygame.Surface, clock: pygame.time.Clock) -> Optional[Path]:
    """
    Show a simple map selection screen.

    Returns:
        Selected map path, or None if cancelled.
    """
    from grid_utils import list_map_files

    title_font = pygame.font.SysFont(None, 42)
    button_font = pygame.font.SysFont(None, 30)
    small_font = pygame.font.SysFont(None, 24)

    while True:
        map_files = list_map_files(MAPS_DIR)
        mouse_pos = pygame.mouse.get_pos()

        buttons: list[tuple[Button, Optional[Path]]] = []

        panel_rect = pygame.Rect(90, 120, WINDOW_WIDTH - 180, WINDOW_HEIGHT - 200)

        if map_files:
            button_width = panel_rect.width - 60
            button_height = 42
            gap = 12
            start_x = panel_rect.x + 30
            start_y = panel_rect.y + 25

            max_visible = min(7, len(map_files))
            for i in range(max_visible):
                path = map_files[i]
                rect = pygame.Rect(
                    start_x,
                    start_y + i * (button_height + gap),
                    button_width,
                    button_height,
                )
                buttons.append((Button(rect, path.name), path))

            if len(map_files) > 7:
                note = f"Showing first 7 of {len(map_files)} maps"
            else:
                note = f"{len(map_files)} map(s) available"
        else:
            note = "No maps found"

        back_button = Button(
            pygame.Rect((WINDOW_WIDTH - 180) // 2, WINDOW_HEIGHT - 60, 180, 42),
            "Back",
        )

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return None

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if back_button.contains(mouse_pos):
                    return None

                for button, path in buttons:
                    if button.contains(mouse_pos):
                        return path

        screen.fill(BACKGROUND_COLOR)

        title_surface = title_font.render("Choose a Map", True, TITLE_COLOR)
        title_rect = title_surface.get_rect(center=(WINDOW_WIDTH // 2, 60))
        screen.blit(title_surface, title_rect)

        pygame.draw.rect(screen, PANEL_COLOR, panel_rect, border_radius=12)
        pygame.draw.rect(screen, BUTTON_BORDER_COLOR, panel_rect, width=2, border_radius=12)

        if map_files:
            for button, _ in buttons:
                button.draw(screen, button_font, button.contains(mouse_pos))
        else:
            empty_surface = button_font.render(
                "No map files found in the maps/ directory.",
                True,
                TEXT_COLOR,
            )
            empty_rect = empty_surface.get_rect(center=panel_rect.center)
            screen.blit(empty_surface, empty_rect)

        note_surface = small_font.render(note, True, SUBTLE_TEXT_COLOR)
        note_rect = note_surface.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT - 95))
        screen.blit(note_surface, note_rect)

        back_button.draw(screen, button_font, back_button.contains(mouse_pos))

        pygame.display.flip()
        clock.tick(60)


def about_menu(screen: pygame.Surface, clock: pygame.time.Clock) -> None:
    """
    Show a simple About screen.
    """
    title_font = pygame.font.SysFont(None, 42)
    text_font = pygame.font.SysFont(None, 32)
    small_font = pygame.font.SysFont(None, 24)

    back_button = Button(
        pygame.Rect((WINDOW_WIDTH - 180) // 2, WINDOW_HEIGHT - 80, 180, 46),
        "Back",
    )

    while True:
        mouse_pos = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if back_button.contains(mouse_pos):
                    return

        screen.fill(BACKGROUND_COLOR)

        title_surface = title_font.render("About", True, TITLE_COLOR)
        title_rect = title_surface.get_rect(center=(WINDOW_WIDTH // 2, 90))
        screen.blit(title_surface, title_rect)

        panel_rect = pygame.Rect(110, 160, WINDOW_WIDTH - 220, 140)
        pygame.draw.rect(screen, PANEL_COLOR, panel_rect, border_radius=12)
        pygame.draw.rect(screen, BUTTON_BORDER_COLOR, panel_rect, width=2, border_radius=12)

        text_surface = text_font.render("SEIR Cellular Automaton V.01", True, TEXT_COLOR)
        text_rect = text_surface.get_rect(center=panel_rect.center)
        screen.blit(text_surface, text_rect)

        hint_surface = small_font.render("ESC or Back to return", True, SUBTLE_TEXT_COLOR)
        hint_rect = hint_surface.get_rect(center=(WINDOW_WIDTH // 2, 330))
        screen.blit(hint_surface, hint_rect)

        back_button.draw(screen, text_font, back_button.contains(mouse_pos))

        pygame.display.flip()
        clock.tick(60)


def main() -> None:
    MAPS_DIR.mkdir(parents=True, exist_ok=True)

    screen, clock = init_launcher_window()
    running = True

    while running:
        action = main_menu(screen, clock)

        if action == "quit":
            running = False

        elif action == "editor":
            from editor import run_editor
            run_editor()
            screen, clock = init_launcher_window()

        elif action == "simulation":
            map_path = choose_map_menu(screen, clock)
            if map_path is not None:
                from simulation import run_simulation
                run_simulation(map_path)
                screen, clock = init_launcher_window()

        elif action == "settings":
            run_settings_editor()
            screen, clock = init_launcher_window()

        elif action == "about":
            about_menu(screen, clock)

    pygame.quit()


if __name__ == "__main__":
    main()
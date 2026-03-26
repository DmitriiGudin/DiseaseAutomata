from __future__ import annotations

import copy
from typing import Dict, Optional

import pygame

from settings_utils import (
    get_current_settings,
    get_default_settings,
    update_current_settings,
    reset_current_to_default,
)


WINDOW_WIDTH = 760
WINDOW_HEIGHT = 420

BACKGROUND_COLOR = (245, 245, 245)
TEXT_COLOR = (20, 20, 20)
MUTED_COLOR = (100, 100, 100)
BOX_COLOR = (255, 255, 255)
ACTIVE_BOX_COLOR = (220, 235, 255)
BORDER_COLOR = (160, 160, 160)
ERROR_COLOR = (190, 40, 40)
SUCCESS_COLOR = (30, 140, 60)

FIELD_ORDER = [
    "GRID_WIDTH",
    "GRID_HEIGHT",
    "CELL_SIZE",
    "alpha",
    "beta",
    "gamma",
    "FPS",
]

FIELD_HINTS = {
    "GRID_WIDTH": "positive integer",
    "GRID_HEIGHT": "positive integer",
    "CELL_SIZE": "positive integer",
    "alpha": "float in [0, 1]",
    "beta": "float in [0, 1]",
    "gamma": "float in [0, 1]",
    "FPS": "positive integer",
}


def parse_field_value(field_name: str, raw_text: str):
    raw_text = raw_text.strip()

    if field_name in {"GRID_WIDTH", "GRID_HEIGHT", "CELL_SIZE", "FPS"}:
        return int(raw_text)

    if field_name in {"alpha", "beta", "gamma"}:
        return float(raw_text)

    raise ValueError(f"Unknown field: {field_name}")


def run_settings_editor() -> None:
    pygame.init()
    pygame.display.set_caption("SEIR Settings")
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    clock = pygame.time.Clock()

    title_font = pygame.font.SysFont(None, 34)
    font = pygame.font.SysFont(None, 28)
    small_font = pygame.font.SysFont(None, 22)

    current_settings = get_current_settings()
    original_settings = copy.deepcopy(current_settings)
    default_settings = get_default_settings()

    field_texts: Dict[str, str] = {
        key: str(current_settings[key]) for key in FIELD_ORDER
    }

    active_index = 0
    message = ""
    message_color = TEXT_COLOR
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                active_field = FIELD_ORDER[active_index]

                if event.key == pygame.K_ESCAPE:
                    running = False

                elif event.key == pygame.K_TAB:
                    if pygame.key.get_mods() & pygame.KMOD_SHIFT:
                        active_index = (active_index - 1) % len(FIELD_ORDER)
                    else:
                        active_index = (active_index + 1) % len(FIELD_ORDER)

                elif event.key == pygame.K_UP:
                    active_index = (active_index - 1) % len(FIELD_ORDER)

                elif event.key == pygame.K_DOWN:
                    active_index = (active_index + 1) % len(FIELD_ORDER)

                elif event.key == pygame.K_BACKSPACE:
                    field_texts[active_field] = field_texts[active_field][:-1]

                elif event.key == pygame.K_RETURN:
                    try:
                        updates = {
                            key: parse_field_value(key, value)
                            for key, value in field_texts.items()
                        }
                        update_current_settings(updates)
                        current_settings = get_current_settings()
                        default_settings = get_default_settings()
                        message = "Settings saved."
                        message_color = SUCCESS_COLOR
                    except Exception as exc:
                        message = f"Error: {exc}"
                        message_color = ERROR_COLOR

                elif event.key == pygame.K_d:
                    try:
                        reset_current_to_default()
                        current_settings = get_current_settings()
                        default_settings = get_default_settings()
                        field_texts = {
                            key: str(current_settings[key]) for key in FIELD_ORDER
                        }
                        message = "Current settings reset to default."
                        message_color = SUCCESS_COLOR
                    except Exception as exc:
                        message = f"Error: {exc}"
                        message_color = ERROR_COLOR

                elif event.key == pygame.K_r:
                    field_texts = {
                        key: str(original_settings[key]) for key in FIELD_ORDER
                    }
                    message = "Reverted unsaved edits."
                    message_color = MUTED_COLOR

                else:
                    if event.unicode and (event.unicode.isdigit() or event.unicode in ".-"):
                        field_texts[active_field] += event.unicode

        screen.fill(BACKGROUND_COLOR)

        title_surface = title_font.render("Settings", True, TEXT_COLOR)
        screen.blit(title_surface, (30, 20))

        help_surface = small_font.render(
            "TAB/UP/DOWN: move   ENTER: save   D: reset to default   R: revert edits   ESC: exit",
            True,
            MUTED_COLOR,
        )
        screen.blit(help_surface, (30, 58))

        start_y = 105
        row_h = 38
        label_x = 40
        box_x = 220
        default_x = 430
        hint_x = 580
        box_w = 160
        box_h = 28

        header1 = small_font.render("Field", True, TEXT_COLOR)
        header2 = small_font.render("Current value", True, TEXT_COLOR)
        header3 = small_font.render("Default", True, TEXT_COLOR)
        screen.blit(header1, (label_x, start_y - 28))
        screen.blit(header2, (box_x, start_y - 28))
        screen.blit(header3, (default_x, start_y - 28))

        for i, field_name in enumerate(FIELD_ORDER):
            y = start_y + i * row_h

            label_surface = font.render(field_name, True, TEXT_COLOR)
            screen.blit(label_surface, (label_x, y))

            box_rect = pygame.Rect(box_x, y - 2, box_w, box_h)
            fill_color = ACTIVE_BOX_COLOR if i == active_index else BOX_COLOR
            pygame.draw.rect(screen, fill_color, box_rect)
            pygame.draw.rect(screen, BORDER_COLOR, box_rect, 2)

            value_surface = font.render(field_texts[field_name], True, TEXT_COLOR)
            screen.blit(value_surface, (box_x + 8, y))

            default_surface = font.render(str(default_settings[field_name]), True, MUTED_COLOR)
            screen.blit(default_surface, (default_x, y))

            hint_surface = small_font.render(FIELD_HINTS[field_name], True, MUTED_COLOR)
            screen.blit(hint_surface, (hint_x, y + 4))

        if message:
            message_surface = small_font.render(message, True, message_color)
            screen.blit(message_surface, (30, WINDOW_HEIGHT - 35))

        pygame.display.flip()
        clock.tick(30)

    pygame.quit()
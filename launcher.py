from __future__ import annotations

from pathlib import Path

from editor import run_editor
from simulation import run_simulation
from grid_utils import list_map_files


MAPS_DIR = Path("maps")


def print_menu() -> None:
    print("\n=== SEIR Cellular Automaton ===")
    print("1. Run editor")
    print("2. Run simulation")
    print("3. Quit")


def choose_map_file() -> Path | None:
    """
    Let the user choose one of the existing map files.

    Returns:
        Path to the selected map, or None if selection is cancelled.
    """
    map_files = list_map_files(MAPS_DIR)

    if not map_files:
        print("\nNo map files found in 'maps/'. Create one in the editor first.")
        return None

    print("\nAvailable maps:")
    for idx, path in enumerate(map_files, start=1):
        print(f"{idx}. {path.name}")

    print("0. Cancel")

    while True:
        choice = input("Choose a map number: ").strip()

        if not choice.isdigit():
            print("Please enter an integer.")
            continue

        choice_int = int(choice)

        if choice_int == 0:
            return None

        if 1 <= choice_int <= len(map_files):
            return map_files[choice_int - 1]

        print("Invalid selection. Try again.")


def main() -> None:
    MAPS_DIR.mkdir(parents=True, exist_ok=True)

    while True:
        print_menu()
        choice = input("Select an option: ").strip()

        if choice == "1":
            run_editor()

        elif choice == "2":
            map_path = choose_map_file()
            if map_path is not None:
                run_simulation(map_path)

        elif choice == "3":
            print("Exiting.")
            break

        else:
            print("Invalid option. Please choose 1, 2, or 3.")


if __name__ == "__main__":
    main()
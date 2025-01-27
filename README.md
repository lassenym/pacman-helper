# pacman-helper
A tool to categorize packages installed via the `pacman` package manager.

## Dependencies:
- Python3
- pyalpm

## Usage

1. Place `pacman_helper.py` in a directory of your choice.
2. Create an alias for convenience, e.g., `alias ph='python path/to/pacman_helper.py'`.

Running the script for the first time generates a `pkg_data.db` file in the same directory, organizing all packages into four categories:
- **library**
- **program**
- **system**
- **dependency**

Packages installed as dependencies are categorized as **dependencies**; the rest require manual categorization. Once a package is sorted, it’s saved in `pkg_data.db` and won’t need re-sorting.

### Commands

Assuming the alias `ph`:
- `ph` — Checks list integrity, updating for installed/uninstalled packages.
- `ph p` — Lists packages + descriptions in the **program** category.
- `ph l` — Lists packages + descriptions in the **library** category.
- `ph s` — Lists packages + descriptions in the **system** category.
- `ph d` — Lists packages + descriptions in the **dependency** category.
- `ph a` — Lists all packages + descriptions.

- `ph i` — Prints the info-panel.

## FAQ

**Why use this?**  
Provides a clear overview of installed packages.

**Why these four categories?**  
This setup works well for my needs, but it’s easy to modify in the code if needed.

**What do you put in each category?**

- **system** — Core packages (e.g., `linux`, `sddm`, `amd-ucode`).
- **program** — Applications (e.g., `chromium`, `konsole`, `steam`).
- **library** — Libraries, often for personal coding (e.g., `python-cloudscraper`).

**Can this damage the system?**

No, it only reads package-info, never changing anything on the system.

##
Example output for `ph p`:

![image](https://github.com/user-attachments/assets/ba2e6d61-ec3b-4535-8456-a920c8758b37)
Example output for `ph i`:

![image](https://github.com/user-attachments/assets/6d766d9a-8b60-450f-b483-6f2136bb6115)


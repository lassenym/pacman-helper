import sqlite3, os, sys, shutil, re, subprocess
import pyalpm

RED = "\033[91m"
GREEN = "\033[92m"
BEIGE = "\033[38;5;223m"
GRAYB = "\033[48;5;235m"
BLUE = "\033[34m"
BLACK = "\033[90m"
YELLOW = "\033[38;5;220m"
RESET = "\033[0m"

FILENAME = "pkg_data.db"

def import_packages():
    handle = pyalpm.Handle("/", "/var/lib/pacman")
    db = handle.get_localdb()
    return db.pkgcache

def import_db():
    handle = pyalpm.Handle("/", "/var/lib/pacman")
    return handle.get_localdb()

def db_connect():
    conn = sqlite3.connect(os.path.join(os.path.dirname(os.path.abspath(__file__)), FILENAME))
    return conn, conn.cursor()

def db_make():
    conn, cursor = db_connect()

    cursor.execute("""
    CREATE TABLE packages (
        name TEXT,
        desc TEXT,
        flag CHAR(1)
    );
    """)

    for pkg in import_packages():
        if pkg.reason == 0:
            cursor.execute("INSERT INTO packages (name, desc, flag) VALUES (?, ?, ?);", (pkg.name, pkg.desc, "x"))
        else:
            cursor.execute("INSERT INTO packages (name, desc, flag) VALUES (?, ?, ?);", (pkg.name, pkg.desc, "d"))

    conn.commit()
    conn.close()

def db_update():
    conn, cursor = db_connect()

    db_pkgs = cursor.execute("SELECT name, flag FROM packages").fetchall()
    pac_pkgs = import_packages()

    db_pkg_names = {pkg[0] for pkg in db_pkgs}
    pac_pkg_names = {pkg.name for pkg in pac_pkgs}

    only_in_db = db_pkg_names - pac_pkg_names
    only_in_pac = pac_pkg_names - db_pkg_names

    if only_in_db:
        for pkg in only_in_db:
            cursor.execute("DELETE FROM packages WHERE name = ?", (pkg, ))
            print(f"{RED}{pkg}{RESET} has been removed from the db")

    if only_in_pac:
        for pkg in only_in_pac:
            desc = [obj.desc for obj in pac_pkgs if obj.name == pkg][0]
            reason = [obj.reason for obj in pac_pkgs if obj.name == pkg][0]
            if reason == 0:
                cursor.execute("INSERT INTO packages (name, desc, flag) VALUES (?, ?, ?);", (pkg, desc, "x"))
            else:
                cursor.execute("INSERT INTO packages (name, desc, flag) VALUES (?, ?, ?);", (pkg, desc, "d"))
            print(f"{GREEN}{pkg}{RESET} has been added to the db")


    conn.commit()
    conn.close()

def db_sort():
    conn, cursor = db_connect()
    pkgs = cursor.execute("SELECT name, desc, flag FROM packages WHERE flag = 'x';").fetchall()
    if pkgs:
        for pkg in pkgs:
            print(f"{BLACK}--------------------------------------------------------{RESET}")
            pkg_sort(pkg[0], pkg[1])
    conn.close()

def pkg_sort(name, desc):
    conn, cursor = db_connect()

    print(f"'{RED}{name}{RESET}' needs to be sorted: {BLACK}({desc}){RESET}")
    new_flag = input(f"'{BLUE}s{RESET}', '{GREEN}p{RESET}' or '{YELLOW}l{RESET}'? ({BLUE}system{RESET}, {GREEN}program{RESET} or {YELLOW}library{RESET}): ")

    if new_flag not in ['s', 'p', 'l']:
        print(f"\n{RED}Error: Wrong flag. Please enter given flags.{RESET}\n")
    else:
        cursor.execute("UPDATE packages SET flag = ? WHERE name = ?;", (new_flag, name))

    conn.commit()
    conn.close()
    
def db_print(cat):
    CATEGORIES = {
    'd': 'Dependencies',
    's': 'System Packages',
    'p': 'Programs',
    'l': 'Libraries',
    'a': 'All Packages'
    }
    conn, cursor = db_connect()

    if cat == 'a':
        pkgs = cursor.execute("SELECT name, desc FROM packages ORDER BY name ASC").fetchall()
    elif cat in ('s', 'p', 'l', 'd'):
        pkgs = cursor.execute("SELECT name, desc FROM packages WHERE flag = ? ORDER BY name ASC;", (cat,)).fetchall()
    else:
        print(f"\n{RED}Error: Unknown category.{RESET}\n")
        return
    conn.close()

    print(f"{YELLOW}{CATEGORIES[cat]}:{RESET}\n{BEIGE}--------------------------------------------------------{RESET}")
    for pkg in pkgs:
        print(f"{BLUE}{pkg[0]}{RESET} {BLACK}({pkg[1]}){RESET}")
    print(f"{BEIGE}--------------------------------------------------------{RESET}")
    print(f"{GRAYB}{YELLOW}{len(pkgs)}{RESET}{GRAYB} packages in category '{YELLOW}{CATEGORIES[cat]}{RESET}{GRAYB}' installed{RESET}")

def get_pkg_from_name(name):
    name = re.sub(r"[<>=!~]+\s*\d+(\.\d+)*.*", "", name).strip()

    if import_db().get_pkg(name):
        return import_db().get_pkg(name)

    for pkg in import_packages():
        for provided in pkg.provides:
            if provided.startswith(name):
                return pkg

def get_biggest_pkgs(count):
    packages = [(pkg.name, int(round(pkg.isize / (1024 * 1024), 0))) for pkg in import_packages()]
    packages = sorted(packages, key=lambda x: float(x[1]), reverse=True)

    return packages[:count]

def get_last_pkgs(count):
    log_file = "/var/log/pacman.log"
    package_names = [pkg.name for pkg in import_packages()]
    package_history = {}

    with open(log_file, 'r') as log:
        for line in log:
            if " installed " in line:
                if line.split(" ")[3] in package_names and not import_db().get_pkg(line.split(" ")[3]).reason:
                    package_history[line.split(" ")[3]] = line.split(" ")[0][1:-6]

    return sorted(package_history.items(), key=lambda x: x[1], reverse=True)[:count]

def get_most_pkgs(count):
    pkg_count = []
    for pkg in import_packages():
        pkg_count.append([pkg.name, len(pkg.depends)])
    
    pkg_count.sort(key=lambda x: x[1], reverse=True)
    
    return pkg_count[:count]

def print_info():
    rows = 10
    columns = 3
    space_per_row = int(shutil.get_terminal_size()[0] / columns) - 1

    biggest = get_biggest_pkgs(rows)
    last  = get_last_pkgs(rows)
    most_dependencies = get_most_pkgs(rows)

    print(f"\n{YELLOW}{("BIGGEST PACKAGES:"[:space_per_row+1])}{RESET}{(" " * (space_per_row - 16))}|", end="")
    print(f"{YELLOW}{("LAST INSTALLED:"[:space_per_row+1])}{RESET}{(" " * (space_per_row - 14))}|", end="")
    print(f"{YELLOW}{("MOST DEPENDENCIES:"[:space_per_row])}{RESET}")


    print("-" * shutil.get_terminal_size()[0])

    for i in range(rows):
        output = f"{RED}{str(biggest[i][1])[:space_per_row]} MB {BLUE}{biggest[i][0][:space_per_row - len(str(biggest[i][1])) - 3]}{RESET}"
        output += " " * (space_per_row - len(biggest[i][0][:space_per_row]) - len(str(biggest[i][1])[:space_per_row - len(biggest[i][0])]) - 3) + "|"
        
        output += f"{RED}{last[i][1][:10]} {BLUE}{last[i][0][:space_per_row - len(last[i][1][:10])]}{RESET}"
        output += " " * (space_per_row - len(last[i][0][:space_per_row - 1]) - len(last[i][1][:10])) + "|"

        output += f"{RED}{str(most_dependencies[i][1])[:space_per_row]} {BLUE}{most_dependencies[i][0][:space_per_row - len(str(most_dependencies[i][1]))]}{RESET}"

        print(output)

    print("-" * shutil.get_terminal_size()[0])

    for pkg in import_packages():
        if len(pkg.compute_requiredby()) == 0 and pkg.reason:
            if len(pkg.compute_optionalfor()) == 1:
                print(f"{YELLOW}{pkg.name}{RESET} is not required. It is optional for: {BLUE}{pkg.compute_optionalfor()[0]}{RESET}")
            elif len(pkg.compute_optionalfor()) == 2:
                print(f"{YELLOW}{pkg.name}{RESET} is not required. It is optional for: {BLUE}{pkg.compute_optionalfor()[0]}{RESET} and {BLUE}{pkg.compute_optionalfor()[1]}{RESET}")
            else:
                print(f"{YELLOW}{pkg.name}{RESET} is not required. It is optional for: {BLUE}{pkg.compute_optionalfor()}{RESET}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "i":
            print_info()
        else:
            db_print(sys.argv[1])
    else:
        if not os.path.isfile(os.path.join(os.path.join(os.path.dirname(__file__)), FILENAME)):
            db_make()
            print(f"{YELLOW}Data imported.{RESET}")
        else:
            print(f"{YELLOW}Updating db...{RESET}")
            db_update()
            print(f"{YELLOW}Done.{RESET}")
            db_sort()

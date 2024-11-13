import os, subprocess, json, sys

RED = "\033[91m"
GREEN = "\033[92m"
BEIGE = "\033[38;5;223m"
GRAYB = "\033[48;5;235m"
BLUE = "\033[34m"
BLACK = "\033[90m"
YELLOW = "\033[38;5;220m"
RESET = "\033[0m"


class Package:
    def __init__(self, name, version, description, size, explicitly_installed, depends_on, required_by, category='dependency'):
        self.name = name
        self.version = version
        self.description = description
        self.size = size
        self.explicitly_installed = explicitly_installed
        self.depends_on = depends_on
        self.required_by = required_by
        self.category = category

    def add_dependency(self, package):
        if isinstance(package, str):
            self.depends_on.append(package)

    def add_required_by(self, package):
        if isinstance(package, str):
            self.required_by.append(package)

def get_installed_packages():
    # Run pacman to list all explicitly installed packages
    result = subprocess.run(['pacman', '-Qi'], capture_output=True, text=True)

    # Parse package information
    packages = []
    package_dict = {}
    package_info = result.stdout.split('\n\n')
    for info in package_info:
        lines = info.splitlines()
        explicitly_installed = False
        temp = []
        for line in lines:
            if line.startswith('Name'):
                package_dict['name'] = line.split(': ')[1]
            elif line.startswith('Version'):
                package_dict['version'] = line.split(': ')[1]
            elif line.startswith('Description'):
                package_dict['description'] = line.split(': ')[1]
            elif line.startswith('Installed Size'):
                package_dict['size'] = line.split(': ')[1]
            elif line.startswith('Install Reason') and 'Explicitly installed' in line:
                explicitly_installed = True
            elif line.startswith('Depends On'):
                temp = line.split(': ')[1].split()
                temp = [item for item in temp if item != 'None']
                package_dict['depends'] = temp
            elif line.startswith('Required By'):
                temp = line.split(': ')[1].split()
            elif line.startswith('Optional For'):
                temp.extend(line.split(': ')[1].split())
                temp = [item for item in temp if item != 'None']
                package_dict['required'] = temp

        if 'name' in package_dict and 'version' in package_dict:
            package = Package(
                name=package_dict['name'],
                version=package_dict['version'],
                description=package_dict.get('description', 'No description'),
                size=package_dict.get('size', 'Unknown size'),
                explicitly_installed=explicitly_installed,
                depends_on=[],
                required_by=[]
            )
            if len(package_dict['depends']) > 0:
                for dep in package_dict['depends']:
                    package.add_dependency(dep)
            if len(package_dict['required']) > 0:
                for req in package_dict['required']:
                    package.add_required_by(req)
            packages.append(package)
            package_dict.clear()

    # Add dependencies to each package
    for info in package_info:
        lines = info.splitlines()
        package_name = None
        dependencies = []
        for line in lines:
            if line.startswith('Name'):
                package_name = line.split(': ')[1]
            elif line.startswith('Depends On') and package_name:
                dependencies = line.split(': ')[1].split() if ': ' in line else []
                for package in packages:
                    if package.name == package_name:
                        for dep_name in dependencies:
                            dep_name = dep_name.split('=')[0]
                            for potential_dep in packages:
                                if potential_dep.name == dep_name:
                                    package.add_dependency(potential_dep)

    return packages

def export_packages_to_json(packages, filename='data.json'):
    current_directory = os.path.dirname(os.path.abspath(__file__))
    filepath = os.path.join(current_directory, filename)
    
    packages_data = []

    for package in packages:
        packages_data.append({
            'name': package.name,
            'version': package.version,
            'description': package.description,
            'size': package.size,
            'explicitly_installed': package.explicitly_installed,
            'depends_on': package.depends_on,
            'required_by': package.required_by,
            'category': package.category
        })
    with open(filepath, 'w') as json_file:
        json.dump(packages_data, json_file, indent=4)

    return

def import_packages_from_json(filename='data.json'):
    packages_data = []
    current_directory = os.path.dirname(os.path.abspath(__file__))
    filepath = os.path.join(current_directory, filename)
    if not os.path.exists(filepath):
        with open(filepath, 'w') as json_file:
            json.dump({}, json_file)
    with open(filepath, 'r') as json_file:
        packages_data = json.load(json_file)
    
    packages = []
    for package_info in packages_data:
        package = Package(
            name=package_info['name'],
            version=package_info['version'],
            description=package_info['description'],
            size=package_info['size'],
            explicitly_installed=package_info['explicitly_installed'],
            category=package_info['category'],
            depends_on=package_info['depends_on'],
            required_by=package_info['required_by']
        )
        packages.append(package)
    
    return packages

def manual_sort(package):
    print(f"\n'{RED}{package.name}{RESET}' needs to be sorted: {BLACK}({package.description}){RESET}\n")
    x = input(f"'{BLUE}s{RESET}', '{GREEN}p{RESET}' or '{YELLOW}l{RESET}'? ({BLUE}system{RESET}, {GREEN}program{RESET} or {YELLOW}library{RESET}): ")
    if x == 's':
        package.category = 'system'
    elif x == 'p':
        package.category = 'program'
    elif x == 'l':
        package.category = 'library'
    else:
        print("Wrong input. Fuck you.")
    
    return

def test_integrity(liste):

    paclist = get_installed_packages()

    for pkg in paclist: # Sees if installed package is already in list
        found = False
        for p in liste:
            if pkg.name == p.name:
                found = True
                break
        if found: # If it is: continue
            continue
        else:
            print(f"{GREEN}{pkg.name}{RESET} has been added to json")
            liste.append(pkg) # If it isnt: add to the list

    for p in liste: # See if package in json is still installed
        for pkg in paclist:
            found = False
            if pkg.name == p.name:
                found = True
                break
        if found: # If it is: continue
            continue
        else:
            print(f"{RED}{p.name}{RESET} has been removed from json")
            liste.remove(p) # If it isnt: remove from list

    for pkg in liste: #test if categories fit
        if pkg.required_by == [] and pkg.category == 'dependency':
            manual_sort(pkg)
    

    export_packages_to_json(liste)

    return

def show_category(liste, cat):
    liste.sort(key=lambda obj: obj.name)
    x = 0
    for pkg in liste:
        if pkg.category == cat:
            x += 1
            print(f"{BLUE}{pkg.name}{RESET} {BLACK}({pkg.description}){RESET}")
    print(f"{BEIGE}--------------------------------------------------------{RESET}\n{GRAYB}{YELLOW}{x}{RESET}{GRAYB} packages in category '{YELLOW}{cat}{RESET}{GRAYB}' installed{RESET}")

def run_main():
    if len(sys.argv) > 1:
        if sys.argv[1] == 'p':
            print(f"{YELLOW}Programs:{RESET}\n{BEIGE}--------------------------------------------------------{RESET}")
            show_category(import_packages_from_json(), 'program')
        elif sys.argv[1] == 'd':
            print(f"{YELLOW}Dependencies:{RESET}\n{BEIGE}--------------------------------------------------------{RESET}")
            show_category(import_packages_from_json(), 'dependency')
        elif sys.argv[1] == 's':
            print(f"{YELLOW}System Packages:{RESET}\n{BEIGE}--------------------------------------------------------{RESET}")
            show_category(import_packages_from_json(), 'system')
        elif sys.argv[1] == 'l':
            print(f"{YELLOW}Libraries:{RESET}\n{BEIGE}--------------------------------------------------------{RESET}")
            show_category(import_packages_from_json(), 'library')
        else:
            print("Unknown arguments. Fuck you.")
    else:
        if not os.path.isfile(os.path.join(os.path.join(os.path.dirname(__file__)), 'data.json')):
            export_packages_to_json(get_installed_packages())
            print("Data imported.")
        else:
            print("Testing integrity...")
            test_integrity(import_packages_from_json())
            print("Done.")

if __name__ == "__main__":
    run_main()

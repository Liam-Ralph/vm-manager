# Imports

import os
import sys


# Fucntions

def get_machines(path_vms, vm_ext):
    output = ""
    for path, dirs, files in os.walk(path_vms):
        vm_path = False
        for file in files:
            if file.endswith(vm_ext):
                vm_path = True
                break
        if vm_path:
            size = 0
            for subpath, subdirs, subfiles in os.walk(path):
                for subfile in subfiles:
                    size += os.path.getsize(f"{subpath}/{subfile}")
            dirs[:] = []
            output += f"{size} {os.path.basename(path)}\n"
    return output.strip()

if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(1)
    path_vms = sys.argv[1]
    vm_ext = sys.argv[2]
    print(get_machines(path_vms, vm_ext), end="")

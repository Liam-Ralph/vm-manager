# Imports

import os
import sys


# Function

def get_vm_files(vms_path, vm_path):
    output = ""
    for path, dirs, files in os.walk(os.path.join(vms_path, vm_path)):
        output += f"dir_{path.removeprefix(vms_path + "/")}\n"
        for file in files:
            output += f"file{os.path.join(path, file).removeprefix(vms_path + "/")}\n"
    return output.strip()


# Run Function

if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(1)
    vms_path = sys.argv[1]
    vm_path = sys.argv[2]
    print(get_vm_files(vms_path, vm_path), end="")

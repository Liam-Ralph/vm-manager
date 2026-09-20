# Imports

import hashlib
import os
import sys


# Functions

def get_machines(path_vms, vm_ext, vm_hashfile_path, vms_path):
    output = ""
    for path, dirs, files in os.walk(path_vms):
        vm_path = False
        for file in files:
            if file.endswith(vm_ext):
                vm_path = True
                break
        if vm_path:
            md5_hash = hashlib.md5()
            with open(f"{path}/{vm_hashfile_path}", "rb") as file:
                for chunk in iter(lambda: file.read(4096), b""):
                    md5_hash.update(chunk)
            size = 0
            for subpath, subdirs, subfiles in os.walk(path):
                for subfile in subfiles:
                    size += os.path.getsize(f"{subpath}/{subfile}")
            dirs[:] = []
            output += (
                f"{md5_hash.hexdigest()} {size} " +
                f"{path[len(vms_path) + 1:] if path.startswith(vms_path) else path}\n"
            )
    return output.strip()

if __name__ == "__main__":
    if len(sys.argv) != 5:
        sys.exit(1)
    path_vms = sys.argv[1]
    vm_ext = sys.argv[2]
    vm_hashfile_path = sys.argv[3]
    vms_path = sys.argv[4]
    print(get_machines(path_vms, vm_ext, vm_hashfile_path, vms_path), end="")

# Imports

import hashlib
import os
import sys


# Function

def get_machines(vms_path, vm_ext, vm_hashfile_path):
    output = ""
    for path, dirs, files in os.walk(vms_path):
        vm_path = False
        for file in files:
            if file.endswith(vm_ext):
                vm_path = True
                break
        if vm_path:
            md5_hash = hashlib.md5()
            with open(os.path.join(path, vm_hashfile_path), "rb") as file:
                for chunk in iter(lambda: file.read(4096), b""):
                    md5_hash.update(chunk)
            size = 0
            for subpath, subdirs, subfiles in os.walk(path):
                for subfile in subfiles:
                    size += os.path.getsize(os.path.join(subpath, subfile))
            dirs[:] = []
            output += (
                f"{md5_hash.hexdigest()} {size} " +
                f"{path.removeprefix(vms_path + "/")}\n"
            )
    return output.strip()


# Run Function

if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit(1)
    vms_path = sys.argv[1]
    vm_ext = sys.argv[2]
    vm_hashfile_path = sys.argv[3]
    print(get_machines(vms_path, vm_ext, vm_hashfile_path), end="")
